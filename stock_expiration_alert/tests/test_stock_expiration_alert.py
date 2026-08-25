from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestStockExpirationAlert(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "Expiration test product",
                "is_storable": True,
                "tracking": "lot",
                "use_expiration_date": True,
            }
        )
        cls.location = cls.env.ref("stock.stock_location_stock")
        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "EXP-TEST-001",
                "product_id": cls.product.id,
                "expiration_date": fields.Datetime.now() + timedelta(days=5),
                "company_id": cls.env.company.id,
            }
        )
        cls.quant = cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": cls.location.id,
                "lot_id": cls.lot.id,
                "quantity": 4.0,
            }
        )
        cls.rule = cls.env["stock.expiration.alert.rule"].create(
            {
                "name": "Test rule",
                "product_id": cls.product.id,
                "days_before_expiration": 10,
                "user_id": cls.env.user.id,
                "severity": "critical",
            }
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "stock_expiration_alert.enabled", True
        )
        cls.env["ir.config_parameter"].sudo().set_param(
            "stock_expiration_alert.resend_hours", 0
        )

    def test_rule_matches_quant(self):
        self.assertTrue(self.rule.matches_quant(self.quant))

    def test_cron_creates_and_resolves_alert(self):
        Alert = self.env["stock.expiration.alert"]
        Alert.action_run_expiration_alert_check()
        alert = Alert.search([("lot_id", "=", self.lot.id), ("state", "=", "open")])
        self.assertEqual(len(alert), 1)
        self.assertEqual(alert.rule_id, self.rule)
        self.assertEqual(alert.severity, "critical")
        self.assertEqual(alert.quantity, 4.0)

        self.lot.expiration_date = fields.Datetime.now() + timedelta(days=20)
        Alert.action_run_expiration_alert_check()
        self.assertEqual(alert.state, "resolved")
