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
from odoo import fields, models


class StockLowAlertNotification(models.Model):
    _name = "stock.low.alert.notification"
    _description = "Low stock alert notification history"
    _order = "sent_at desc, id desc"

    alert_id = fields.Many2one("stock.low.alert", string="Alert", required=True, ondelete="cascade", index=True)
    user_id = fields.Many2one("res.users", string="User", required=True, ondelete="restrict")
    channel = fields.Selection([("activity", "Activity"), ("email", "Email")], required=True)
    sent_at = fields.Datetime(string="Sent at", default=fields.Datetime.now, required=True)
    state = fields.Selection(
        [("sent", "Sent"), ("done", "Done"), ("cancelled", "Ignored/Deleted"), ("error", "Error")],
        string="Status", default="sent", required=True,
    )
    activity_id = fields.Many2one("mail.activity", string="Activity", ondelete="set null")
    email_to = fields.Char(string="Email")
    error_message = fields.Text(string="Error details")
