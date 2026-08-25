########################################################################
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2021 Make IT - http://www.makeitgroup.com/
# All Rights Reserved.
#
# Developer(s): Anibal Arenas Pastor
#               (anibalarenas2107@gmail.com)
#
########################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockLowAlert(models.Model):
    _name = "stock.low.alert"
    _description = "Low stock alert"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"

    name = fields.Char(string="Alert", required=True, copy=False, readonly=True, default=lambda self: _("New"))
    state = fields.Selection(
        [("open", "Open"), ("resolved", "Resolved"), ("ignored", "Ignored")],
        string="Status", default="open", required=True, tracking=True, index=True,
    )
    assigned_user_id = fields.Many2one("res.users", string="Assigned user", tracking=True, index=True)
    product_id = fields.Many2one("product.product", string="Product", required=True, readonly=True, index=True)
    orderpoint_id = fields.Many2one("stock.warehouse.orderpoint", string="Reordering rule", required=True, readonly=True, index=True)
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", readonly=True, index=True)
    location_id = fields.Many2one("stock.location", string="Location", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", required=True, readonly=True, index=True)
    uom_id = fields.Many2one("uom.uom", string="UoM", readonly=True)
    stock_current = fields.Float(string="Current stock", digits="Product Unit of Measure", tracking=True, readonly=True)
    min_qty = fields.Float(string="Configured minimum", digits="Product Unit of Measure", readonly=True)
    max_qty = fields.Float(string="Configured maximum", digits="Product Unit of Measure", readonly=True)
    last_purchase_date = fields.Datetime(string="Last purchase", readonly=True)
    last_supplier_id = fields.Many2one("res.partner", string="Vendor", readonly=True)
    last_purchase_qty = fields.Float(string="Last purchase quantity", digits="Product Unit of Measure", readonly=True)
    last_purchase_order_id = fields.Many2one("purchase.order", string="Purchase order", readonly=True)
    notification_count = fields.Integer(string="Times sent", compute="_compute_notification_count")
    notification_ids = fields.One2many("stock.low.alert.notification", "alert_id", string="Notification history", readonly=True)
    first_alert_date = fields.Datetime(string="First detection", default=fields.Datetime.now, readonly=True)
    last_alert_date = fields.Datetime(string="Last detection", default=fields.Datetime.now, readonly=True)
    last_notification_date = fields.Datetime(string="Last notification", readonly=True)
    resolved_date = fields.Datetime(string="Resolution date", readonly=True)
    related_alert_count = fields.Integer(string="Related alerts", compute="_compute_related_alert_count")

    @api.depends("notification_ids")
    def _compute_notification_count(self):
        for rec in self:
            rec.notification_count = len(rec.notification_ids.filtered(lambda n: n.state != "error"))

    def _compute_related_alert_count(self):
        for rec in self:
            rec.related_alert_count = self.search_count([("id", "!=", rec.id), ("orderpoint_id", "=", rec.orderpoint_id.id)]) if rec.orderpoint_id else 0

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = seq.next_by_code("stock.low.alert") or _("Stock alert")
        return super().create(vals_list)

    def action_resolve(self):
        self.write({"state": "resolved", "resolved_date": fields.Datetime.now()})
        return True

    def action_ignore(self):
        self.write({"state": "ignored", "resolved_date": fields.Datetime.now()})
        return True

    def action_reopen(self):
        for rec in self:
            if rec.stock_current > rec.min_qty:
                raise UserError(_("The alert cannot be reopened because current stock is already above the minimum."))
        self.write({"state": "open", "resolved_date": False})
        return True

    def action_send_notification(self):
        for rec in self.filtered(lambda a: a.state == "open"):
            rec._send_configured_notifications(force=True)
        return True

    def action_view_related_alerts(self):
        self.ensure_one()
        action = self.env.ref("low_stock_alert.action_stock_low_alert").read()[0]
        action["domain"] = [("orderpoint_id", "=", self.orderpoint_id.id), ("id", "!=", self.id)]
        action["context"] = {"create": False}
        return action

    @api.model
    def action_run_stock_alert_check(self):
        params = self.env["ir.config_parameter"].sudo()
        if params.get_param("low_stock_alert.enabled", "False") not in ("True", "1", True):
            return True

        orderpoints = self.env["stock.warehouse.orderpoint"].sudo().search([])
        now = fields.Datetime.now()
        for orderpoint in orderpoints:
            try:
                self._process_orderpoint(orderpoint, now)
            except Exception:
                _logger.exception("Error while processing reordering rule %s", orderpoint.display_name)
        return True

    @api.model
    def _process_orderpoint(self, orderpoint, now):
        product = orderpoint.product_id
        if not product or not orderpoint.location_id:
            return
        if self._is_excepted(orderpoint, now):
            existing = self.sudo().search([("orderpoint_id", "=", orderpoint.id), ("state", "=", "open")], limit=1)
            if existing:
                existing.write({"state": "ignored", "resolved_date": now, "last_alert_date": now})
            return

        current_stock = product.with_company(orderpoint.company_id).with_context(location=orderpoint.location_id.id).qty_available
        minimum = orderpoint.product_min_qty
        maximum = orderpoint.product_max_qty
        open_alert = self.sudo().search([("orderpoint_id", "=", orderpoint.id), ("state", "=", "open")], limit=1)

        if current_stock <= minimum:
            purchase_vals = self._get_last_purchase_values(product, orderpoint.company_id)
            responsible, notification_mode = self._get_responsible(orderpoint)
            values = {
                "assigned_user_id": responsible.id if responsible else False,
                "stock_current": current_stock,
                "min_qty": minimum,
                "max_qty": maximum,
                "last_alert_date": now,
                **purchase_vals,
            }
            if open_alert:
                open_alert.sudo().write(values)
                alert = open_alert
            else:
                values.update({
                    "product_id": product.id,
                    "orderpoint_id": orderpoint.id,
                    "warehouse_id": orderpoint.warehouse_id.id if orderpoint.warehouse_id else False,
                    "location_id": orderpoint.location_id.id,
                    "company_id": orderpoint.company_id.id,
                    "uom_id": orderpoint.product_uom.id if orderpoint.product_uom else product.uom_id.id,
                    "first_alert_date": now,
                })
                alert = self.sudo().create(values)
            alert._send_configured_notifications(notification_mode=notification_mode)
        elif open_alert:
            open_alert.sudo().write({
                "stock_current": current_stock,
                "last_alert_date": now,
                "state": "resolved",
                "resolved_date": now,
            })

    @api.model
    def _is_excepted(self, orderpoint, now):
        exceptions = self.env["stock.low.alert.exception"].sudo().search([("active", "=", True)])
        for exc in exceptions:
            if exc.date_from and now < exc.date_from:
                continue
            if exc.date_to and now > exc.date_to:
                continue
            if exc.orderpoint_id and exc.orderpoint_id != orderpoint:
                continue
            if exc.product_id and exc.product_id != orderpoint.product_id:
                continue
            if exc.category_id and exc.category_id != orderpoint.product_id.categ_id:
                continue
            if exc.warehouse_id and exc.warehouse_id != orderpoint.warehouse_id:
                continue
            if exc.location_id and exc.location_id != orderpoint.location_id:
                continue
            return True
        return False

    @api.model
    def _get_responsible(self, orderpoint):
        rules = self.env["stock.low.alert.responsible"].sudo().search([("active", "=", True)], order="sequence, id")
        default_mode = self.env["ir.config_parameter"].sudo().get_param("low_stock_alert.notification_mode", "activity")
        for rule in rules:
            if rule.product_id and rule.product_id != orderpoint.product_id:
                continue
            if rule.category_id and rule.category_id != orderpoint.product_id.categ_id:
                continue
            if rule.warehouse_id and rule.warehouse_id != orderpoint.warehouse_id:
                continue
            mode = default_mode if rule.notification_mode == "default" else rule.notification_mode
            return rule.user_id, mode
        return self.env.user, default_mode

    @api.model
    def _get_last_purchase_values(self, product, company):
        # Odoo does not allow ordering a model search by a related field such
        # as ``order_id.date_order``. Find the latest confirmed purchase order
        # first, then obtain the product lines that belong to that order.
        purchase_order = self.env["purchase.order"].sudo().search([
            ("company_id", "=", company.id),
            ("state", "in", ["purchase", "done"]),
            ("order_line.product_id", "=", product.id),
        ], order="date_order desc, id desc", limit=1)
        if not purchase_order:
            return {
                "last_purchase_date": False,
                "last_supplier_id": False,
                "last_purchase_qty": 0.0,
                "last_purchase_order_id": False,
            }

        lines = purchase_order.order_line.filtered(lambda line: line.product_id == product)
        qty = 0.0
        for line in lines:
            if line.product_uom and product.uom_id:
                qty += line.product_uom._compute_quantity(line.product_qty, product.uom_id)
            else:
                qty += line.product_qty

        return {
            "last_purchase_date": purchase_order.date_order,
            "last_supplier_id": purchase_order.partner_id.id,
            "last_purchase_qty": qty,
            "last_purchase_order_id": purchase_order.id,
        }

    def _send_configured_notifications(self, notification_mode=None, force=False):
        params = self.env["ir.config_parameter"].sudo()
        resend_hours = int(params.get_param("low_stock_alert.resend_hours", "24") or 0)
        now = fields.Datetime.now()
        for alert in self:
            user = alert.assigned_user_id
            if not user:
                continue
            if not force and alert.last_notification_date:
                if resend_hours <= 0:
                    continue
                elapsed = (now - alert.last_notification_date).total_seconds() / 3600.0
                if elapsed < resend_hours:
                    continue
            mode = notification_mode or params.get_param("low_stock_alert.notification_mode", "activity")
            sent_any = False
            if mode in ("activity", "both"):
                sent_any = alert._send_activity(user) or sent_any
            if mode in ("email", "both"):
                sent_any = alert._send_email(user) or sent_any
            if sent_any:
                alert.sudo().write({"last_notification_date": now})

    def _send_activity(self, user):
        self.ensure_one()
        notification = self.env["stock.low.alert.notification"].sudo().create({
            "alert_id": self.id, "user_id": user.id, "channel": "activity", "state": "sent",
        })
        try:
            activity = self.env["mail.activity"].sudo().create({
                "activity_type_id": self.env.ref("low_stock_alert.mail_activity_type_stock_low_alert").id,
                "summary": _("Low stock: %s") % self.product_id.display_name,
                "note": _("Current stock: %(stock)s %(uom)s. Minimum: %(min)s. Maximum: %(max)s.") % {
                    "stock": self.stock_current, "uom": self.uom_id.name or "", "min": self.min_qty, "max": self.max_qty,
                },
                "res_model_id": self.env["ir.model"]._get_id(self._name),
                "res_id": self.id,
                "user_id": user.id,
                "date_deadline": fields.Date.context_today(self),
                "low_stock_notification_id": notification.id,
            })
            notification.write({"activity_id": activity.id})
            return True
        except Exception as exc:
            notification.write({"state": "error", "error_message": str(exc)})
            _logger.exception("Could not create the low stock activity for %s", self.display_name)
            return False

    def _send_email(self, user):
        self.ensure_one()
        notification = self.env["stock.low.alert.notification"].sudo().create({
            "alert_id": self.id, "user_id": user.id, "channel": "email", "state": "sent", "email_to": user.email or "",
        })
        if not user.email:
            notification.write({"state": "error", "error_message": _("The user does not have an email address configured.")})
            return False
        try:
            template = self.env.ref("low_stock_alert.mail_template_stock_low_alert")
            template.sudo().send_mail(self.id, force_send=True, email_values={"email_to": user.email})
            return True
        except Exception as exc:
            notification.write({"state": "error", "error_message": str(exc)})
            _logger.exception("Could not send the low stock email for %s", self.display_name)
            return False
