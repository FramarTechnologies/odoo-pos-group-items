/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ProductGroupPriceVariantPopup } from "./product_group_popup";

console.log("Framar Product Groups: product_group_screen.js loaded");

const originalAddProduct = PosStore.prototype.addProductToCurrentOrder;

PosStore.prototype.addProductToCurrentOrder = async function(product, options = {}) {
    // Convert product ID to product object if needed
    if (Number.isInteger(product)) {
        product = this.db.get_product_by_id(product);
    }
    
    if (!product) {
        return originalAddProduct.call(this, product, options);
    }
    
    // SIMPLE CHECK: Is this a product group?
    if (!product.is_product_group) {
        // NOT a product group - use normal flow
        return originalAddProduct.call(this, product, options);
    }
    
    // STOP HERE - This IS a product group - DO NOT add it normally!
    // We MUST show popup first, then only add if user selects a sub group
    
    // Get product group ID
    let productGroupId = null;
    if (product.product_group_id) {
        productGroupId = Array.isArray(product.product_group_id) 
            ? product.product_group_id[0] 
            : (product.product_group_id.id || product.product_group_id);
    }
    
    if (!productGroupId) {
        console.error("Framar Product Groups: Product group ID not found - cannot show popup");
        // DO NOT add product - just return
        return;
    }
    
    // Find the product group in loaded data
    const productGroup = (this.product_groups || []).find(pg => pg.id === productGroupId);
    
    if (!productGroup) {
        console.error("Framar Product Groups: Product group", productGroupId, "not found in loaded groups");
        // DO NOT add product - just return
        return;
    }
    
    // Check if sub groups exist
    if (!productGroup.sub_groups || productGroup.sub_groups.length === 0) {
        console.error("Framar Product Groups: No sub groups found for", productGroup.name);
        // DO NOT add product - just return
        return;
    }
    
    // FORCE POPUP TO SHOW - This is mandatory for product groups
    try {
        console.log("Framar Product Groups: Showing popup for product group:", productGroup.name);
        console.log("Framar Product Groups: Sub groups to show:", productGroup.sub_groups.length);
        
        const result = await this.env.services.popup.add(ProductGroupPriceVariantPopup, {
                        productGroup: productGroup,
                    });
        
        console.log("Framar Product Groups: Popup result:", result);
        
        // ONLY add product if user confirmed and selected a sub group
        if (result && result.confirmed && result.payload) {
            const selectedSubGroup = result.payload;
            console.log("Framar Product Groups: User selected sub group:", selectedSubGroup.name);
            await this._addSubGroupToOrder(product, selectedSubGroup, options);
            return;
        }
        
        // User cancelled - DO NOT add anything
        console.log("Framar Product Groups: User cancelled popup - not adding product");
                            return;
                    } catch (error) {
        console.error("Framar Product Groups: ERROR showing popup:", error);
        console.error("Framar Product Groups: Error details:", error.message, error.stack);
        // DO NOT fall back to default - product groups should ALWAYS show popup
        // If popup fails, don't add the product
                return;
    }
};

// Helper method to add sub group to order
PosStore.prototype._addSubGroupToOrder = async function(product, subGroup, options = {}) {
        const order = this.get_order() || this.add_new_order();
        
        if (!order) {
            return;
        }
        
    // Use sub group price
    const price = subGroup.price || 0;
    
    // IMPORTANT: Set price_type in options to "manual" BEFORE adding product
    // This prevents Odoo from recalculating the price
    const productOptions = { 
        ...options, 
        price: price,
        price_type: "manual"  // Set price_type to manual to lock the price
    };
    
    console.log("Framar Product Groups: _addSubGroupToOrder - Adding product with price:", price, "price_type: manual");
    
    // add_product is async, so await it
    const line = await order.add_product(product, productOptions);
    
    if (!line) {
        console.error("Framar Product Groups: ERROR - line is null or undefined!");
        this.numberBuffer.reset();
        return;
    }
    
    console.log("Framar Product Groups: _addSubGroupToOrder - line created:", line, "line.price:", line.price, "line.price_type:", line.price_type);
    
    // Prepare sub group data
    const subGroupData = {
        product_group_id: subGroup.product_group_id || null,
        product_group_name: subGroup.product_group_name || null,
        product_sub_group_id: subGroup.id,
        product_sub_group_name: subGroup.name,
        display_name: subGroup.name,
        price: subGroup.price || 0,
    };
    
    // Store sub group info FIRST - try using the patched method, fallback to manual assignment
    if (line.set_product_group_data && typeof line.set_product_group_data === 'function') {
        console.log("Framar Product Groups: Using set_product_group_data method with price:", subGroup.price);
        line.set_product_group_data(subGroupData);
        console.log("Framar Product Groups: After set_product_group_data - price:", line.price, "price_type:", line.price_type, "product_sub_group_price:", line.product_sub_group_price, "locked:", line._price_locked);
    } else {
        // FALLBACK: Manually set all properties if patch method isn't available
        console.warn("Framar Product Groups: set_product_group_data method not available, using manual assignment");
        line.product_group_id = subGroupData.product_group_id;
        line.product_group_name = subGroupData.product_group_name;
        line.product_sub_group_id = subGroupData.product_sub_group_id;
        line.product_sub_group_name = subGroupData.product_sub_group_name;
        line.product_sub_group_price = subGroupData.price;
        line._price_locked = true;
        
        // Update display name
        if (subGroupData.display_name) {
            line.full_product_name = subGroupData.display_name;
        }
        
        console.log("Framar Product Groups: Manually set sub group data - product_sub_group_id:", line.product_sub_group_id, "price:", line.product_sub_group_price);
    }
    
    // Ensure price_type is set to manual (CRITICAL for price locking)
    if (line.price_type !== "manual") {
        console.log("Framar Product Groups: Force setting price_type to manual");
        line.price_type = "manual";
    }
    
    // Ensure price is locked
    if (!line._price_locked) {
        line._price_locked = true;
    }
    
    // Verify price is correct
    const currentPrice = line.get_unit_price ? line.get_unit_price() : line.price;
    if (Math.abs(parseFloat(currentPrice) - parseFloat(price)) > 0.01) {
        console.log("Framar Product Groups: Price mismatch detected! Setting price from", currentPrice, "to", price);
        line.set_unit_price(price);
        // Verify again after setting
        const newPrice = line.get_unit_price ? line.get_unit_price() : line.price;
        console.log("Framar Product Groups: Price after correction:", newPrice);
    } else {
        console.log("Framar Product Groups: ✓ Price is correct:", currentPrice);
    }
    
    // CRITICAL: Ensure sub-group data will be exported (even if patch method wasn't available)
    // Verify the data is set
    console.log("Framar Product Groups: Final check - product_sub_group_id:", line.product_sub_group_id, "price:", line.price, "price_type:", line.price_type);
    
    this.numberBuffer.reset();
};

console.log("Framar Product Groups: Patch applied to PosStore.prototype.addProductToCurrentOrder");
