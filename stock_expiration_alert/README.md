# Make IT - Stock Expiration Alerts (Odoo 19)

Proactive monitoring for expiring and expired stock, built on Odoo's native lot/serial expiration dates and stock quants.

## Features

- Prioritized rules scoped by product, product category, warehouse, and/or internal location.
- A configurable number of days before expiration for every rule.
- Responsible user, severity (information, warning, or critical), and notification channel per rule.
- Odoo activities, email notifications, or both, with auditable delivery history.
- One active alert per lot and location, preserving historical alerts after resolution.
- Current quantity, expiration date, days remaining, warehouse, location, responsible, and rule on every alert.
- Automatic resolution when the lot no longer has positive stock or no longer meets any active rule.
- Daily scheduled analysis and a configurable resend interval.
- Global enable/disable and default notification channel in Inventory settings.
- Spanish (`es`) and Spanish / Mexico (`es_MX`) translations.

## Native Odoo integration

The module depends on Odoo's `product_expiry` module. It does not add a parallel expiration date. It reads `stock.lot.expiration_date` and evaluates positive `stock.quant` records in internal locations, so the same lot can be monitored independently in each location where stock exists.

## Rule precedence

Rules are evaluated by ascending sequence. The first active rule matching the quant's company and configured scope is used. Empty scope fields are wildcards. A location rule includes its child locations.

An alert is applicable when:

```text
lot expiration date <= today + configured days before expiration
and quantity in the internal location > 0
```

Negative `days_remaining` values identify already expired stock.

## Installation and configuration

1. Add this repository to the Odoo 19 addons path and update the Apps list.
2. Install **Make IT - Stock Expiration Alerts**. Odoo installs `product_expiry` if needed.
3. Enable **Stock Expiration Alerts** under **Inventory > Configuration > Settings**.
4. Create at least one rule under **Inventory > Reporting > Expiration Alerts > Alert Rules**.
5. Ensure monitored products use lot or serial tracking and their lots have an expiration date.
6. Run **Stock expiration alerts: review lots** manually for an immediate check, or wait for its daily execution.

## Quick test

1. Create a tracked storable product and receive stock in a lot.
2. Set the lot expiration date five days from today.
3. Create a rule with a ten-day threshold and choose a responsible user.
4. Run the scheduled action.
5. Open **Inventory > Reporting > Expiration Alerts > Alerts** and verify the alert and notification history.
6. Remove the stock or move the expiration beyond the threshold, rerun the action, and verify automatic resolution.

## Security

Inventory users can read alerts, rules, and notification history and can update alert workflow state. Inventory managers can create and maintain rules and have full module model access. Rules and alerts are company-aware.

## Compatibility

- Odoo 19.0
- Source code and technical definitions are 100% English
- LGPL-3

