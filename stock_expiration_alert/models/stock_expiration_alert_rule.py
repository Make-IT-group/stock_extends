from odoo import api, fields, models
from odoo.exceptions import ValidationError


class StockExpirationAlertRule(models.Model):
    _name = "stock.expiration.alert.rule"
    _description = "Stock expiration alert rule"
    _order = "sequence, id"

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10, help="Lower values have higher priority.")
    name = fields.Char(required=True, translate=True)
    product_id = fields.Many2one("product.product")
    category_id = fields.Many2one("product.category", string="Product category")
    warehouse_id = fields.Many2one("stock.warehouse")
    location_id = fields.Many2one("stock.location", domain=[("usage", "=", "internal")])
    days_before_expiration = fields.Integer(
        string="Days before expiration", required=True, default=30
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible user",
        required=True,
        ondelete="restrict",
        domain=[("share", "=", False)],
    )
    severity = fields.Selection(
        [("info", "Information"), ("warning", "Warning"), ("critical", "Critical")],
        default="warning",
        required=True,
    )
    notification_mode = fields.Selection(
        [
            ("default", "Use global settings"),
            ("activity", "Activity"),
            ("email", "Email"),
            ("both", "Activity and email"),
        ],
        string="Notification",
        default="default",
        required=True,
    )
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True
    )

    @api.constrains("days_before_expiration")
    def _check_days_before_expiration(self):
        if any(rule.days_before_expiration < 0 for rule in self):
            raise ValidationError(
                self.env._("Days before expiration cannot be negative.")
            )

    @api.constrains("product_id", "category_id")
    def _check_product_category(self):
        for rule in self:
            if (
                rule.product_id
                and rule.category_id
                and rule.product_id.categ_id != rule.category_id
            ):
                raise ValidationError(
                    self.env._(
                        "The configured category does not match the selected product category."
                    )
                )

    @api.constrains("warehouse_id", "location_id")
    def _check_warehouse_location(self):
        for rule in self:
            if rule.warehouse_id and rule.location_id:
                warehouse = rule.location_id.warehouse_id
                if warehouse and warehouse != rule.warehouse_id:
                    raise ValidationError(
                        self.env._(
                            "The selected location does not belong to the configured warehouse."
                        )
                    )

    def matches_quant(self, quant):
        self.ensure_one()
        product = quant.product_id
        location = quant.location_id
        return (
            self.company_id == quant.company_id
            and (not self.product_id or self.product_id == product)
            and (not self.category_id or self.category_id == product.categ_id)
            and (not self.warehouse_id or self.warehouse_id == location.warehouse_id)
            and (
                not self.location_id
                or location == self.location_id
                or location.parent_path.startswith(self.location_id.parent_path)
            )
        )
