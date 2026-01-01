# POS Product Groups Module

## Overview
This module allows you to create combo products (product groups) in Odoo POS with multiple price variants. Perfect for food businesses selling items like Rolex, Kikomando, etc.

## Features

1. **Create Product Groups**: Define combo products with a name (e.g., "Rolex", "Kikomando")
2. **Multiple Price Variants**: Set different prices for the same product group (e.g., Small: 2000, Large: 3000)
3. **Component Management**: Define which individual products make up each combo
4. **Smart POS Integration**: 
   - When clicking a product group in POS, a dropdown shows all available price variants
   - Receipt shows the combo name (e.g., "Rolex - Large")
   - Backend posts individual components for inventory tracking
5. **Inventory Tracking**: Components are tracked separately, not the combo product

## Installation

1. Copy this module to `server/odoo/addons/pos_product_groups`
2. Update the apps list in Odoo
3. Install "POS Product Groups (Combo Products)" module

## Usage

### Creating a Product Group

1. Go to **Point of Sale → Product Groups**
2. Click **Create**
3. Enter the name (e.g., "Rolex")
4. Go to **Price Variants** tab:
   - Add variants: "Small" (2000), "Large" (3000), etc.
5. Go to **Components** tab:
   - Add components: 1x Chapati, 1x Beans, etc.
6. Save

### Using in POS

1. Open a POS session
2. Click on a product group product
3. A popup will show all available price variants
4. Select the desired variant
5. The product is added to the order
6. On receipt, it shows as "Rolex - Large" (or selected variant)
7. In backend, individual components are posted

## Example: Kikomando Setup

- **Product Group Name**: Kikomando
- **Price Variants**:
  - Regular: 1500
  - Large: 2000
- **Components**:
  - 1x Chapati (1000)
  - 1x Beans (500)

When sold:
- **Receipt shows**: "Kikomando - Regular" for 1500
- **Backend posts**: 1x Chapati + 1x Beans

## Technical Details

- Product groups are linked to product templates
- Components are tracked individually for inventory
- Price variants are stored separately for flexibility
- Order lines store product group info for receipt display
- Backend expands product groups into components on order confirmation

## Support

For issues or questions, contact your system administrator.




















