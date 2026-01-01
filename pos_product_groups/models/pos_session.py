# -*- coding: utf-8 -*-

from odoo import models, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Add product group and sub group fields to product loading, and exclude sub groups from POS"""
        params = super(PosSession, self)._loader_params_product_product()
        
        # Add product group and sub group fields to the fields list
        if 'search_params' in params and 'fields' in params['search_params']:
            fields = params['search_params']['fields']
            if 'is_product_group' not in fields:
                fields.append('is_product_group')
            if 'product_group_id' not in fields:
                fields.append('product_group_id')
            if 'is_product_sub_group' not in fields:
                fields.append('is_product_sub_group')
            if 'product_sub_group_id' not in fields:
                fields.append('product_sub_group_id')
            # Also add product_tmpl_id fields if not already there (needed for related fields)
            if 'product_tmpl_id' not in fields:
                fields.append('product_tmpl_id')
        
        # Exclude sub group products from POS - they should only appear in popup when selecting from big groups
        if 'search_params' in params:
            # Get existing domain or create empty one
            domain = params['search_params'].get('domain', [])
            # Add condition to exclude sub groups: only show products that are NOT sub groups
            # This will exclude products where is_product_sub_group is True
            domain.append(('is_product_sub_group', '!=', True))
            params['search_params']['domain'] = domain
        
        return params

