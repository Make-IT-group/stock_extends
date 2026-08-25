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


class StockLowAlertException(models.Model):
    _name = "stock.low.alert.exception"
    _description = "Low stock alert exception"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Name", required=True)
    reason = fields.Text(string="Reason")
    date_from = fields.Datetime(string="Valid from")
    date_to = fields.Datetime(string="Valid until")
    product_id = fields.Many2one("product.product", string="Product")
    category_id = fields.Many2one("product.category", string="Category")
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse")
    location_id = fields.Many2one("stock.location", string="Location", domain=[("usage", "=", "internal")])
    orderpoint_id = fields.Many2one("stock.warehouse.orderpoint", string="Reordering rule")

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise ValidationError("The start date cannot be later than the end date.")

    @api.constrains("product_id", "category_id", "warehouse_id", "location_id", "orderpoint_id")
    def _check_scope(self):
        for rec in self:
            if not any([rec.product_id, rec.category_id, rec.warehouse_id, rec.location_id, rec.orderpoint_id]):
                raise ValidationError("The exception must specify at least one product, category, warehouse, location, or reordering rule.")
