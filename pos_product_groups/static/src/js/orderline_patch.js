/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/store/models";
import { roundDecimals as round_di } from "@web/core/utils/numbers";

console.log("Framar Product Groups: orderline_patch.js loaded");
console.log("Framar Product Groups: Orderline class:", Orderline);

patch(Orderline, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        // Initialize product group data
        this.product_group_id = null;
        this.product_group_name = null;
        this.product_sub_group_id = null;
        this.product_sub_group_name = null;
        this.product_sub_group_price = null;  // Store original sub group price
        this._price_locked = false;  // Flag to prevent price changes
        
        // If price_type is "manual" in options and we have a price, ensure it's preserved
        // This happens before set_quantity is called, so we need to set price_type early
        if (options && options.price_type === "manual" && options.price !== undefined) {
            // Price type will be set by super.setup, but ensure we keep it as manual
            this.price_type = "manual";
            this.product_sub_group_price = options.price;  // Store the price immediately
            this._price_locked = true;  // Lock the price
            console.log("Framar Product Groups: Setup - Set price_type to manual from options, price:", options.price);
        }
        
        // Watch for price changes using a property descriptor
        // This ensures any direct property assignment is intercepted
        if (this._price_locked && this.product_sub_group_price) {
            const self = this;
            Object.defineProperty(this, 'price', {
                get: function() {
                    return self.product_sub_group_price || self._price || 0;
                },
                set: function(value) {
                    if (self._price_locked && self.product_sub_group_price) {
                        console.log("Framar Product Groups: Blocked direct price assignment:", value, "keeping:", self.product_sub_group_price);
                        self._price = self.product_sub_group_price;
                        return;
                    }
                    self._price = value;
                },
                configurable: true
            });
        }
    },
    
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        // Load product group data from JSON
        if (json.product_group_id || json.product_sub_group_id) {
            this.product_group_id = json.product_group_id;
            this.product_group_name = json.product_group_name;
            this.product_sub_group_id = json.product_sub_group_id;
            this.product_sub_group_name = json.product_sub_group_name;
        }
    },
    
    set_product_group_data(data) {
        this.product_group_id = data.product_group_id;
        this.product_group_name = data.product_group_name;
        this.product_sub_group_id = data.product_sub_group_id;
        this.product_sub_group_name = data.product_sub_group_name;
        this.product_sub_group_price = data.price || null;  // Store the sub group price
        
        console.log("Framar Product Groups: set_product_group_data called with:", {
            product_sub_group_id: this.product_sub_group_id,
            product_sub_group_name: this.product_sub_group_name,
            product_group_id: this.product_group_id,
            product_group_name: this.product_group_name,
            price: this.product_sub_group_price
        });
        
        // Update display name for receipt
        if (data.display_name) {
            this.full_product_name = data.display_name;
        }
        
        // IMPORTANT: Set price_type to "manual" to prevent Odoo from recalculating price when quantity changes
        if (this.product_sub_group_id) {
            this.price_type = "manual";
            this._price_locked = true;  // Lock the price
            console.log("Framar Product Groups: Set price_type to 'manual' for sub group to prevent price recalculation");
        }
        
        // Set the price immediately and ensure it's locked
        if (this.product_sub_group_price !== null) {
            const lockedPrice = this.product_sub_group_price;
            
            // Set the price to the sub-group price
            super.set_unit_price.call(this, lockedPrice);
            
            // Store a backup in case the property gets modified
            this._locked_sub_group_price = lockedPrice;
            
            // CRITICAL: Override the price property to always return the locked price
            // This ensures that even if something tries to change it, it will always show the correct price
            const self = this;
            try {
                // Delete the existing price property if it exists as an own property
                if (this.hasOwnProperty('price')) {
                    delete this.price;
                }
                
                // Define a new price property that always returns the locked price
                Object.defineProperty(this, 'price', {
                    get: function() {
                        // If we have a locked sub-group price, ALWAYS return it
                        if (self._price_locked && self._locked_sub_group_price !== null && self._locked_sub_group_price !== undefined) {
                            return self._locked_sub_group_price;
                        }
                        // Fallback: use stored internal price or locked price
                        return self._internal_price !== undefined ? self._internal_price : (self._locked_sub_group_price || lockedPrice);
                    },
                    set: function(value) {
                        // If price is locked, ALWAYS ignore attempts to change it
                        if (self._price_locked && self._locked_sub_group_price !== null && self._locked_sub_group_price !== undefined) {
                            console.log("Framar Product Groups: BLOCKED price property set to", value, "- keeping locked price:", self._locked_sub_group_price);
                            // Don't even store the new value - completely ignore it
                            return;
                        }
                        // Only store if not locked
                        self._internal_price = value;
                    },
                    configurable: true,
                    enumerable: true
                });
                
                // Initialize both internal price and locked price to the sub-group price
                this._internal_price = lockedPrice;
                
                console.log("Framar Product Groups: Price property locked at", lockedPrice, "- getter/setter installed");
            } catch (e) {
                console.warn("Framar Product Groups: Could not override price property:", e);
                // Fallback: just store the price
                this._internal_price = lockedPrice;
            }
        }
    },
    
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        
        // Add product group info for receipt display
        if (this.product_sub_group_id) {
            result.product_sub_group_id = this.product_sub_group_id;
            result.product_sub_group_name = this.product_sub_group_name;
            result.product_group_name = this.product_group_name;
            // Override product name for receipt - show sub group name
            if (this.product_sub_group_name) {
                result.productName = this.product_sub_group_name;
            }
        } else if (this.product_group_id) {
            result.product_group_id = this.product_group_id;
            result.product_group_name = this.product_group_name;
            if (this.product_group_name) {
                result.productName = this.product_group_name;
            }
        }
        
        return result;
    },
    
    export_as_JSON() {
        const result = super.export_as_JSON(...arguments);
        
        console.log("Framar Product Groups: export_as_JSON called. this.product_sub_group_id =", this.product_sub_group_id, "current price_unit:", result.price_unit);
        
        // ALWAYS include product group data when exporting order - even if null/undefined
        // This ensures the backend can detect and expand sub groups
        result.product_sub_group_id = this.product_sub_group_id || null;
        result.product_sub_group_name = this.product_sub_group_name || null;
        result.product_group_id = this.product_group_id || null;
        result.product_group_name = this.product_group_name || null;
        result.is_component = this.is_component || false;
        
        // CRITICAL: If this is a sub group item, ALWAYS use the original sub group price as price_unit
        // This ensures the backend can match it correctly, even if quantity changed
        if (this.product_sub_group_id && this.product_sub_group_price !== null && this.product_sub_group_price !== undefined) {
            result.price_unit = this.product_sub_group_price;  // Force unit price to be the sub group price
            console.log("Framar Product Groups: ✓ Forced price_unit to sub group price:", this.product_sub_group_price, "(was:", result.price_unit, ")");
            console.log("Framar Product Groups: ✓ Orderline exported with product_sub_group_id:", this.product_sub_group_id, "price_unit:", result.price_unit);
        } else if (this.product_sub_group_id) {
            console.log("Framar Product Groups: ✓ Orderline exported with product_sub_group_id:", this.product_sub_group_id, "but no stored price!");
            console.log("Framar Product Groups: Export result keys:", Object.keys(result));
        } else {
            console.log("Framar Product Groups: ⚠ Orderline exported WITHOUT product_sub_group_id");
            console.log("Framar Product Groups: this.product_sub_group_id:", this.product_sub_group_id);
            console.log("Framar Product Groups: this keys:", Object.keys(this).filter(k => k.includes('group')));
        }
        
        return result;
    },
    
    // Store original sub group price to preserve it when quantity changes
    // CRITICAL: When quantity changes, the unit price MUST NEVER change - only the total should change
    set_quantity(newQty, keep_price) {
        console.log("Framar Product Groups: set_quantity called - qty:", newQty, "keep_price:", keep_price, "product_sub_group_id:", this.product_sub_group_id, "current price:", this.price);
        
        // If this line has a sub group, preserve the price and prevent any recalculation
        const preservePrice = this.product_sub_group_price;
        
        if (this.product_sub_group_id && preservePrice !== null && preservePrice !== undefined) {
            // Store the locked price
            this._price_locked = true;
            this.price_type = "manual";
            console.log("Framar Product Groups: Sub group detected - locking price at:", preservePrice);
            
            // Store current internal price (might be different from what we display)
            const originalInternalPrice = this.price;
            
            // Call super with keep_price to prevent price recalculation
            const result = super.set_quantity(newQty, "keep_price");
            
            // IMMEDIATELY restore the price after quantity change
            // This ensures the internal price stays at the sub-group price
            this.price_type = "manual";
            this._price_locked = true;
            
            // Force the internal price to be the sub-group price
            // Even though get_unit_price() will override the display, we need the internal price correct too
            if (Math.abs(parseFloat(this.price) - parseFloat(preservePrice)) > 0.01) {
                console.log("Framar Product Groups: Internal price changed from", this.price, "to", preservePrice, "- restoring");
                super.set_unit_price.call(this, preservePrice);
            }
            
            // Set up monitoring to catch any delayed price changes
            const self = this;
            const checkAndRestore = () => {
                if (self.product_sub_group_id && Math.abs(parseFloat(self.price) - parseFloat(preservePrice)) > 0.01) {
                    console.log("Framar Product Groups: [Monitor] Price changed to", self.price, "- restoring to", preservePrice);
                    self.price_type = "manual";
                    self._price_locked = true;
                    super.set_unit_price.call(self, preservePrice);
                }
            };
            
            // Check immediately after current stack
            Promise.resolve().then(checkAndRestore);
            
            // Check after a short delay
            setTimeout(checkAndRestore, 50);
            setTimeout(checkAndRestore, 200);
            
            console.log("Framar Product Groups: Quantity changed to", newQty, "- price locked at", preservePrice);
            return result;
        }
        
        // For regular products, call super normally
        return super.set_quantity(...arguments);
    },
    
    // Override get_unit_price to ALWAYS return the sub-group price for locked items
    // This ensures the price displayed and exported is ALWAYS the sub-group price
    get_unit_price() {
        // If this is a sub-group item with a locked price, ALWAYS return that price
        if (this.product_sub_group_id && this.product_sub_group_price !== null && this.product_sub_group_price !== undefined) {
            const digits = this.pos.dp["Product Price"];
            const lockedPrice = parseFloat(round_di(this.product_sub_group_price || 0, digits).toFixed(digits));
            console.log("Framar Product Groups: get_unit_price - returning locked sub-group price:", lockedPrice, "(internal price is:", this.price, ")");
            return lockedPrice;
        }
        
        // For regular products, use the normal calculation
        return super.get_unit_price(...arguments);
    },
    
    // Also override set_unit_price to prevent price changes for sub groups
    set_unit_price(price) {
        console.log("Framar Product Groups: set_unit_price called - new price:", price, "product_sub_group_id:", this.product_sub_group_id, "stored price:", this.product_sub_group_price);
        
        // If this line has a stored sub group price, always preserve it
        if (this.product_sub_group_price !== null && this.product_sub_group_price !== undefined && this.product_sub_group_id) {
            // Block ANY price changes that don't match the sub group price
            // This is a critical safety net - no exceptions!
            if (Math.abs(parseFloat(price) - parseFloat(this.product_sub_group_price)) > 0.01) {
                console.log("Framar Product Groups: BLOCKED price change from", this.price, "to", price, "- forcing back to sub group price:", this.product_sub_group_price);
                // Force price_type to manual first
                this.price_type = "manual";
                this._price_locked = true;
                // Then set the correct price (even though get_unit_price will override it)
                return super.set_unit_price.call(this, this.product_sub_group_price);
            }
        }
        
        // For regular products, allow price change
        return super.set_unit_price.call(this, price);
    },
    
});




