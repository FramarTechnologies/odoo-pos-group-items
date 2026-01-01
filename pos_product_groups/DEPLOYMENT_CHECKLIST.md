# Deployment Checklist for Contabo Hosting

## Pre-Deployment Preparation

### 1. Clean Up Debug Files (RECOMMENDED)
Before deploying to production, consider removing these debug/documentation files:
- `CHECK_EXPANSION.md`
- `DEBUG_INSTRUCTIONS.md`
- `DEBUG_STEPS.md`
- `EXPANSION_FIX.md`
- `QUICK_FIX.md`
- `SIMPLE_FLOW.md`
- `TESTING_GUIDE.md`
- `README.md` (optional - keep if you want documentation)

These are not needed in production and will just take up space.

### 2. Console Logging (OPTIONAL)
The module contains many `console.log()` statements for debugging. In production:
- **Option A (Recommended)**: Keep them - they're useful for troubleshooting in production
- **Option B**: Wrap them in debug checks or remove (can make troubleshooting harder)

### 3. Verify Manifest Information
Update `__manifest__.py`:
- ✅ Author name
- ✅ Website URL
- ✅ Module version (currently 17.0.1.0.0)
- ✅ License (currently LGPL-3)

### 4. Module Structure
✅ All required files are present:
- `__init__.py`
- `__manifest__.py`
- `models/` directory with all Python files
- `security/ir.model.access.csv`
- `static/src/js/` with all JavaScript files
- `static/src/xml/` with all XML templates
- `views/` with view definitions

## Deployment Steps

### Step 1: Create Module Archive
```bash
# From the addons directory
cd /path/to/odoo/addons
tar -czf pos_product_groups.tar.gz pos_product_groups/
```

Or use ZIP:
```bash
zip -r pos_product_groups.zip pos_product_groups/
```

### Step 2: Upload to Contabo Server
1. Upload the archive to your Contabo server via:
   - SFTP/SCP
   - SSH file transfer
   - Contabo control panel file manager

2. Extract in your Odoo addons directory:
```bash
cd /path/to/odoo/addons
tar -xzf pos_product_groups.tar.gz
# OR
unzip pos_product_groups.zip
```

### Step 3: Set Proper Permissions
```bash
cd /path/to/odoo/addons/pos_product_groups
chown -R odoo:odoo .
find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;
```

### Step 4: Update Odoo App List
1. Restart Odoo server:
```bash
sudo systemctl restart odoo
# OR
sudo service odoo restart
```

2. Update Apps List in Odoo:
   - Login as Administrator
   - Go to Apps menu
   - Click "Update Apps List"
   - Search for "POS Product Groups"

### Step 5: Install Module
1. Enable Developer Mode (if not already enabled)
2. Go to Apps
3. Remove "Apps" filter
4. Search for "POS Product Groups"
5. Click Install

### Step 6: Upgrade Assets (CRITICAL!)
After installing, you MUST upgrade assets to load JavaScript/CSS:
1. Go to Apps → Apps menu
2. Select your module
3. Click "Upgrade"
4. OR restart Odoo server and clear browser cache

### Step 7: Clear Browser Cache
In your browser:
- Chrome/Edge: Ctrl + Shift + Delete → Clear cached images and files
- Firefox: Ctrl + Shift + Delete → Cached Web Content
- OR use Hard Refresh: Ctrl + Shift + R

## Post-Deployment Verification

### ✅ Checklist:
- [ ] Module appears in Apps list
- [ ] Module installs without errors
- [ ] Product Groups menu appears in Inventory
- [ ] Can create a product group
- [ ] Can create sub-groups with prices
- [ ] Can add components to sub-groups
- [ ] POS loads without JavaScript errors (check browser console)
- [ ] Product groups appear in POS
- [ ] Clicking a group shows sub-group popup
- [ ] Selecting a sub-group adds it to order with correct price
- [ ] Changing quantity preserves price
- [ ] Order exports components correctly in backend

## Important Notes

### 1. Static Assets
- JavaScript files are loaded via Odoo's asset bundling system
- After deployment, assets will be bundled automatically
- If changes aren't visible, restart Odoo and clear browser cache

### 2. Database Compatibility
- Module uses standard Odoo ORM
- No special database requirements
- Works with PostgreSQL (standard for Odoo)

### 3. Performance
- Module adds minimal overhead
- Sub-group expansion happens during order creation (server-side)
- No impact on POS frontend performance

### 4. Security
- All security rules are defined in `security/ir.model.access.csv`
- Uses standard Odoo user groups (base.group_user)
- No external API calls or sensitive data

### 5. Backup Before Installation
**IMPORTANT**: Always backup your database before installing new modules:
```bash
# Via Odoo interface: Settings → Database → Backup
# OR via command line:
pg_dump -U odoo -d your_database_name > backup_before_pos_groups.sql
```

## Troubleshooting

### Module doesn't appear in Apps list:
- Check file permissions
- Verify module is in correct addons path
- Check Odoo logs: `/var/log/odoo/odoo.log`
- Restart Odoo service

### JavaScript errors in POS:
- Clear browser cache completely
- Restart Odoo server
- Check browser console for errors
- Verify all JS files are loaded (Network tab)

### Price still changes when quantity changes:
- Check browser console for "Framar Product Groups" messages
- Verify assets were upgraded
- Hard refresh browser (Ctrl + Shift + R)

### Components not expanding in backend:
- Check server logs for "Framar Product Groups" messages
- Verify `product_sub_group_id` is being sent from frontend
- Check database logs for order creation

## Support

If issues occur after deployment:
1. Check Odoo server logs: `/var/log/odoo/odoo.log`
2. Check browser console (F12) for JavaScript errors
3. Verify all files were uploaded correctly
4. Check file permissions

## Version History
- 17.0.1.0.0 - Initial production release








