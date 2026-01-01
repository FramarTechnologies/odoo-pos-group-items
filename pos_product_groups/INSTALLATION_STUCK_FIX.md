# Module Installation Stuck - Troubleshooting Guide

## Quick Fixes to Try

### Option 1: Check Server Logs (Most Important!)

SSH into your Contabo server and check Odoo logs:

```bash
# View live logs
tail -f /var/log/odoo/odoo.log

# OR check systemd logs
sudo journalctl -u odoo -f

# OR check recent errors
tail -100 /var/log/odoo/odoo.log | grep -i "error\|exception\|traceback" -A 10
```

Look for:
- Foreign key errors
- SQL errors
- Timeout errors
- Any exceptions

### Option 2: Check If It's Actually Installing

Sometimes it just takes time. Wait 2-3 minutes. If still stuck:

1. **Refresh the browser page** (F5)
2. Check if installation completed

### Option 3: Try Upgrading Instead of Installing

If the module was previously installed:

1. Go to **Apps** menu
2. Remove "Apps" filter
3. Search for "POS Product Groups"
4. Click **"Upgrade"** instead of "Install"

### Option 4: Cancel and Restart

1. Click **"Cancel Install"** button
2. Refresh browser (Ctrl + Shift + R)
3. Try again

### Option 5: Check Database Locks

The installation might be stuck due to database locks:

```bash
# Check for database locks
sudo -u postgres psql -d your_database_name -c "SELECT * FROM pg_locks WHERE NOT granted;"

# Check for long-running queries
sudo -u postgres psql -d your_database_name -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' AND query NOT LIKE '%pg_stat_activity%';"
```

### Option 6: Manual Installation via Database

If web interface is stuck, try installing via command line:

1. **Backup database first!**
   ```bash
   pg_dump -U odoo your_database_name > backup_before_manual_install.sql
   ```

2. **Enable Developer Mode in Odoo** (Settings → Activate Developer Mode)

3. **Try upgrading via shell**:
   ```bash
   # This requires Odoo shell access
   odoo-bin shell -d your_database_name -r odoo -w odoo
   # Then in Python shell:
   # env['ir.module.module'].search([('name', '=', 'pos_product_groups')]).button_immediate_upgrade()
   ```

## Common Causes

### 1. Foreign Key Errors During Installation
If you see errors about foreign keys:
- The module might be trying to create tables with invalid references
- Check if all dependencies are installed
- Verify database integrity

### 2. Missing Dependencies
Check if required modules are installed:
- Point of Sale
- Product

### 3. JavaScript Errors
Check browser console (F12) for JavaScript errors that might prevent UI updates.

### 4. Server Timeout
Large installations can timeout. Increase timeout in Odoo config or wait longer.

### 5. Database Connection Issues
Check if database is accessible and not locked.

## Force Cancel and Retry

If truly stuck:

1. **Cancel the installation** (click "Cancel Install")
2. **Check server logs** for errors
3. **Fix any errors** found in logs
4. **Restart Odoo**:
   ```bash
   sudo systemctl restart odoo
   ```
5. **Clear browser cache** completely
6. **Try installing again**

## Check Installation Status

After canceling, check if module is partially installed:

1. Go to **Apps** menu
2. Search for "POS Product Groups"
3. Check status:
   - **Not Installed** - Can try installing again
   - **Installed** - Should upgrade instead
   - **To Upgrade** - Needs upgrade

## If Module is Partially Installed

If installation started but didn't complete:

1. **Go to Apps → Installed**
2. **Find "POS Product Groups"**
3. **Click "Upgrade"** to complete installation

## Prevention

After fixing, ensure:
- ✅ All dependencies are installed
- ✅ Database is healthy
- ✅ No foreign key violations
- ✅ Server has enough resources

## Still Stuck?

Share these details:

1. **Server log errors** (last 50 lines)
2. **Browser console errors** (F12 → Console tab)
3. **Module status** in Apps menu (Installed? To Upgrade?)
4. **How long** it's been stuck (seconds/minutes)








