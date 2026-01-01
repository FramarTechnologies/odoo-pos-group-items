/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";

console.log("Framar Product Groups: product_group_popup.js loaded");

export class ProductGroupPriceVariantPopup extends AbstractAwaitablePopup {
    static template = "pos_product_groups.ProductGroupPriceVariantPopup";
    
    static props = {
        productGroup: { type: Object, optional: true },
        zIndex: { type: Number, optional: true },
        cancelKey: { type: String, optional: true },
        confirmKey: { type: String, optional: true },
        id: { type: Number, optional: true },
        resolve: { type: Function, optional: true },
        close: { type: Function, optional: true },
    };
    
    setup() {
        console.log("Framar Product Groups: Popup setup called");
        super.setup(...arguments);
        this.selectedVariant = null;
        
        console.log("Framar Product Groups: Popup props:", this.props);
        console.log("Framar Product Groups: ProductGroup in props:", this.props?.productGroup);
        console.log("Framar Product Groups: Sub groups in props:", this.props?.productGroup?.sub_groups);
        
        this.selectSubGroupHandler = (subGroup) => {
            console.log("Framar Product Groups: Sub group selected:", subGroup);
            this.selectedVariant = subGroup;
            this.confirm();
        };
    }
    
    mounted() {
        console.log("Framar Product Groups: Popup mounted - should be visible now");
        console.log("Framar Product Groups: Sub groups count:", this.subGroups.length);
    }
    
    get productGroup() {
        const pg = this.props?.productGroup || {};
        console.log("Framar Product Groups: productGroup getter:", pg);
        return pg;
    }
    
    get subGroups() {
        const subGroups = this.productGroup?.sub_groups || [];
        console.log("Framar Product Groups: subGroups getter returning:", subGroups.length, "items");
        return subGroups;
    }
    
    format_currency(amount) {
        if (this.env?.utils?.formatCurrency) {
            return this.env.utils.formatCurrency(amount);
        }
        return amount?.toString() || "0";
    }
    
    async getPayload() {
        console.log("Framar Product Groups: getPayload called, returning:", this.selectedVariant);
        return this.selectedVariant;
    }
}

console.log("Framar Product Groups: ProductGroupPriceVariantPopup class exported");
