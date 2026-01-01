# Production Fix - RPC Error Resolution

## Issues Found in Production Logs

1. **ERROR**: `line does not have set_product_group_data method!`
   - The Orderline patch method isn't being recognized
   - **FIX**: Added fallback to manually set properties

2. **RPC_ERROR**: "Failed to send orders" / "Odoo Server Error"
   - Orders failing to save to backend
   - Likely due to missing sub-group data in export

## Changes Made

### 1. Added Fallback in `product_group_screen.js`

If the patched method isn't available, we now manually set all properties:

```javascript
// FALLBACK: Manually set all properties if patch method isn't available
line.product_group_id = subGroupData.product_group_id;
line.product_group_name = subGroupData.product_group_name;
line.product_sub_group_id = subGroupData.product_sub_group_id;
line.product_sub_group_name = subGroupData.product_sub_group_name;
line.product_sub_group_price = subGroupData.price;
line._price_locked = true;
```

This ensures the data is set even if the patch isn't working correctly.

### 2. Enhanced Export Verification

The `export_as_JSON` patch should still work because it checks for the properties directly, not the method.

## Deployment Steps

1. **Upload the updated files:**
   - `static/src/js/product_group_screen.js`

2. **Clear browser cache:**
   - Hard refresh: Ctrl + Shift + R
   - Or clear all cached files

3. **Restart Odoo** (if needed):
   ```bash
   sudo systemctl restart odoo
   ```

4. **Test:**
   - Add a sub-group item to order
   - Check browser console - should see "Manually set sub group data" message
   - Try to save/pay the order
   - Check if RPC errors are gone

## Verification

After deploying, check browser console for:

✅ **Good signs:**
- "Manually set sub group data" message (means fallback is working)
- No "ERROR - line does not have set_product_group_data method" message
- Orders save successfully (no RPC errors)

❌ **Bad signs:**
- Still seeing "ERROR - line does not have set_product_group_data method"
- RPC errors when saving orders
- Orders not saving to backend

## If Issues Persist

1. **Check server logs:**
   ```bash
   tail -100 /var/log/odoo/odoo.log | grep -i "error\|exception" -A 10
   ```

2. **Check browser console:**
   - Look for JavaScript errors
   - Check Network tab for failed requests
   - Check for "export_as_JSON" messages

3. **Verify patch is loading:**
   - Browser console should show: "Framar Product Groups: orderline_patch.js loaded"
   - If not, assets might not be updated

4. **Force asset regeneration:**
   - Upgrade module in Apps menu
   - OR restart Odoo server
   - Clear browser cache completely

## Notes

- The fallback ensures functionality even if patches don't apply correctly
- Manual property assignment works the same as the method
- Export should still work because it checks properties directly
- This is a defensive fix to handle edge cases in production








