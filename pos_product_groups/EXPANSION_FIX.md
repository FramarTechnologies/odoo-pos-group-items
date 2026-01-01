# Expansion Still Not Working - Debug Steps

## What Should Happen:
- When you sell "Kikomando 1500", session report should show components (Chapati, Beans, etc.)
- Currently: Session report still shows "Kikomando 1500"

## To Debug - Check These Logs:

### 1. Browser Console (F12)
When completing a sale, look for:
- "Framar Product Groups: Orderline exported with product_sub_group_id: X"
- This confirms the frontend is sending the sub group ID

### 2. Server Logs (server/odoo.log)
After completing a sale, search for:
- "Framar Product Groups: _order_fields called"
- "Framar Product Groups: Expanding sub group X"
- "Framar Product Groups: Added component..."

## If You See:
- ✅ Frontend log but ❌ No backend expansion → Field not reaching backend
- ❌ No frontend log → `product_sub_group_id` not being set on orderline
- ✅ Expansion logs but still shows group → Report querying wrong field

## Quick Test:
1. Make a sale with "Kikomando 1500"
2. Complete payment
3. Check server logs immediately after
4. Share what you see in logs

This will tell us exactly where the problem is!









