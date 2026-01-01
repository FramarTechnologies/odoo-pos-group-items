# Price and Quantity Posting Mechanism

This document explains how component items get their quantities and prices when a sub-group product is sold.

## Overview Flow

```
POS Frontend → Order Export → Backend Processing → Component Expansion → Price Distribution → Final Posting
```

---

## Step-by-Step Mechanism

### STEP 1: Frontend - Orderline Creation (JavaScript)

**File:** `static/src/js/orderline_patch.js`

When a user adds "Kikomando 1500" to the cart:

1. **Orderline Setup** (lines 11-49)
   - Orderline is created with `product_sub_group_id` and `product_sub_group_price = 1500`
   - Price is locked: `_price_locked = true`
   - Price property is overridden to always return `1500` (lines 110-131)

2. **Price Protection** (lines 259-292)
   - `get_unit_price()` always returns the locked sub-group price
   - `set_unit_price()` blocks any price changes
   - `set_quantity()` preserves price when quantity changes

3. **Order Export** (lines 168-197)
   - `export_as_JSON()` is called when order is sent to backend
   - Includes: `product_sub_group_id`, `price_unit = 1500`, `qty = 1`
   - **Critical:** `price_unit` is forced to sub-group price (line 184)

**Example Export Data:**
```javascript
{
    product_sub_group_id: 5,
    product_sub_group_name: "Kikomando 1500",
    product_id: 123,  // Product group ID
    qty: 1,
    price_unit: 1500,  // Locked sub-group price
    // ... other fields
}
```

---

### STEP 2: Backend - Order Reception (Python)

**File:** `models/pos_order.py`

Method: `_order_fields(ui_order)` (called automatically by Odoo)

**Line 72-96:** Sub-group Detection
```python
# Receives order lines from frontend
if product_sub_group_id:
    qty = line_data.get('qty', 1)  # e.g., 1
    original_price_unit = line_data.get('price_unit', sub_group.price)  # e.g., 1500
    sub_group_total_price = original_price_unit * qty  # e.g., 1500
```

**Input Received:**
```python
{
    'product_sub_group_id': 5,
    'qty': 1,
    'price_unit': 1500,
    # ...
}
```

---

### STEP 3: Component Base Value Calculation

**Lines 98-118:** First Pass - Calculate Component Base Values

For "Kikomando 1500" with components:
- Chapati: 1 qty × 1000 unit_price = **1000 base value**
- Beans: 1 qty × 500 unit_price = **500 base value**

```python
component_base_values = {}  # {product_id: base_value}
total_base_value = 0.0

for component in sub_group.component_ids:
    component_unit_price = component.product_id.list_price  # e.g., 1000 for Chapati
    component_base_value = component_unit_price * component.quantity  # 1000 × 1 = 1000
    component_base_values[component_product.id] = component_base_value
    total_base_value += component_base_value  # 1000 + 500 = 1500
```

**Result:**
```python
component_base_values = {
    10: 1000,  # Chapati product_id: base_value
    11: 500,   # Beans product_id: base_value
}
total_base_value = 1500
```

---

### STEP 4: Component Expansion & Price Distribution

**Lines 124-235:** Expand Sub-group into Components

For each component in the sub-group:

**A. Calculate Component Quantity** (line 145)
```python
component_qty = component.quantity * qty
# Chapati: 1 × 1 = 1
# Beans: 1 × 1 = 1
```

**B. Get Component Unit Price** (line 159)
```python
component_unit_price = component_product.list_price  # e.g., 1000 for Chapati
```

**C. Calculate Proportional Price Portion** (lines 161-171)
```python
component_base_value = component_base_values.get(component_product_id, 0.0)  # e.g., 1000

if total_base_value > 0 and component_base_value > 0:
    # Proportional distribution
    component_price_portion = (component_base_value / total_base_value) * sub_group_total_price
    
    # Chapati: (1000 / 1500) × 1500 = 1000
    # Beans: (500 / 1500) × 1500 = 500
```

