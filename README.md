# Make IT — Stock Extensions for Odoo 19

<p align="center">
  <img src="low_stock_alert/static/description/icon.png" alt="Make IT - Low Stock Alerts" width="140" />
</p>

<p align="center">
  <strong>Inventory extensions for Odoo 19 focused on proactive, traceable stock monitoring.</strong>
</p>

<p align="center">
  <img alt="Odoo 19" src="https://img.shields.io/badge/Odoo-19.0-875A7B?logo=odoo&logoColor=white" />
  <img alt="License LGPL-3" src="https://img.shields.io/badge/License-LGPL--3-blue" />
  <img alt="Status" src="https://img.shields.io/badge/status-active-success" />
</p>

---

## Overview

This repository contains inventory extensions developed by **Make IT** for **Odoo 19**.

The current module, **Low Stock Alerts**, extends Odoo's native reordering rules (`stock.warehouse.orderpoint`) with a configurable alerting layer. It detects products whose current stock reaches or falls below the configured minimum quantity and creates traceable alerts for the responsible users.

Instead of replacing Odoo's replenishment workflow, the module works on top of the standard minimum and maximum quantities already defined in reordering rules.

## Included module

### `low_stock_alert`

**Make IT - Low Stock Alerts**

Version: `19.0.1.0.2`

Dependencies:

- `stock`
- `purchase`
- `mail`

The module provides centralized low-stock monitoring, configurable responsibility rules, exceptions, notification history, activity tracking, email notifications, and automatic alert resolution.

### `stock_expiration_alert`

**Make IT - Stock Expiration Alerts**

Version: `19.0.1.0.0`

Monitors positive stock by lot and internal location using Odoo's native expiration dates. Prioritized rules configure product/category/warehouse/location scope, advance warning days, responsible user, severity, and notification channel.

## Main features

- Uses native Odoo reordering rules as the source for minimum and maximum stock levels.
- Creates an alert when:

  ```text
  current stock <= minimum quantity
  ```

- Automatically resolves an open alert when stock rises above the minimum quantity.
- Creates a new related alert if the product falls below the minimum again later.
- Keeps historical alerts related to the same reordering rule.
- Stores the main information needed to investigate each stock situation:
  - assigned user;
  - alert creation date;
  - product;
  - warehouse and location;
  - current stock;
  - configured minimum quantity;
  - configured maximum quantity;
  - latest purchase order;
  - latest purchase date;
  - vendor;
  - quantity purchased in the latest purchase;
  - number of notifications sent;
  - related alerts;
  - notification and activity history.
- Supports notifications through:
  - Odoo activity;
  - email;
  - both activity and email.
- Tracks whether generated activities were completed, deleted/ignored, sent, or failed.
- Supports configurable automatic notification resend intervals.
- Includes configurable responsible rules by product, product category, and warehouse.
- Includes exceptions by product, category, warehouse, location, or specific reordering rule.
- Exceptions can optionally have validity dates.
- Can be enabled or disabled from Inventory settings.
- Includes an hourly scheduled action for automatic stock evaluation.
- Includes Spanish and Spanish (Mexico) translations.

## Menu location

After installation, the module adds its options under:

```text
Inventory
└── Reporting
    └── Alerts
        ├── Stock Alerts
        ├── Responsibles
        └── Exceptions
```

General module settings are available under:

```text
Inventory > Configuration > Settings
```

## How it works

1. Odoo products are configured with standard **Reordering Rules**.
2. Each rule defines the minimum and maximum quantity for a product and location.
3. The module periodically reviews the active reordering rules.
4. When current stock reaches or falls below the minimum quantity, the module evaluates:
   - configured exceptions;
   - applicable responsible rule;
   - configured notification method.
5. If the rule is eligible, a low-stock alert is created or updated.
6. The assigned user receives an Odoo activity, an email, or both depending on configuration.
7. Every notification is recorded in the alert history.
8. If the stock remains low, the notification can be resent according to the configured interval.
9. When stock rises above the minimum quantity, the alert is automatically marked as resolved.

