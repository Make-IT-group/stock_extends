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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockLowAlertResponsible(models.Model):
    _name = "stock.low.alert.responsible"
    _description = "Low stock alert responsible"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(compute="_compute_name", store=True)
    user_id = fields.Many2one(
        "res.users", string="Responsible user", required=True, ondelete="cascade",
        domain=[("share", "=", False)],
    )
    product_id = fields.Many2one("product.product", string="Product")
    category_id = fields.Many2one("product.category", string="Category")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    notification_mode = fields.Selection(
        [
            ("default", "Use global settings"),
            ("activity", "Activity"),
            ("email", "Email"),
            ("both", "Activity and email"),
        ],
        string="Notification", default="default", required=True,
    )

    @api.depends("user_id", "product_id", "category_id", "warehouse_id")
    def _compute_name(self):
        for rec in self:
            scope = rec.product_id.display_name or rec.category_id.display_name or rec.warehouse_id.display_name or "General"
            rec.name = f"{rec.user_id.name or ''} - {scope}"

    @api.constrains("product_id", "category_id")
    def _check_product_category(self):
        for rec in self:
            if rec.product_id and rec.category_id and rec.product_id.categ_id != rec.category_id:
                raise ValidationError("The configured category does not match the selected product category.")