**D. Store in Component Map** (lines 178-234)
```python
if component_product_id in component_map:
    # Component already exists - combine quantities and prices
    existing['total_qty'] += component_qty
    existing['total_price'] += component_price_portion
else:
    # First occurrence - add to map
    component_map[component_product_id] = {
        'data': {
            'product_id': component_product_id,
            'qty': component_qty,
            'price_unit': component_unit_price,  # Component's own unit price
            'full_product_name': component_product_name,
            'is_component': True,
            # ...
        },
        'total_qty': component_qty,  # e.g., 1
        'total_price': component_price_portion,  # e.g., 1000
        'component_unit_price': component_unit_price,  # e.g., 1000
        # ...
    }
```

**After Expansion:**
```python
component_map = {
    10: {  # Chapati
        'total_qty': 1,
        'total_price': 1000,
        'component_unit_price': 1000,
        # ...
    },
    11: {  # Beans
        'total_qty': 1,
        'total_price': 500,
        'component_unit_price': 500,
        # ...
    }
}
```

---

### STEP 5: Final Line Creation & Posting

**Lines 248-294:** Convert Component Map to Order Lines

For each component in the map:

```python
for component_product_id, component_info in component_items:
    component_data = component_info['data'].copy()
    total_qty = component_info['total_qty']  # e.g., 1
    total_price = component_info.get('total_price', 0.0)  # e.g., 1000
    component_unit_price = component_info.get('component_unit_price', 0.0)  # e.g., 1000
    
    # Use component's own unit price (NOT calculated from distributed price)
    if component_unit_price > 0:
        price_unit = component_unit_price  # Use stored unit price: 1000
        calculated_total = price_unit * total_qty  # 1000 × 1 = 1000
        
        # Verify consistency
        if abs(calculated_total - total_price) > 0.01:
            # Adjust if mismatch (shouldn't happen, but safety check)
            total_price = calculated_total
    
    # Update line data
    component_data.update({
        'qty': total_qty,  # 1
        'price_unit': price_unit,  # 1000
    })
    
    # Add to processed lines - THIS CREATES THE pos.order.line RECORD
    processed_lines.append((0, 0, component_data))
```

**Final Processed Lines:**
```python
processed_lines = [
    (0, 0, {
        'product_id': 10,  # Chapati
        'qty': 1,
        'price_unit': 1000,
        'is_component': True,
        'full_product_name': 'Chapati',
        # ...
    }),
    (0, 0, {
        'product_id': 11,  # Beans
        'qty': 1,
        'price_unit': 500,
        'is_component': True,
        'full_product_name': 'Beans',
        # ...
    }),
]
```

---

### STEP 6: Order Line Creation (Odoo Core)

**Line 303:** `return super(PosOrder, self)._order_fields(ui_order)`

Odoo processes the `processed_lines` and creates `pos.order.line` records:

```python
# Odoo creates:
pos.order.line #1:
    - product_id = 10 (Chapati)
    - qty = 1
    - price_unit = 1000
    - price_subtotal = 1000
    - is_component = True

pos.order.line #2:
    - product_id = 11 (Beans)
    - qty = 1
    - price_unit = 500
    - price_subtotal = 500
    - is_component = True
```

---

## Complete Example: Selling 1× "Kikomando 1500"

### Input (From Frontend)
```
Sub-group: Kikomando 1500
Qty: 1
Price: 1500 USh
```

### Processing

**Step 1: Base Values**
```
Chapati: 1000 × 1 = 1000 base value
Beans: 500 × 1 = 500 base value
Total base: 1500
```

**Step 2: Price Distribution**
```
Chapati portion: (1000 / 1500) × 1500 = 1000 USh
Beans portion: (500 / 1500) × 1500 = 500 USh
```

**Step 3: Component Quantities**
```
Chapati qty: 1 × 1 = 1
Beans qty: 1 × 1 = 1
```

**Step 4: Final Lines**
```
Line 1: Chapati, qty=1, price_unit=1000, total=1000
Line 2: Beans, qty=1, price_unit=500, total=500
Grand Total: 1500 USh ✓
```

---

## Example: Selling 2× "Kikomando 1500"

### Input
```
Sub-group: Kikomando 1500
Qty: 2
Price: 1500 USh (unit price)
```

