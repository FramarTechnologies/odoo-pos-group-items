# POS Product Groups - Testing Guide

## Current Status
✅ All modules are loading correctly
✅ Patches are being applied (methods exist)
⚠️ Patched methods need to be called to verify they work

## What You Should See in Console

### When POS Loads:
```
Framar Product Groups: Main module file loaded
Framar Product Groups: models.js loaded
Framar Product Groups: PosStore available? true
Framar Product Groups: PosStore.after_load_server_data exists? function
Framar Product Groups: after_load_server_data PATCH CALLED!  ← This should appear when opening a NEW POS session
Framar Product Groups: Found X product groups  ← Should show number of groups
```

### When Clicking a Product:
```
Framar Product Groups: addProductToCurrentOrder PATCH CALLED!  ← Should appear when clicking ANY product
Framar Product Groups: addProductToCurrentOrder called {...}  ← Product details
```

### If Product is a Product Group:
```
Framar Product Groups: Found product group: {...}
Framar Product Groups: Showing price variant popup with X variants
```

## Testing Steps

### Step 1: Verify Product Group Setup
1. Go to: **Point of Sale → Product Groups**
2. Create a product group (e.g., "Rolex")
3. Add at least ONE price variant (e.g., "Small: 2000")
4. Add at least ONE component (e.g., "1 Chapati")
5. Save

### Step 2: Verify Product is Created
1. Go to: **Point of Sale → Products**
2. Find your product group product (should have same name as group)
3. Edit it
4. Verify:
   - ✅ "Is Product Group" checkbox is checked
   - ✅ "Product Group" field shows your group name
5. Save

### Step 3: Test in POS (IMPORTANT - Open NEW Session)
1. **Close any existing POS sessions**
2. Open browser console (F12)
3. **Open a NEW POS session** (this triggers `after_load_server_data`)
4. Look for: "Framar Product Groups: after_load_server_data PATCH CALLED!"
5. Look for: "Framar Product Groups: Found X product groups"

### Step 4: Click a Product
1. In POS, click on ANY product (regular or product group)
2. Look for: "Framar Product Groups: addProductToCurrentOrder PATCH CALLED!"
3. Check the product details in the log

### Step 5: Click a Product Group Product
1. Click on your product group product (e.g., "Rolex")
2. You should see:
   - "Framar Product Groups: addProductToCurrentOrder PATCH CALLED!"
   - "Framar Product Groups: Found product group: {...}"
   - "Framar Product Groups: Showing price variant popup with X variants"
   - **A popup should appear** showing price variants

### Step 6: Select Price Variant
1. Click on a price variant in the popup
2. Product should be added to order with selected price
3. Check order line - should show product group name

### Step 7: Complete Sale
1. Add payment and complete sale
2. Check receipt - should show product group name
3. Check backend order - should show individual components
4. Check session report - should show components, not group

## Troubleshooting

### If "after_load_server_data PATCH CALLED!" doesn't appear:
- ✅ This is NORMAL if you already had a POS session open
- ✅ Close POS and open a NEW session
- ✅ The method is only called when POS initializes

### If "addProductToCurrentOrder PATCH CALLED!" doesn't appear:
- ❌ This means the patch isn't working
- Check browser console for JavaScript errors
- Try: Developer Mode → Settings → Technical → Assets → Regenerate Assets
- Restart Odoo server

### If popup doesn't appear when clicking product group:
- Check console for: "Framar Product Groups: Found product group"
- Verify product group has price variants
- Check: "Framar Product Groups: product_groups_available: X" (should be > 0)

### If product groups show as 0:
- Verify product groups are created in backend
- Check: "Framar Product Groups: Found X product groups" in console
- If 0, check backend: Point of Sale → Product Groups

## Expected Console Output (Full Flow)

```
Framar Product Groups: Main module file loaded
Framar Product Groups: models.js loaded
Framar Product Groups: PosStore available? true
Framar Product Groups: PosStore.after_load_server_data exists? function
Framar Product Groups: after_load_server_data PATCH CALLED!
Framar Product Groups: Starting to load product groups...
Framar Product Groups: ORM available? true
Framar Product Groups: Found 1 product groups
Framar Product Groups: Loaded group "Rolex" with 2 variants and 2 components
Framar Product Groups: Product groups loaded successfully

[User clicks product]
Framar Product Groups: addProductToCurrentOrder PATCH CALLED!
Framar Product Groups: addProductToCurrentOrder called {
  product: "Rolex",
  isProductGroup: true,
  productGroupId: 1,
  product_groups_available: 1
}
Framar Product Groups: Found product group: {id: 1, name: "Rolex", ...}
Framar Product Groups: Showing price variant popup with 2 variants
Framar Product Groups: Popup result: {confirmed: true, payload: {...}}
```

## Next Steps After Testing

1. Share console logs when:
   - Opening a NEW POS session
   - Clicking a product (any product)
   - Clicking a product group product

2. Share backend verification:
   - Product group exists
   - Product is marked as product group
   - Product has price variants and components

3. Share results:
   - Does popup appear?
   - Does receipt show group name?
   - Does backend show components?
















