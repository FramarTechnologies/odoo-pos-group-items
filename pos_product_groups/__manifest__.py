# -*- coding: utf-8 -*-
{
    'name': 'POS Product Groups (Combo Products)',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Create combo products with multiple price variants for POS',
    'description': """
        POS Product Groups Module
        =========================
        
        This module allows you to:
        - Create product groups (combo products) like Rolex, Kikomando, etc.
        - Set multiple price variants for each product group
        - Add components to product groups
        - When selling a combo product, it shows on receipt but posts components separately
        - Quick selection with price dropdown in POS interface
        
        Perfect for food businesses selling combo meals!
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['point_of_sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_group_views.xml',
        'views/product_template_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_product_groups/static/src/js/main.js',
            'pos_product_groups/static/src/js/models.js',
            'pos_product_groups/static/src/js/orderline_patch.js',
            'pos_product_groups/static/src/js/product_group_screen.js',
            'pos_product_groups/static/src/js/product_group_popup.js',
            'pos_product_groups/static/src/xml/product_group_screen.xml',
            'pos_product_groups/static/src/xml/product_group_popup.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