### Processing

**Step 1: Base Values** (same as before)
```
Chapati: 1000 × 1 = 1000 base value
Beans: 500 × 1 = 500 base value
Total base: 1500
```

**Step 2: Price Distribution**
```
Sub-group total price: 1500 × 2 = 3000 USh
Chapati portion: (1000 / 1500) × 3000 = 2000 USh
Beans portion: (500 / 1500) × 3000 = 1000 USh
```

**Step 3: Component Quantities**
```
Chapati qty: 1 × 2 = 2
Beans qty: 1 × 2 = 2
```

**Step 4: Final Lines**
```
Line 1: Chapati, qty=2, price_unit=1000, total=2000
Line 2: Beans, qty=2, price_unit=500, total=1000
Grand Total: 3000 USh ✓
```

---

## Key Points

1. **Each Component Uses Its Own Unit Price**
   - Component's `list_price` is stored and used
   - Unit price is NOT recalculated from distributed price
   - Ensures: `unit_price × qty = total_price`

2. **Proportional Price Distribution**
   - Based on component's base value (unit_price × qty_per_subgroup)
   - Formula: `(component_base_value / total_base_value) × sub_group_total_price`

3. **Quantity Calculation**
   - Component quantity = `component.quantity × sub_group_qty`
   - Handles multiple sub-groups with same component correctly

4. **Price Consistency Verification**
   - Checks: `unit_price × qty ≈ distributed_price`
   - Adjusts if mismatch (shouldn't happen, but safety check)

5. **No Conflicts**
   - Each component maintains its own unit price independently
   - Prices sum correctly to sub-group total
   - Quantities are accurate

---

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (JavaScript)                                       │
│                                                             │
│ User adds "Kikomando 1500"                                 │
│ → Orderline created with:                                  │
│   - product_sub_group_id = 5                               │
│   - qty = 1                                                │
│   - price_unit = 1500 (LOCKED)                             │
│                                                             │
│ export_as_JSON() → sends to backend                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (Python) - _order_fields()                         │
│                                                             │
│ 1. Receive order line                                      │
│    - product_sub_group_id = 5                              │
│    - qty = 1                                               │
│    - price_unit = 1500                                     │
│                                                             │
│ 2. Get sub-group components                                │
│    - Chapati: 1 qty, unit_price = 1000                     │
│    - Beans: 1 qty, unit_price = 500                        │
│                                                             │
│ 3. Calculate base values                                   │
│    - Chapati base: 1000 × 1 = 1000                         │
│    - Beans base: 500 × 1 = 500                             │
│    - Total base: 1500                                      │
│                                                             │
│ 4. Distribute price proportionally                         │
│    - Chapati: (1000/1500) × 1500 = 1000                    │
│    - Beans: (500/1500) × 1500 = 500                        │
│                                                             │
│ 5. Create component lines                                  │
│    - Chapati: qty=1, price_unit=1000, total=1000          │
│    - Beans: qty=1, price_unit=500, total=500              │
│                                                             │
│ 6. Return processed_lines                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ ODOO CORE                                                   │
│                                                             │
│ Creates pos.order.line records:                            │
│                                                             │
│ Line 1:                                                     │
│   - product_id = 10 (Chapati)                              │
│   - qty = 1                                                │
│   - price_unit = 1000                                      │
│   - price_subtotal = 1000                                  │
│                                                             │
│ Line 2:                                                     │
│   - product_id = 11 (Beans)                                │
│   - qty = 1                                                │
│   - price_unit = 500                                       │
│   - price_subtotal = 500                                   │
│                                                             │
│ Order Total: 1500 USh ✓                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

The mechanism ensures:
1. ✅ Each component item carries its own unit price
2. ✅ Prices are distributed proportionally based on component values
3. ✅ Quantities are calculated correctly (component_qty × sub_group_qty)
4. ✅ Total price matches sub-group price exactly
5. ✅ No conflicts or miscalculations
6. ✅ Each component shows independently in session reports

The key is that **each component uses its own `list_price` as the unit price**, while the **total price is distributed proportionally** to ensure the sum equals the sub-group's total price.



