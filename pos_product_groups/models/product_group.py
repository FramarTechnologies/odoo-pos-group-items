# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class ProductGroup(models.Model):
    """Big Group - Main collection (e.g., Kikomando, Rolex)"""
    _name = 'product.group'
    _description = 'Product Group (Big Group)'
    _order = 'name'

    name = fields.Char(string='Group Name', required=True, help='e.g., Kikomando, Rolex')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    
    # Sub groups (e.g., Kikomando 1500, Kikomando 3000)
    sub_group_ids = fields.One2many(
        'product.group.sub',
        'product_group_id',
        string='Sub Groups',
        help='Sub groups within this big group (e.g., Kikomando 1500, Kikomando 3000)'
    )
    
    # Related product template for the big group (shown in POS)
    product_template_id = fields.Many2one(
        'product.template',
        string='Product Template',
        help='Product template for this big group (shown in POS)'
    )

    @api.model
    def create(self, vals):
        """Create a product template when creating a big group"""
        res = super(ProductGroup, self).create(vals)
        # Create a product template for this big group
        try:
            # Build product template values
            template_vals = {
                'name': vals.get('name'),
                'type': 'product',
                'available_in_pos': True,
                'sale_ok': True,
                'purchase_ok': False,
                'is_product_group': True,
                'product_group_id': res.id,
                'list_price': 0.0,  # Price will be set by sub groups
            }
            
            # Don't set pos_categ_ids - let Odoo handle it automatically or set it manually later
            # This avoids foreign key constraint issues during creation
            
            product_template = self.env['product.template'].create(template_vals)
            res.product_template_id = product_template.id
            
            # Ensure the product variant also has the fields
            for product_variant in product_template.product_variant_ids:
                product_variant.is_product_group = True
                product_variant.product_group_id = res.id
        except Exception as e:
            # Log error but don't fail the creation
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Error creating product template for product group {res.id}: {e}")
        
        return res

    def write(self, vals):
        """Update product template when product group is updated"""
        res = super(ProductGroup, self).write(vals)
        if 'name' in vals and self.product_template_id and self.product_template_id.exists():
            try:
                # Update name safely
                self.product_template_id.sudo().write({'name': vals['name']})
            except Exception as e:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.warning(f"Error updating product template name for product group {self.id}: {e}")
        return res

    def unlink(self):
        """Clean up product template and its relationships before deletion"""
        # Store product template IDs before deletion
        template_ids = self.mapped('product_template_id').ids
        
        # Remove POS category relationships first to avoid foreign key constraint
        for template in self.mapped('product_template_id'):
            if template.exists():
                # Clear pos_categ_ids to remove the relationship
                template.write({'pos_categ_ids': [(5, 0, 0)]})
        
        # Delete the product templates
        templates = self.env['product.template'].browse(template_ids)
        templates.filtered(lambda t: t.exists()).unlink()
        
        return super(ProductGroup, self).unlink()


