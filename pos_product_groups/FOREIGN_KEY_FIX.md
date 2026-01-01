# Foreign Key Violation Fix

## Error
```
psycopg2.errors.ForeignKeyViolation: insert or update on table "pos_order_line_product_template_attribute_value_rel" violates foreign key constraint

DETAIL: Key (product_template_attribute_value_id)=(51) is not present in table "product_template_attribute_value".
```

## Root Cause

When expanding sub-groups into components, we were copying **all fields** from the original line, including:
- `attribute_value_ids` - Product attribute values specific to the sub-group product
- `custom_attribute_value_ids` - Custom attributes
- `pack_lot_ids` - Lot tracking data

When creating component lines, Odoo tries to link these attribute values to the component products, but:
- Component products don't have those attribute values
- The attribute value ID (like 51) doesn't exist for component products
- Database foreign key constraint fails

## Fix Applied

Modified `models/pos_order.py` to **explicitly remove** attribute-related fields when creating component lines:

```python
fields_to_remove = [
    'product_sub_group_id',
    'product_group_id',
    'attribute_value_ids',  # Component products have different/no attributes
    'custom_attribute_value_ids',  # Custom attributes are product-specific
    'pack_lot_ids',  # Lot tracking is product-specific
    'id',  # Remove any existing line ID
    'uuid',  # Remove UUID - new line needs new UUID
    'skip_change',  # Reset flags
]
```

## Deployment

1. Upload the updated file:
   - `models/pos_order.py`

2. Restart Odoo:
   ```bash
   sudo systemctl restart odoo
   ```

3. Test:
   - Create an order with a sub-group item
   - Try to save/pay the order
   - Should no longer get foreign key violation errors

## What This Means

- Component lines are now created cleanly without product-specific fields
- Each component line only has the data it needs
- No more foreign key violations when saving orders
- Inventory tracking still works (components are tracked correctly)








