/** @odoo-module **/

console.log("Framar Product Groups: Main module file loaded - ALL JS FILES SHOULD LOAD AFTER THIS");

// Import PosStore to ensure it's available when patches are applied
import { PosStore } from "@point_of_sale/app/store/pos_store";
console.log("Framar Product Groups: PosStore imported in main.js:", !!PosStore);