class ProductGroupSub(models.Model):
    """Sub Group - Specific variant with price (e.g., Kikomando 1500, Kikomando 3000)"""
    _name = 'product.group.sub'
    _description = 'Product Sub Group'
    _order = 'sequence, price'
    
    @api.model
    def _hide_all_sub_groups_from_pos(self):
        """Hide all existing sub group products from POS (called on module upgrade)"""
        sub_groups = self.search([])
        for sub_group in sub_groups:
            if sub_group.product_template_id and sub_group.product_template_id.exists():
                if sub_group.product_template_id.available_in_pos:
                    try:
                        sub_group.product_template_id.write({'available_in_pos': False})
                        _logger.info(f"Hidden sub group product '{sub_group.product_template_id.name}' from POS")
                    except Exception as e:
                        _logger.warning(f"Error hiding sub group product '{sub_group.product_template_id.name}' from POS: {e}")

    name = fields.Char(string='Sub Group Name', required=True, help='e.g., Kikomando 1500, Kikomando 3000')
    product_group_id = fields.Many2one('product.group', string='Big Group', required=True, ondelete='cascade')
    price = fields.Float(string='Price', required=True, digits='Product Price', help='Selling price for this sub group')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10, help='Order of display in POS')
    
    # Components that make up this sub group
    component_ids = fields.One2many(
        'product.group.component',
        'sub_group_id',
        string='Components',
        help='Individual products that make up this sub group'
    )
    
    # Related product template for the sub group
    product_template_id = fields.Many2one(
        'product.template',
        string='Product Template',
        help='Product template for this sub group'
    )

    @api.model
    def create(self, vals):
        """Create a product template when creating a sub group"""
        res = super(ProductGroupSub, self).create(vals)
        # Create a product template for this sub group
        try:
            # Check if product_template_id was already set (shouldn't happen, but be safe)
            if res.product_template_id and res.product_template_id.exists():
                # Template already exists, just update it
                template_vals = {}
                if 'name' in vals:
                    template_vals['name'] = vals.get('name')
                if 'price' in vals:
                    template_vals['list_price'] = vals.get('price', 0.0)
                if template_vals:
                    res.product_template_id.sudo().write(template_vals)
            else:
                # Build product template values
                # NOTE: Sub groups should NOT appear in POS - they're only for selection in popup
                template_vals = {
                    'name': vals.get('name'),
                    'type': 'product',
                    'available_in_pos': False,  # Hide sub groups from POS - only show in popup
                    'sale_ok': True,
                    'purchase_ok': False,
                    'is_product_sub_group': True,
                    'product_sub_group_id': res.id,
                    'list_price': vals.get('price', 0.0),
                }
                
                # Don't set pos_categ_ids - let Odoo handle it automatically or set it manually later
                # This avoids foreign key constraint issues during creation
                
                product_template = self.env['product.template'].create(template_vals)
                res.product_template_id = product_template.id
                
                # Ensure the product variant also has the fields
                for product_variant in product_template.product_variant_ids:
                    product_variant.is_product_sub_group = True
                    product_variant.product_sub_group_id = res.id
        except Exception as e:
            # Log error but don't fail the creation
            import logging
            _logger = logging.getLogger(__name__)
            _logger.warning(f"Error creating product template for sub group {res.id}: {e}")
        
        return res

    def write(self, vals):
        """Update product template when sub group is updated"""
        res = super(ProductGroupSub, self).write(vals)
        if self.product_template_id and self.product_template_id.exists():
            try:
                # Before updating, clear any problematic pos_categ_ids relationships
                # This prevents foreign key constraint errors
                template = self.product_template_id.sudo()
                if template.pos_categ_ids:
                    try:
                        # Clear pos_categ_ids to avoid constraint issues
                        template.write({'pos_categ_ids': [(5, 0, 0)]})
                    except Exception:
                        # If clearing fails, continue anyway
                        pass
                
                update_vals = {}
                if 'name' in vals:
                    update_vals['name'] = vals['name']
                if 'price' in vals:
                    # Use list_price (list price) - correct field name
                    # Check if field exists before writing
                    if 'list_price' in template._fields:
                        update_vals['list_price'] = vals['price']
                # Ensure sub groups are always hidden from POS (they should only appear in popup)
                if template.available_in_pos:
                    update_vals['available_in_pos'] = False
                if update_vals:
                    # Use sudo() to avoid permission issues and write safely
                    template.write(update_vals)
            except Exception as e:
                # If there's an error with the product template, log it but continue
                _logger.warning(f"Error updating product template for sub group {self.id}: {e}")
                # Don't try to recreate - just log the error and continue
        return res

    def unlink(self):
        """Clean up product template and its relationships before deletion"""
        # Store product template IDs before deletion
        template_ids = self.mapped('product_template_id').ids
        
        # Remove POS category relationships first to avoid foreign key constraint
        for template in self.mapped('product_template_id'):
            if template.exists():
                # Clear pos_categ_ids to remove the relationship
                template.write({'pos_categ_ids': [(5, 0, 0)]})
        
        # Delete the product templates
        templates = self.env['product.template'].browse(template_ids)
        templates.filtered(lambda t: t.exists()).unlink()
        
        return super(ProductGroupSub, self).unlink()

    def action_open_components(self):
        """Open components window for this sub group"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Components - {self.name}',
            'res_model': 'product.group.component',
            'view_mode': 'tree,form',
            'domain': [('sub_group_id', '=', self.id)],
            'context': {'default_sub_group_id': self.id, 'search_default_sub_group_id': self.id},
            'target': 'new',
        }


class ProductGroupComponent(models.Model):
    """Component - Individual products that make up a sub group"""
    _name = 'product.group.component'
    _description = 'Product Group Component'
    _order = 'sequence'

    sub_group_id = fields.Many2one('product.group.sub', string='Sub Group', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Component Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0, digits='Product Unit of Measure')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # Computed field to display product name and quantity
    display_name = fields.Char(string='Component', compute='_compute_display_name', store=False)

    @api.depends('product_id', 'quantity')
    def _compute_display_name(self):
        for record in self:
            if record.product_id:
                qty = int(record.quantity) if record.quantity == int(record.quantity) else record.quantity
                record.display_name = f"{record.product_id.name} - {qty} pieces"
            else:
                record.display_name = ""

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise models.ValidationError('Component quantity must be greater than 0')

