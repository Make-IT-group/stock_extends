from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_expiration_alert_enabled = fields.Boolean(
        string="Enable stock expiration alerts",
        config_parameter="stock_expiration_alert.enabled",
        default=False,
    )
    stock_expiration_alert_notification_mode = fields.Selection(
        [("activity", "Activity"), ("email", "Email"), ("both", "Activity and email")],
        string="Default notification channel",
        config_parameter="stock_expiration_alert.notification_mode",
        default="activity",
        required=True,
    )
    stock_expiration_alert_resend_hours = fields.Integer(
        string="Resend every (hours)",
        config_parameter="stock_expiration_alert.resend_hours",
        default=24,
        help="Resend open alerts after this interval. Use 0 to disable automatic resending.",
    )
