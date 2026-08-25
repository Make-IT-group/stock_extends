from odoo import fields, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    stock_expiration_notification_id = fields.Many2one(
        "stock.expiration.alert.notification",
        string="Stock expiration notification",
        ondelete="set null",
        index=True,
        copy=False,
    )

    def action_feedback(self, feedback=False, attachment_ids=None):
        notifications = self.mapped("stock_expiration_notification_id").filtered(
            lambda notification: notification.state == "sent"
        )
        result = super().action_feedback(
            feedback=feedback, attachment_ids=attachment_ids
        )
        notifications.write({"state": "done"})
        return result

    def unlink(self):
        notifications = self.mapped("stock_expiration_notification_id").filtered(
            lambda notification: notification.state == "sent"
        )
        result = super().unlink()
        notifications.write({"state": "cancelled"})
        return result
