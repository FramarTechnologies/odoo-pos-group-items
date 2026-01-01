/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

console.log("Framar Product Groups: models.js loaded");

// Verify PosStore exists
console.log("Framar Product Groups: PosStore available?", !!PosStore);
console.log("Framar Product Groups: PosStore.after_load_server_data exists?", typeof PosStore.prototype.after_load_server_data);

// Store original method
const originalAfterLoad = PosStore.prototype.after_load_server_data;

// Apply patch directly to prototype
PosStore.prototype.after_load_server_data = async function() {
    console.log("Framar Product Groups: after_load_server_data PATCH CALLED!");
    const result = await originalAfterLoad.call(this, ...arguments);
    
    console.log("Framar Product Groups: after_load_server_data super call completed");
    
    // Load product groups after server data is loaded
    try {
        console.log("Framar Product Groups: Starting to load product groups...");
        console.log("Framar Product Groups: ORM available?", !!this.orm);
        
        if (!this.orm) {
            console.error("Framar Product Groups: ORM not available!");
            this.product_groups = [];
            return result;
        }
        
        const productGroups = await this.orm.searchRead(
            "product.group",
            [["active", "=", true]],
            ["name", "sub_group_ids", "product_template_id"]
        );
        
        console.log(`Framar Product Groups: Found ${productGroups.length} big groups`, productGroups);
        
        // Load sub groups for each big group
        for (let group of productGroups) {
            try {
                console.log(`Framar Product Groups: Loading sub groups for group ${group.id} (${group.name})...`);
                const subGroups = await this.orm.searchRead(
                    "product.group.sub",
                    [["product_group_id", "=", group.id], ["active", "=", true]],
                    ["name", "price", "sequence", "component_ids", "product_template_id"]
                );
                console.log(`Framar Product Groups: Found ${subGroups.length} sub groups for "${group.name}":`, subGroups);
                
                // Sort by sequence, handling missing sequence values
                group.sub_groups = subGroups.sort((a, b) => {
                    const seqA = a.sequence || 10;
                    const seqB = b.sequence || 10;
                    return seqA - seqB;
                });
                
                // Add parent group info to each sub group for easy access
                group.sub_groups.forEach(subGroup => {
                    subGroup.product_group_id = group.id;
                    subGroup.product_group_name = group.name;
                });
                
                console.log(`Framar Product Groups: Sorted ${group.sub_groups.length} sub groups for "${group.name}"`);
                
                // Load components for each sub group
                for (let subGroup of group.sub_groups) {
                    try {
                        const components = await this.orm.searchRead(
                            "product.group.component",
                            [["sub_group_id", "=", subGroup.id]],
                            ["product_id", "quantity", "sequence"]
                        );
                        subGroup.components = components.sort((a, b) => {
                            const seqA = a.sequence || 10;
                            const seqB = b.sequence || 10;
                            return seqA - seqB;
                        });
                    } catch (componentError) {
                        console.error(`Framar Product Groups: Error loading components for sub group ${subGroup.id}:`, componentError);
                        subGroup.components = [];
                    }
                }
                
                console.log(`Framar Product Groups: Loaded big group "${group.name}" with ${group.sub_groups.length} sub groups`);
                if (group.sub_groups.length > 0) {
                    console.log(`Framar Product Groups: Sub groups for "${group.name}":`, group.sub_groups.map(sg => ({ id: sg.id, name: sg.name, price: sg.price })));
                }
            } catch (subGroupError) {
                console.error(`Framar Product Groups: Error loading sub groups for group ${group.id}:`, subGroupError);
                group.sub_groups = [];
            }
        }
        
        this.product_groups = productGroups || [];
        console.log("Framar Product Groups: Product groups loaded successfully", this.product_groups);
    } catch (error) {
        console.error("Framar Product Groups: Error loading product groups:", error);
        console.error("Framar Product Groups: Error details:", error.message, error.stack);
        this.product_groups = [];
    }
    
    return result;
};

console.log("Framar Product Groups: Patch applied to PosStore.prototype.after_load_server_data");

