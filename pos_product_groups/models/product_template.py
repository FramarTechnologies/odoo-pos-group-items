# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_product_group = fields.Boolean(string='Is Product Group (Big Group)', default=False)
    product_group_id = fields.Many2one('product.group', string='Product Group (Big Group)', ondelete='set null')
    is_product_sub_group = fields.Boolean(string='Is Product Sub Group', default=False)
    product_sub_group_id = fields.Many2one('product.group.sub', string='Product Sub Group', ondelete='set null')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # These fields are inherited from product.template, but we need to make sure
    # they're accessible on product.product for POS
    is_product_group = fields.Boolean(related='product_tmpl_id.is_product_group', readonly=True, store=True)
    product_group_id = fields.Many2one(related='product_tmpl_id.product_group_id', readonly=True, store=True)
    is_product_sub_group = fields.Boolean(related='product_tmpl_id.is_product_sub_group', readonly=True, store=True)
    product_sub_group_id = fields.Many2one(related='product_tmpl_id.product_sub_group_id', readonly=True, store=True)




