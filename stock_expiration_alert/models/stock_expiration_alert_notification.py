from odoo import fields, models


class StockExpirationAlertNotification(models.Model):
    _name = "stock.expiration.alert.notification"
    _description = "Stock expiration alert notification history"
    _order = "sent_at desc, id desc"

    alert_id = fields.Many2one(
        "stock.expiration.alert", required=True, ondelete="cascade", index=True
    )
    user_id = fields.Many2one("res.users", required=True, ondelete="restrict")
    channel = fields.Selection(
        [("activity", "Activity"), ("email", "Email")], required=True
    )
    sent_at = fields.Datetime(default=fields.Datetime.now, required=True)
    state = fields.Selection(
        [
            ("sent", "Sent"),
            ("done", "Done"),
            ("cancelled", "Ignored/Deleted"),
            ("error", "Error"),
        ],
        default="sent",
        required=True,
    )
    activity_id = fields.Many2one("mail.activity", ondelete="set null")
    email_to = fields.Char()
    error_message = fields.Text()
