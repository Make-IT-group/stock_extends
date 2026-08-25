# Make IT - Low Stock Alerts (Odoo 19)

Low stock monitoring based on Odoo reordering rules (`stock.warehouse.orderpoint`). The module creates traceable alerts when current stock reaches or falls below the configured minimum.

## Features

- Menu: **Inventory > Reporting > Alerts**.
- Alert records with assigned user, creation date, product, current stock, minimum, maximum, latest purchase, vendor, latest purchased quantity, notification count, and notification history.
- Related alert history for the same reordering rule.
- Responsible rules configurable by product, category, and/or warehouse, evaluated by sequence.
- Exceptions configurable by product, category, warehouse, location, or reordering rule, with optional validity dates.
- Notifications by Odoo activity, email, or both.
- Activity tracking: sent, completed, ignored/deleted, or error.
- Configurable automatic resend interval.
- Enable/disable switch under **Inventory > Configuration > Settings**.
- Hourly scheduled action. When the feature is disabled, the scheduled action exits without generating alerts.

## Trigger rule

An open alert is created or updated when:

`current stock <= reordering rule minimum quantity`

When stock rises above the minimum, the open alert is automatically resolved. If stock falls again later, a new alert is created and remains related to previous alerts for the same reordering rule.

## Installation

1. Copy `low_stock_alert` into an Odoo addons path.
2. Restart Odoo.
3. Update the Apps list.
4. Install **Make IT - Low Stock Alerts**.
5. Open **Inventory > Configuration > Settings** and enable low stock alerts.
6. Configure at least one responsible rule under **Inventory > Reporting > Alerts > Responsibles**.

## Quick test

1. Create a storable product with a vendor.
2. Create a reordering rule, for example minimum `10` and maximum `50`.
3. Set stock in the rule location to `10` or less.
4. Configure a responsible and choose Activity, Email, or Activity and email.
5. Run the scheduled action **Stock alerts: review reordering rules** manually, or wait for the hourly run.
6. Review **Inventory > Reporting > Alerts > Stock alerts**.
7. Complete the generated activity and verify that the notification history changes to **Done**.
8. Raise stock above the minimum and run the scheduled action again; the alert should become **Resolved**.

## Languages

The source code and technical definitions are written in English. Translations are included for:

- Spanish (`es`)
- Spanish / Mexico (`es_MX`)


## Odoo 19 compatibility

This version is migrated for Odoo 19. The migration keeps the original module behavior and adapts technical references to the Odoo 19 API, including the Purchase Order Line unit-of-measure field (`product_uom_id`) and the Odoo 19 product quantity precision (`Product Unit`).
