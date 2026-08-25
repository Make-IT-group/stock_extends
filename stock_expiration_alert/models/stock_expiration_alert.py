import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockExpirationAlert(models.Model):
    _name = "stock.expiration.alert"
    _description = "Stock expiration alert"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "expiration_date, id desc"

    name = fields.Char(
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env._("New"),
    )
    state = fields.Selection(
        [("open", "Open"), ("resolved", "Resolved"), ("ignored", "Ignored")],
        default="open",
        required=True,
        tracking=True,
        index=True,
    )
    rule_id = fields.Many2one(
        "stock.expiration.alert.rule",
        required=True,
        readonly=True,
        ondelete="restrict",
        index=True,
    )
    assigned_user_id = fields.Many2one(
        "res.users", readonly=True, tracking=True, index=True
    )
    severity = fields.Selection(
        [("info", "Information"), ("warning", "Warning"), ("critical", "Critical")],
        required=True,
        readonly=True,
        tracking=True,
        index=True,
    )
    product_id = fields.Many2one(
        "product.product", required=True, readonly=True, index=True
    )
    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot/Serial Number",
        required=True,
        readonly=True,
        index=True,
    )
    warehouse_id = fields.Many2one("stock.warehouse", readonly=True, index=True)
    location_id = fields.Many2one(
        "stock.location", required=True, readonly=True, index=True
    )
    company_id = fields.Many2one(
        "res.company", required=True, readonly=True, index=True
    )
    uom_id = fields.Many2one("uom.uom", string="UoM", readonly=True)
    quantity = fields.Float(digits="Product Unit", readonly=True, tracking=True)
    expiration_date = fields.Datetime(
        required=True, readonly=True, tracking=True, index=True
    )
    days_remaining = fields.Integer(readonly=True, tracking=True)
    first_alert_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    last_alert_date = fields.Datetime(default=fields.Datetime.now, readonly=True)
    last_notification_date = fields.Datetime(readonly=True)
    resolved_date = fields.Datetime(readonly=True)
    notification_ids = fields.One2many(
        "stock.expiration.alert.notification", "alert_id", readonly=True
    )
    notification_count = fields.Integer(compute="_compute_notification_count")
    related_alert_count = fields.Integer(compute="_compute_related_alert_count")

    @api.depends("notification_ids", "notification_ids.state")
    def _compute_notification_count(self):
        for alert in self:
            alert.notification_count = len(
                alert.notification_ids.filtered(
                    lambda notification: notification.state != "error"
                )
            )

    def _compute_related_alert_count(self):
        for alert in self:
            alert.related_alert_count = self.search_count(
                [
                    ("id", "!=", alert.id),
                    ("lot_id", "=", alert.lot_id.id),
                    ("location_id", "=", alert.location_id.id),
                ]
            )

    @api.model_create_multi
    def create(self, vals_list):
        sequence = self.env["ir.sequence"]
        for values in vals_list:
            if values.get("name", self.env._("New")) == self.env._("New"):
                values["name"] = sequence.next_by_code(
                    "stock.expiration.alert"
                ) or self.env._("Expiration alert")
        return super().create(vals_list)

    def action_resolve(self):
        self.write({"state": "resolved", "resolved_date": fields.Datetime.now()})
        return True

    def action_ignore(self):
        self.write({"state": "ignored", "resolved_date": fields.Datetime.now()})
        return True

    def action_reopen(self):
        today = fields.Date.context_today(self)
        for alert in self:
            deadline = fields.Date.add(today, days=alert.rule_id.days_before_expiration)
            if alert.quantity <= 0 or alert.expiration_date.date() > deadline:
                raise UserError(
                    self.env._("The alert condition is no longer applicable.")
                )
        self.write({"state": "open", "resolved_date": False})
        return True

    def action_send_notification(self):
        for alert in self.filtered(lambda item: item.state == "open"):
            alert._send_configured_notifications(force=True)
        return True

    def action_view_related_alerts(self):
        self.ensure_one()
        action = self.env.ref(
            "stock_expiration_alert.action_stock_expiration_alert"
        ).read()[0]
        action["domain"] = [
            ("id", "!=", self.id),
            ("lot_id", "=", self.lot_id.id),
            ("location_id", "=", self.location_id.id),
        ]
        return action

    @api.model
    def action_run_expiration_alert_check(self):
        parameters = self.env["ir.config_parameter"].sudo()
        if parameters.get_param("stock_expiration_alert.enabled", "False") not in (
            "True",
            "1",
            True,
        ):
            return True
        rules = (
            self.env["stock.expiration.alert.rule"]
            .sudo()
            .search([("active", "=", True)], order="sequence, id")
        )
        now = fields.Datetime.now()
        today = fields.Date.context_today(self)
        seen_alert_ids = set()
        quants = (
            self.env["stock.quant"]
            .sudo()
            .search(
                [
                    ("quantity", ">", 0),
                    ("location_id.usage", "=", "internal"),
                    ("lot_id", "!=", False),
                    ("lot_id.expiration_date", "!=", False),
                ]
            )
        )
        grouped_quants = {}
        for quant in quants:
            key = (quant.lot_id.id, quant.location_id.id)
            if key not in grouped_quants:
                grouped_quants[key] = {"quant": quant, "quantity": 0.0}
            grouped_quants[key]["quantity"] += quant.quantity
        for group in grouped_quants.values():
            quant = group["quant"]
            try:
                alert = self._process_quant(quant, group["quantity"], rules, now, today)
                if alert:
                    seen_alert_ids.add(alert.id)
            except Exception:
                _logger.exception(
                    "Error while processing stock quant %s", quant.display_name
                )
                existing_alert = self.sudo().search(
                    [
                        ("lot_id", "=", quant.lot_id.id),
                        ("location_id", "=", quant.location_id.id),
                        ("state", "=", "open"),
                    ],
                    limit=1,
                )
                if existing_alert:
                    seen_alert_ids.add(existing_alert.id)
        stale_alerts = (
            self.sudo()
            .search([("state", "=", "open")])
            .filtered(lambda alert: alert.id not in seen_alert_ids)
        )
        stale_alerts.write(
            {"state": "resolved", "resolved_date": now, "last_alert_date": now}
        )
        return True

    @api.model
    def _process_quant(self, quant, quantity, rules, now, today):
        expiration_date = quant.lot_id.expiration_date
        matching_rule = next(
            (rule for rule in rules if rule.matches_quant(quant)), False
        )
        open_alert = self.sudo().search(
            [
                ("lot_id", "=", quant.lot_id.id),
                ("location_id", "=", quant.location_id.id),
                ("state", "=", "open"),
            ],
            limit=1,
        )
        if not matching_rule or expiration_date.date() > fields.Date.add(
            today, days=matching_rule.days_before_expiration
        ):
            if open_alert:
                open_alert.write(
                    {"state": "resolved", "resolved_date": now, "last_alert_date": now}
                )
            return False
        days_remaining = (expiration_date.date() - today).days
        values = {
            "rule_id": matching_rule.id,
            "assigned_user_id": matching_rule.user_id.id,
            "severity": matching_rule.severity,
            "quantity": quantity,
            "expiration_date": expiration_date,
            "days_remaining": days_remaining,
            "last_alert_date": now,
        }
        if open_alert:
            open_alert.write(values)
            alert = open_alert
        else:
            values.update(
                {
                    "product_id": quant.product_id.id,
                    "lot_id": quant.lot_id.id,
                    "warehouse_id": quant.location_id.warehouse_id.id,
                    "location_id": quant.location_id.id,
                    "company_id": quant.company_id.id,
                    "uom_id": quant.product_uom_id.id,
                    "first_alert_date": now,
                }
            )
            alert = self.sudo().create(values)
        mode = matching_rule.notification_mode
        alert._send_configured_notifications(notification_mode=mode)
        return alert

    def _send_configured_notifications(self, notification_mode=None, force=False):
        parameters = self.env["ir.config_parameter"].sudo()
        resend_hours = int(
            parameters.get_param("stock_expiration_alert.resend_hours", "24") or 0
        )
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
            mode = notification_mode or alert.rule_id.notification_mode
            if mode == "default":
                mode = parameters.get_param(
                    "stock_expiration_alert.notification_mode", "activity"
                )
            sent = False
            if mode in ("activity", "both"):
                sent = alert._send_activity(user) or sent
            if mode in ("email", "both"):
                sent = alert._send_email(user) or sent
            if sent:
                alert.write({"last_notification_date": now})

    def _send_activity(self, user):
        self.ensure_one()
        notification = (
            self.env["stock.expiration.alert.notification"]
            .sudo()
            .create({"alert_id": self.id, "user_id": user.id, "channel": "activity"})
        )
        try:
            activity = (
                self.env["mail.activity"]
                .sudo()
                .create(
                    {
                        "activity_type_id": self.env.ref(
                            "stock_expiration_alert.mail_activity_type_stock_expiration_alert"
                        ).id,
                        "summary": self.env._(
                            "Expiring stock: %(product)s",
                            product=self.product_id.display_name,
                        ),
                        "note": self.env._(
                            "Lot %(lot)s expires on %(date)s. Quantity: %(quantity)s %(uom)s.",
                            lot=self.lot_id.name,
                            date=self.expiration_date,
                            quantity=self.quantity,
                            uom=self.uom_id.name or "",
                        ),
                        "res_model_id": self.env["ir.model"]._get_id(self._name),
                        "res_id": self.id,
                        "user_id": user.id,
                        "date_deadline": fields.Date.context_today(self),
                        "stock_expiration_notification_id": notification.id,
                    }
                )
            )
            notification.write({"activity_id": activity.id})
            return True
        except Exception as exception:
            notification.write({"state": "error", "error_message": str(exception)})
            _logger.exception(
                "Could not create the expiration activity for %s", self.display_name
            )
            return False

    def _send_email(self, user):
        self.ensure_one()
        notification = (
            self.env["stock.expiration.alert.notification"]
            .sudo()
            .create(
                {
                    "alert_id": self.id,
                    "user_id": user.id,
                    "channel": "email",
                    "email_to": user.email or "",
                }
            )
        )
        if not user.email:
            notification.write(
                {
                    "state": "error",
                    "error_message": self.env._(
                        "The user does not have an email address configured."
                    ),
                }
            )
            return False
        try:
            self.env.ref(
                "stock_expiration_alert.mail_template_stock_expiration_alert"
            ).sudo().send_mail(
                self.id, force_send=True, email_values={"email_to": user.email}
            )
            return True
        except Exception as exception:
            notification.write({"state": "error", "error_message": str(exception)})
            _logger.exception(
                "Could not send the expiration email for %s", self.display_name
            )
            return False