## Responsible configuration

Responsible rules define who should receive an alert.

A rule can be limited by:

- product;
- product category;
- warehouse.

Rules are evaluated according to their configured sequence, allowing more specific rules to take priority over general ones.

Each responsible rule can define the notification method used for the assigned user.

## Exceptions

Exceptions allow specific stock situations to be excluded from alert generation without changing the original Odoo reordering rule.

An exception can be configured for:

- a product;
- a product category;
- a warehouse;
- a stock location;
- a specific reordering rule.

Optional start and end dates can be used when an exception should only apply during a specific period.

## Notifications

The module supports three notification modes:

| Mode | Behavior |
| --- | --- |
| Activity | Creates an Odoo activity for the responsible user. |
| Email | Sends an email notification to the responsible user. |
| Activity and Email | Creates the activity and sends the email. |

Notification history is stored on the alert so repeated notifications can be audited later.

## Scheduled action

The module installs the following scheduled action:

```text
Stock alerts: review reordering rules
```

By default, it runs every hour.

The scheduled action can also be executed manually from Odoo's Scheduled Actions menu when testing or troubleshooting.

If the feature is disabled from Inventory settings, the scheduled action exits without creating or updating alerts.

## Installation

1. Clone this repository into an Odoo addons path:

   ```bash
   git clone -b 19.0 https://github.com/Asociacion-Mexicana-de-Ingenieria/stock_extends.git
   ```

2. Make sure the repository path is included in your Odoo `addons_path`.
3. Restart the Odoo service.
4. Enable developer mode if required.
5. Update the Apps list.
6. Search for **Make IT - Low Stock Alerts**.
7. Install the module.

## Initial configuration

After installing the module:

1. Open **Inventory > Configuration > Settings**.
2. Enable **Low Stock Alerts**.
3. Configure the default notification mode.
4. Configure the notification resend interval.
5. Open **Inventory > Reporting > Alerts > Responsibles**.
6. Create at least one responsible rule.
7. Optionally configure exceptions.
8. Make sure the products to monitor have valid Odoo reordering rules.

## Quick test

A simple functional test can be performed as follows:

1. Create or select a storable product.
2. Configure a vendor for the product.
3. Create a reordering rule, for example:

   ```text
   Minimum: 10
   Maximum: 50
   ```

4. Set the available stock at the rule location to `10` units or less.
5. Configure a responsible rule for the product, category, or warehouse.
6. Select **Activity**, **Email**, or **Activity and Email**.
7. Execute the scheduled action manually:

   ```text
   Stock alerts: review reordering rules
   ```

8. Open:

   ```text
   Inventory > Reporting > Alerts > Stock Alerts
   ```

9. Confirm that the alert contains the expected product, stock values, responsible user, and notification history.
10. Increase stock above the minimum quantity and run the scheduled action again.
11. Confirm that the alert is automatically resolved.

## Languages

The source code and technical definitions are written in **English**.

Translations are included for:

- Spanish (`es`)
- Spanish / Mexico (`es_MX`)

Odoo displays translated labels and messages according to the language configured for each user.

## Repository structure

```text
stock_extends/
├── README.md
├── low_stock_alert/
└── stock_expiration_alert/
    ├── data/
    ├── i18n/
    ├── models/
    ├── security/
    ├── static/
    │   └── description/
    ├── views/
    ├── __init__.py
    ├── __manifest__.py
    └── README.md
```

## Compatibility

This branch is intended for:

```text
Odoo 19.0
```

Use the corresponding repository branch for other Odoo versions when available.

## License

This module is distributed under the **GNU Lesser General Public License v3.0 (LGPL-3)**, as declared in the Odoo module manifest.

## Author

**Make IT**  
Odoo development and business solutions.

Website: [makeitgroup.com](http://www.makeitgroup.com/)

---

<p align="center">
  <strong>Make IT — turning operational needs into practical Odoo solutions.</strong>
</p>
