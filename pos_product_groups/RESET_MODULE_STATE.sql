-- SQL script to reset module state in database
-- Run this in PostgreSQL to fix "not installable" error

-- Step 1: Check current module state
SELECT name, state, latest_version, author 
FROM ir_module_module 
WHERE name = 'pos_product_groups';

-- Step 2: Delete the module record (if it exists)
-- This will allow Odoo to recreate it fresh when you "Update Apps List"
DELETE FROM ir_module_module WHERE name = 'pos_product_groups';

-- Step 3: Verify it's deleted
SELECT COUNT(*) FROM ir_module_module WHERE name = 'pos_product_groups';
-- Should return 0

-- Step 4: Also clean up any related records (optional but recommended)
DELETE FROM ir_model_data WHERE module = 'pos_product_groups';

-- Done! Now restart Odoo and update apps list.







