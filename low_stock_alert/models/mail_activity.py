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


class MailActivity(models.Model):
    _inherit = "mail.activity"

    low_stock_notification_id = fields.Many2one(
        "stock.low.alert.notification", string="Low stock notification", ondelete="set null", index=True, copy=False,
    )

    def action_feedback(self, feedback=False, attachment_ids=None):
        notifications = self.mapped("low_stock_notification_id").filtered(lambda n: n.state == "sent")
        result = super().action_feedback(feedback=feedback, attachment_ids=attachment_ids)
        notifications.write({"state": "done"})
        return result

    def unlink(self):
        notifications = self.mapped("low_stock_notification_id").filtered(lambda n: n.state == "sent")
        result = super().unlink()
        notifications.write({"state": "cancelled"})
        return result
