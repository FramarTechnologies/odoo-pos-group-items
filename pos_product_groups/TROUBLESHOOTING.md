# Troubleshooting Guide - Common Errors After Upload

## Quick Checklist

Before we troubleshoot, verify:

- [ ] You uploaded ONLY the `pos_product_groups` folder (not the parent directories)
- [ ] The folder structure is correct (see below)
- [ ] Files have correct permissions
- [ ] Odoo can see the module in addons path

## Common Errors & Solutions

### Error 1: "Module not found" or "Apps list empty"

**Problem**: Odoo can't find your module

**Solutions**:

1. **Check module is in correct location:**
   ```bash
   # Find your Odoo addons path
   grep addons_path /etc/odoo/odoo.conf
   # OR
   ps aux | grep odoo | grep addons
   
   # Verify module is there
   ls -la /path/to/addons/pos_product_groups
   ```

2. **Check folder structure is correct:**
   ```
   pos_product_groups/
   ├── __init__.py
   ├── __manifest__.py
   ├── models/
   │   ├── __init__.py
   │   ├── product_group.py
   │   ├── product_template.py
   │   ├── pos_order.py
   │   └── pos_session.py
   ├── security/
   │   └── ir.model.access.csv
   ├── static/
   │   └── src/
   │       ├── js/
   │       └── xml/
   └── views/
       ├── product_group_views.xml
       └── product_template_views.xml
   ```

3. **Update Apps List in Odoo:**
   - Go to Apps menu
   - Click "Update Apps List" button
   - Remove "Apps" filter
   - Search for "POS Product Groups"

4. **Restart Odoo:**
   ```bash
   sudo systemctl restart odoo
   ```

### Error 2: "Invalid module file structure" or "Missing __init__.py"

**Problem**: Module structure is incomplete

**Solutions**:

1. **Verify all required files exist:**
   ```bash
   cd /path/to/addons/pos_product_groups
   ls -la
   
   # Should see:
   # __init__.py
   # __manifest__.py
   ```

2. **Check __init__.py exists and has content:**
   ```bash
   cat __init__.py
   # Should contain: from . import models
   ```

3. **Check __manifest__.py is valid JSON:**
   ```bash
   python3 -m json.tool __manifest__.py
   # Should show JSON without errors
   ```

### Error 3: Permission Denied Errors

**Problem**: Odoo user can't read module files

**Solutions**:

1. **Set correct ownership:**
   ```bash
   # Find Odoo user
   ps aux | grep odoo | head -1
   
   # Set ownership (replace 'odoo' with your Odoo user)
   sudo chown -R odoo:odoo /path/to/addons/pos_product_groups
   ```

2. **Set correct permissions:**
   ```bash
   sudo chmod -R 755 /path/to/addons/pos_product_groups
   ```

3. **Verify:**
   ```bash
   ls -la /path/to/addons/pos_product_groups
   # Files should be readable by Odoo user
   ```

### Error 4: "Syntax Error" or "Invalid Python code"

**Problem**: Python files have errors

**Solutions**:

1. **Check Python syntax:**
   ```bash
   python3 -m py_compile /path/to/addons/pos_product_groups/models/*.py
   ```

2. **Check Odoo logs for specific error:**
   ```bash
   tail -f /var/log/odoo/odoo.log
   # OR
   sudo journalctl -u odoo -f
   ```

3. **Check for Windows line endings (if uploaded from Windows):**
   ```bash
   # Convert if needed
   sudo apt-get install dos2unix
   sudo find /path/to/addons/pos_product_groups -type f -name "*.py" -exec dos2unix {} \;
   ```

### Error 5: "Missing dependency" or "Module not found: point_of_sale"

**Problem**: Dependencies not installed

**Solutions**:

1. **Verify dependencies in manifest:**
   ```bash
   grep -A 2 "depends" /path/to/addons/pos_product_groups/__manifest__.py
   ```

2. **Check Odoo has required modules:**
   - Login to Odoo
   - Go to Apps
   - Search for "Point of Sale" - should be installed
   - Search for "Product" - should be installed

### Error 6: "Invalid manifest file" or JSON errors

**Problem**: __manifest__.py has syntax errors

**Solutions**:

1. **Check manifest syntax:**
   ```bash
   python3 -c "import ast; ast.parse(open('/path/to/addons/pos_product_groups/__manifest__.py').read())"
   ```

2. **Verify it's valid Python dict:**
   ```bash
   python3 -c "exec(open('/path/to/addons/pos_product_groups/__manifest__.py').read())"
   ```

### Error 7: JavaScript/CSS not loading in POS

**Problem**: Assets not found or not loading

**Solutions**:

1. **Verify static files exist:**
   ```bash
   ls -la /path/to/addons/pos_product_groups/static/src/js/
   ls -la /path/to/addons/pos_product_groups/static/src/xml/
   ```

2. **Upgrade module after installation:**
   - Go to Apps
   - Find "POS Product Groups"
   - Click "Upgrade" button

3. **Restart Odoo:**
   ```bash
   sudo systemctl restart odoo
   ```

4. **Clear browser cache:**
   - Hard refresh: Ctrl + Shift + R
   - Or clear all cached files

5. **Check Odoo logs for asset errors:**
   ```bash
   tail -f /var/log/odoo/odoo.log | grep -i "asset\|js\|css"
   ```

### Error 8: Database errors during installation

**Problem**: Database schema creation fails

**Solutions**:

1. **Check database user permissions:**
   ```bash
   # Verify Odoo can connect to database
   sudo -u odoo psql -d your_database_name -c "SELECT version();"
   ```

2. **Backup before installing:**
   ```bash
   # Always backup first!
   pg_dump -U odoo your_database_name > backup_before_install.sql
   ```

3. **Check for existing tables:**
   ```bash
   sudo -u odoo psql -d your_database_name -c "\dt product_group*"
   ```

4. **Try upgrading database:**
   - Go to Apps
   - Find module
   - Click "Upgrade" instead of "Install"

## Getting Error Details

### Check Odoo Logs:

```bash
# Standard log location
tail -f /var/log/odoo/odoo.log

# Systemd service logs
sudo journalctl -u odoo -f

# Check for errors
grep -i error /var/log/odoo/odoo.log | tail -20
```

### Check Browser Console:

1. Open POS in browser
2. Press F12 (Developer Tools)
3. Check Console tab for JavaScript errors
4. Check Network tab for failed file loads

### Enable Debug Mode:

1. Login to Odoo
2. Enable Developer Mode:
   - Go to Settings
   - Activate Developer Mode
3. This shows more detailed error messages

## Verification Steps

After fixing, verify:

```bash
# 1. Module exists
ls -la /path/to/addons/pos_product_groups

# 2. Permissions correct
ls -ld /path/to/addons/pos_product_groups

# 3. Python files readable
python3 -m py_compile /path/to/addons/pos_product_groups/models/*.py

# 4. Odoo can see it
# (Check in Odoo web interface - Apps menu)
```

## Still Having Issues?

Share these details:

1. **Exact error message** (copy/paste)
2. **Odoo log snippet** (last 50 lines)
3. **Module path** on server
4. **Odoo version** (17.0?)
5. **What happens when you try to install** (screenshot or description)








