# CRITICAL FIX: Module Not Installable

## The Problem
```
WARNING: module pos_product_groups: not installable, skipped
ERROR: Some modules have inconsistent states
```

## Root Cause Found
I found that `auto_install` was set to `True` in the manifest. This has been fixed to `False`.

## Complete Fix Steps

### Step 1: Upload the Fixed Manifest File

The `__manifest__.py` file has been corrected. Make sure you upload the latest version with:
- `'auto_install': False` (not `True`)

### Step 2: Check for Python Errors on Server

Run this command on your Contabo server to see the ACTUAL error:

```bash
# Check for Python import errors
cd /path/to/odoo/addons/pos_product_groups
python3 -c "
import sys
import os
sys.path.insert(0, '/path/to/odoo')
os.environ['ODOO_RC'] = '/etc/odoo/odoo.conf'
try:
    from odoo.addons import pos_product_groups
    print('SUCCESS: Module imports correctly')
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
"
```

### Step 3: Check Odoo Logs for Detailed Error

```bash
# Get the FULL error with traceback
sudo tail -1000 /var/log/odoo/odoo-server.log | grep -A 30 -B 5 "pos_product_groups\|not installable\|ERROR\|Traceback" | tail -100
```

### Step 4: Verify Module Path

Ensure the module is in Odoo's addons path:

```bash
# Find Odoo config
sudo find /etc /opt /home -name "odoo.conf" 2>/dev/null | head -1

# Check addons_path in config
sudo grep "addons_path" /etc/odoo/odoo.conf  # or wherever config is

# Verify module is in one of those paths
ls -la /path/to/odoo/addons/pos_product_groups/__manifest__.py
```

### Step 5: Fix File Permissions

```bash
# Set correct ownership
sudo chown -R odoo:odoo /path/to/odoo/addons/pos_product_groups

# Set correct permissions
sudo chmod -R 755 /path/to/odoo/addons/pos_product_groups
sudo find /path/to/odoo/addons/pos_product_groups -name "*.py" -exec chmod 644 {} \;
```

### Step 6: Verify All Required Files Exist

```bash
cd /path/to/odoo/addons/pos_product_groups

# Check critical files
echo "Checking files..."
[ -f __init__.py ] && echo "✓ __init__.py" || echo "✗ MISSING __init__.py"
[ -f __manifest__.py ] && echo "✓ __manifest__.py" || echo "✗ MISSING __manifest__.py"
[ -f models/__init__.py ] && echo "✓ models/__init__.py" || echo "✗ MISSING models/__init__.py"
[ -f security/ir.model.access.csv ] && echo "✓ security/ir.model.access.csv" || echo "✗ MISSING security file"
[ -f views/product_group_views.xml ] && echo "✓ views/product_group_views.xml" || echo "✗ MISSING view file"
[ -d static/src/js ] && echo "✓ static/src/js directory" || echo "✗ MISSING static directory"
```

### Step 7: Restart Odoo

```bash
sudo systemctl restart odoo
sudo systemctl status odoo
```

### Step 8: Update Apps List and Try Again

1. In Odoo web interface: **Apps** → **Update Apps List**
2. Wait for completion
3. Hard refresh browser: `Ctrl + Shift + R`
4. Search for "POS Product Groups"
5. Click **Install**

## Most Common Issues:

### Issue 1: Python Import Error
**Symptom**: Module fails to import due to syntax error or missing dependency

**Solution**: 
- Run the Python import test above
- Fix any syntax errors found
- Check all `from . import` statements

### Issue 2: Missing Files
**Symptom**: Odoo can't find referenced files in manifest

**Solution**: 
- Verify all files in `data` and `assets` sections exist
- Check file paths are correct

### Issue 3: Wrong Module Path
**Symptom**: Module not in Odoo's addons_path

**Solution**: 
- Check Odoo config for addons_path
- Ensure module is in one of those directories
- Restart Odoo after moving module

### Issue 4: Permission Issues
**Symptom**: Odoo user can't read files

**Solution**: 
- Set ownership: `chown -R odoo:odoo`
- Set permissions: `chmod -R 755`

## If Still Not Working:

Share these outputs:

1. **Python import test result** (from Step 2)
2. **Full error log** (from Step 3)
3. **Module path verification** (from Step 4)
4. **File existence check** (from Step 6)

This will help identify the exact problem!







