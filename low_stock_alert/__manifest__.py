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
{
    "name": "Make IT - Low Stock Alerts",
    "summary": "Low stock alerts based on reordering rules",
    "version": "18.0.1.1.0",
    "category": "Inventory/Inventory",
    "author": "Make IT",
    "website": "http://www.makeitgroup.com/",
    "license": "LGPL-3",
    "depends": ["stock", "purchase", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_template_data.xml",
        "data/ir_cron_data.xml",
        "views/stock_low_alert_views.xml",
        "views/stock_low_alert_responsible_views.xml",
        "views/stock_low_alert_exception_views.xml",
        "views/res_config_settings_views.xml",
        "views/stock_low_alert_menus.xml",
    ],
    "assets": {},
    "installable": True,
    "application": False,
}
