# How to Check if Expansion is Working

## Steps to Debug:

1. **Make a sale** with a product group sub group (e.g., "Kikomando 1500")
2. **Check server logs** - Look for:
   - "Framar Product Groups: _order_fields called"
   - "Framar Product Groups: Expanding sub group X"
   - "Framar Product Groups: Added component..."

3. **Check browser console** - Look for:
   - "Framar Product Groups: Orderline exported with product_sub_group_id: X"

4. **If expansion logs appear but session report still shows group:**
   - The expansion is working but maybe the report is showing the wrong field
   - Check if session report uses `full_product_name` or `product_id.name`

5. **If NO expansion logs appear:**
   - `product_sub_group_id` is not being sent from frontend
   - Check if `export_as_JSON()` is including the field

## Expected Behavior:

When you sell "Kikomando 1500":
- Order line should have `product_sub_group_id` set
- Backend should detect it and expand into components
- Session report should show components, not "Kikomando 1500"

## Common Issues:

1. **Field not being exported** - Check `export_as_JSON()` in orderline_patch.js
2. **Expansion not triggering** - Check if `product_sub_group_id` is in line data
3. **Report showing wrong field** - Session report might be using product name instead of component name









