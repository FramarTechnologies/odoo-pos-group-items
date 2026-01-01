# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _order_fields(self, ui_order):
        """Override to expand product sub groups into components before processing"""
        _logger.info("Framar Product Groups: _order_fields called")
        _logger.info(f"Framar Product Groups: ui_order type: {type(ui_order)}")
        _logger.info(f"Framar Product Groups: ui_order keys: {list(ui_order.keys()) if isinstance(ui_order, dict) else 'not a dict'}")
        
        # Ensure ui_order is a dict (it should be, but be safe)
        if not isinstance(ui_order, dict):
            return super(PosOrder, self)._order_fields(ui_order)
        
        # Process lines to expand product sub groups
        processed_lines = []
                        # Track components by product_id to combine duplicates
        component_map = {}  # {product_id: {data, total_qty, total_price, sub_group_unit_prices}}
        
        if ui_order.get('lines'):
            _logger.info(f"Framar Product Groups: Processing {len(ui_order['lines'])} order lines")
            for line_index, line_tuple in enumerate(ui_order['lines']):
                _logger.info(f"Framar Product Groups: Processing line {line_index}: {type(line_tuple)}")
                
                # Line format is (0, 0, {...}) where index 2 is the data dict
                if isinstance(line_tuple, (list, tuple)) and len(line_tuple) >= 3:
                    line_data = line_tuple[2]
                    _logger.info(f"Framar Product Groups: Line {line_index} data keys: {list(line_data.keys()) if isinstance(line_data, dict) else 'not a dict'}")
                    _logger.info(f"Framar Product Groups: Line {line_index} has product_sub_group_id: {line_data.get('product_sub_group_id') if isinstance(line_data, dict) else 'N/A'}")
                    
                    # Check if this line has product_sub_group_id (indicates it's a sub group)
                    product_sub_group_id = line_data.get('product_sub_group_id')
                    product_sub_group_name = line_data.get('product_sub_group_name')
                    product_id = line_data.get('product_id')
                    price_unit = line_data.get('price_unit')
                    full_product_name = line_data.get('full_product_name', '')
                    
                    _logger.info(f"Framar Product Groups: Checking line - product_id: {product_id}, price_unit: {price_unit}, product_sub_group_id: {product_sub_group_id}")
                    
                    # FALLBACK: If product_sub_group_id is missing but product is a product group, find sub group by price
                    if not product_sub_group_id and product_id:
                        try:
                            product = self.env['product.product'].browse(product_id)
                            if product.exists() and product.is_product_group and product.product_group_id:
                                # This is a product group - find the sub group that matches the price
                                _logger.info(f"Framar Product Groups: Product {product_id} is a product group, looking for sub group with price {price_unit}")
                                product_group = product.product_group_id
                                
                                # Find sub group that matches the price
                                matching_sub_group = self.env['product.group.sub'].search([
                                    ('product_group_id', '=', product_group.id),
                                    ('price', '=', price_unit),
                                    ('active', '=', True)
                                ], limit=1)
                                
                                if matching_sub_group:
                                    product_sub_group_id = matching_sub_group.id
                                    _logger.info(f"Framar Product Groups: ✓ Found matching sub group {product_sub_group_id} by price {price_unit}")
                                else:
                                    _logger.warning(f"Framar Product Groups: No sub group found for product group {product_group.id} with price {price_unit}")
                        except Exception as e:
                            _logger.warning(f"Framar Product Groups: Error in fallback detection: {e}")
                    
                    if isinstance(line_data, dict) and product_sub_group_id:
                        qty = line_data.get('qty', 1)
                        _logger.info(f"Framar Product Groups: Found sub group ID {product_sub_group_id} in line {line_index}")
                        
                        _logger.info(f"Framar Product Groups: Expanding sub group {product_sub_group_id} with qty {qty}")
                        _logger.info(f"Framar Product Groups: Line data keys: {list(line_data.keys())}")
                        
                        # Get the product sub group
                        sub_group = self.env['product.group.sub'].browse(product_sub_group_id)
                        
                        if not sub_group.exists():
                            _logger.warning(f"Framar Product Groups: Sub group {product_sub_group_id} not found, keeping original line")
                            processed_lines.append(line_tuple)
                            continue
                        
                        if not sub_group.component_ids:
                            _logger.warning(f"Framar Product Groups: Sub group {product_sub_group_id} has no components, keeping original line")
                            processed_lines.append(line_tuple)
                            continue
                        
                        # Get original price from the sub group line - this is the UNIT price of the sub-group
                        original_price_unit = line_data.get('price_unit', sub_group.price)
                        sub_group_total_price = original_price_unit * qty  # Total price for this sub group order
                        
                        _logger.info(f"Framar Product Groups: Sub group {product_sub_group_id} - qty: {qty}, price_unit: {original_price_unit}, total: {sub_group_total_price}")
                        
                        # FIRST PASS: Calculate base values for price distribution
                        # Get each component's unit price and calculate proportional distribution
                        component_base_values = {}  # {product_id: base_value}
                        total_base_value = 0.0
                        
                        for component in sub_group.component_ids:
                            component_product = component.product_id
                            if not component_product:
                                continue
                            
                            # Get component's unit price (list_price)
                            component_unit_price = component_product.list_price or 0.0
                            
                            # Base value = unit price × quantity per sub-group
                            component_base_value = component_unit_price * component.quantity
                            component_base_values[component_product.id] = component_base_value
                            total_base_value += component_base_value
                            
                            _logger.info(f"Framar Product Groups: Component {component_product.name} - unit_price: {component_unit_price}, qty_per_subgroup: {component.quantity}, base_value: {component_base_value}")
                        
                        _logger.info(f"Framar Product Groups: Total base value: {total_base_value}, sub-group price: {original_price_unit}")
                        
                        # Expand into components
                        component_index = 0
                        _logger.info(f"Framar Product Groups: Found {len(sub_group.component_ids)} components to expand")
                        
                        for component in sub_group.component_ids:
                            # Create a new line tuple for each component
                            component_line_data = line_data.copy()
                            
                            # CRITICAL: Remove fields that are specific to the sub-group product
                            # These can cause foreign key violations when used with component products
                            fields_to_remove = [
                                'product_sub_group_id',  # Remove so it doesn't get expanded again
                                'product_group_id',  # Remove big group ID
                                'attribute_value_ids',  # Component products have different/no attributes - THIS WAS CAUSING THE ERROR!
                                'custom_attribute_value_ids',  # Custom attributes are product-specific
                                'pack_lot_ids',  # Lot tracking is product-specific
                                'id',  # Remove any existing line ID
                                'uuid',  # Remove UUID - new line needs new UUID
                                'skip_change',  # Reset flags
                                'price_subtotal',  # Remove old subtotal - will be calculated for component
                                'price_subtotal_incl',  # Remove old subtotal incl - will be calculated for component
                                'price_total',  # Remove old total - will be calculated for component
                            ]
                            
                            for field in fields_to_remove:
                                component_line_data.pop(field, None)
                            
                            # Calculate component quantity based on sub group quantity
                            component_qty = component.quantity * qty
                            
                            # Get the component product - handle both direct access and browse
                            component_product = component.product_id
                            if not component_product:
                                _logger.error(f"Framar Product Groups: Component {component.id} has no product_id!")
                                continue
                            
                            component_product_id = component_product.id if hasattr(component_product, 'id') else component_product
                            component_product_name = component_product.name if hasattr(component_product, 'name') else str(component_product)
                            
                            _logger.info(f"Framar Product Groups: Expanding component {component.id}: {component_product_name} (id: {component_product_id}) x {component_qty}")
                            
                            # Get component's own unit price
                            component_unit_price = component_product.list_price or 0.0
                            
                            # Calculate proportional price for this component based on its base value
                            # This ensures the component carries the right portion of the sub-group price
                            component_base_value = component_base_values.get(component_product_id, 0.0)
                            
                            if total_base_value > 0 and component_base_value > 0:
                                # Proportional distribution: component gets its share based on base value
                                component_price_portion = (component_base_value / total_base_value) * sub_group_total_price
                            else:
                                # Fallback: if no base values, use component's own unit price × quantity
                                component_price_portion = component_unit_price * component_qty
                                _logger.warning(f"Framar Product Groups: No base value for {component_product_name}, using component unit price × qty")
                            
                            # Store component's unit price for later use
                            # This ensures the unit price displayed matches the component's actual price
                            
                            _logger.info(f"Framar Product Groups: Component {component_product_name} - unit_price: {component_unit_price}, base_value: {component_base_value}, price_portion: {component_price_portion} (for qty: {component_qty})")
                            
                            # Check if this component product already exists in our map
                            if component_product_id in component_map:
                                # Component already exists - combine quantities and prices
                                existing = component_map[component_product_id]
                                existing['total_qty'] += component_qty
                                existing['total_price'] += component_price_portion
                                
                                # Verify unit price consistency - all occurrences should have the same unit price
                                if 'component_unit_price' in existing:
                                    if abs(existing['component_unit_price'] - component_unit_price) > 0.01:
                                        _logger.warning(f"Framar Product Groups: Component {component_product_name} has different unit prices: {existing['component_unit_price']} vs {component_unit_price}, keeping first")
                                else:
                                    existing['component_unit_price'] = component_unit_price
                                
                                # Keep track of all sub groups this component came from
                                if 'sub_groups' not in existing:
                                    existing['sub_groups'] = []
                                existing['sub_groups'].append(sub_group.name)
                                
                                # Track sub-group unit prices for reference
                                if 'sub_group_unit_prices' not in existing:
                                    existing['sub_group_unit_prices'] = []
                                existing['sub_group_unit_prices'].append({
                                    'sub_group_name': sub_group.name,
                                    'unit_price': original_price_unit,
                                    'qty': qty,
                                    'component_qty': component_qty,
                                    'component_price_portion': component_price_portion,
                                })
                                
                                _logger.info(f"Framar Product Groups: Combined component {component_product_name}: total qty now {existing['total_qty']}, total price now {existing['total_price']}, added {component_price_portion}")
                            else:
                                # First occurrence of this component - add to map
                                component_line_data.update({
                                    'product_id': component_product_id,
                                    'qty': component_qty,
                                    'price_unit': component_unit_price,  # Use component's own unit price
                                    'full_product_name': component_product_name,
                                    'is_component': True,
                                    'product_sub_group_name': sub_group.name,
                                    'product_group_name': sub_group.product_group_id.name if sub_group.product_group_id else '',
                                })
                                component_map[component_product_id] = {
                                    'data': component_line_data,
                                    'total_qty': component_qty,
                                    'total_price': component_price_portion,  # Proportional price for this component
                                    'component_unit_price': component_unit_price,  # Store component's unit price
                                    'sub_groups': [sub_group.name],
                                    'sub_group_unit_prices': [{
                                        'sub_group_name': sub_group.name,
                                        'unit_price': original_price_unit,
                                        'qty': qty,
                                        'component_qty': component_qty,
                                        'component_price_portion': component_price_portion,
                                    }],
                                }
                                _logger.info(f"Framar Product Groups: Added component {component_product_name} x {component_qty}, unit_price: {component_unit_price}, price_portion: {component_price_portion}")
                            component_index += 1
                        
                        _logger.info(f"Framar Product Groups: ✓ Expanded sub group {product_sub_group_id} into {component_index} component entries")
                    else:
                        # Regular product (not a sub group component), keep as is
                        _logger.info(f"Framar Product Groups: Line {line_index} is a regular product, keeping as is")
                        processed_lines.append(line_tuple)
                
                else:
                    # Not a tuple, keep as is (shouldn't happen but be safe)
                    _logger.warning(f"Framar Product Groups: Line {line_index} is not in expected tuple format, keeping as is")
                    processed_lines.append(line_tuple)
            
            # Now convert component_map to lines, combining duplicates
            # Each component uses its own unit price and carries its proportional portion of the sub-group price
            component_items = list(component_map.items())
            
            # Process all components - each uses its own unit price
            total_distributed_price = 0.0
            for component_product_id, component_info in component_items:
                component_data = component_info['data'].copy()
                total_qty = component_info['total_qty']
                total_price = component_info.get('total_price', 0.0)
                component_unit_price = component_info.get('component_unit_price', 0.0)
                
                # Use the component's own unit price (not calculated from distributed price)
                # This ensures: unit_price × qty = correct total for each component
                if component_unit_price > 0:
                    price_unit = component_unit_price
                    calculated_total = price_unit * total_qty
                    
                    # Verify the calculated total matches the distributed price (with small tolerance for rounding)
                    price_diff = abs(calculated_total - total_price)
                    if price_diff > 0.01:
                        _logger.warning(f"Framar Product Groups: Component {component_data.get('full_product_name')} - price mismatch! unit_price × qty = {calculated_total}, but distributed price = {total_price}. Adjusting distributed price.")
                        # Use calculated total to ensure consistency
                        total_price = calculated_total
                    
                    _logger.info(f"Framar Product Groups: Component {component_data.get('full_product_name')} - qty: {total_qty}, unit_price: {price_unit}, total: {total_price}")
                else:
                    # Fallback: calculate from distributed price if unit price not available
                    if total_qty > 0 and total_price > 0:
                        price_unit = total_price / total_qty
                        _logger.warning(f"Framar Product Groups: Component {component_data.get('full_product_name')} - no unit price, calculating from distributed price: {price_unit}")
                    else:
                        price_unit = 0.0
                        _logger.warning(f"Framar Product Groups: Component {component_data.get('full_product_name')} - no price or quantity")
                
                # Calculate subtotal explicitly: price_unit × qty
                # This ensures each component shows the correct subtotal, not the sub-group's total
                calculated_subtotal = round(price_unit * total_qty, 2)
                
                # Ensure discount is 0 for components to avoid price distortion
                discount = 0.0
                
                # CRITICAL: Explicitly set all price-related fields to ensure correct display
                component_data.update({
                    'qty': total_qty,
                    'price_unit': price_unit,
                    'discount': discount,  # Force discount to 0
                    'price_subtotal': calculated_subtotal,  # Explicitly set: unit_price × qty
                    'price_subtotal_incl': calculated_subtotal,  # Same as subtotal if no tax
                    'price_total': calculated_subtotal,  # Total price for this component line
                })
                
                processed_lines.append((0, 0, component_data))
                total_distributed_price += calculated_subtotal
                _logger.info(f"Framar Product Groups: ✓ Final component line: {component_data.get('full_product_name')} x {total_qty} at unit_price {price_unit} = subtotal {calculated_subtotal}")
            
            # Verify total distributed price matches expected
            _logger.info(f"Framar Product Groups: Total distributed price: {total_distributed_price}")
            
            # Update ui_order with processed lines
            _logger.info(f"Framar Product Groups: Processed {len(processed_lines)} lines (original: {len(ui_order.get('lines', []))}, components: {len(component_map)})")
            ui_order = ui_order.copy()
            ui_order['lines'] = processed_lines
        else:
            _logger.warning("Framar Product Groups: No lines found in ui_order")
        
        return super(PosOrder, self)._order_fields(ui_order)


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    product_group_name = fields.Char(string='Big Group Name', help='Name of the big product group (e.g., Kikomando)')
    product_sub_group_name = fields.Char(string='Sub Group Name', help='Name of the sub group for receipt display (e.g., Kikomando 1500)')
    product_sub_group_id = fields.Many2one('product.group.sub', string='Product Sub Group', help='Sub group that this line represents (for expansion into components)')
    is_component = fields.Boolean(string='Is Component', default=False, help='True if this line is a component of a product sub group')
    
    def _is_field_accepted(self, field):
        """Override to allow product_sub_group_id and related fields through"""
        # First check parent implementation
        if super(PosOrderLine, self)._is_field_accepted(field):
            return True
        # Allow our custom fields even if they're not in _fields yet (during export)
        if field in ['product_sub_group_id', 'product_sub_group_name', 'product_group_id', 'product_group_name', 'is_component']:
            return True
        return False

