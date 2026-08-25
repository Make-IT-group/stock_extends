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


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_low_alert_enabled = fields.Boolean(
        string="Enable low stock alerts",
        config_parameter="low_stock_alert.enabled",
        default=False,
    )
    stock_low_alert_notification_mode = fields.Selection(
        [
            ("activity", "Activity"),
            ("email", "Email"),
            ("both", "Activity and email"),
        ],
        string="Default notification channel",
        config_parameter="low_stock_alert.notification_mode",
        default="activity",
        required=True,
    )
    stock_low_alert_resend_hours = fields.Integer(
        string="Resend every (hours)",
        config_parameter="low_stock_alert.resend_hours",
        default=24,
        help="While stock remains at or below the minimum, the alert can be sent again after this interval. Use 0 to disable automatic resending.",
    )
