# File Permissions Guide for Contabo

## Understanding the Command

```bash
sudo chmod -R 755 /odoo/odoo-server/addons/pos_product_groups
```

### Command Breakdown:

- **`sudo`** = Run as superuser (administrator)
- **`chmod`** = Change file/directory permissions
- **`-R`** = Recursive (apply to all files and subdirectories)
- **`755`** = Permission mode (see explanation below)
- **`/odoo/odoo-server/addons/pos_product_groups`** = Target directory path

### Permission Mode 755 Explained:

```
7   5   5
│   │   │
│   │   └── Others:     read + execute (r-x)
│   └────── Group:      read + execute (r-x)
└────────── Owner:      read + write + execute (rwx)
```

- **7 (Owner)**: Read (4) + Write (2) + Execute (1) = 7 (rwx)
- **5 (Group)**: Read (4) + Execute (1) = 5 (r-x)
- **5 (Others)**: Read (4) + Execute (1) = 5 (r-x)

## Important: Find Your Actual Odoo Path First!

The path `/odoo/odoo-server/addons/` is just an example. Your actual path on Contabo might be different.

### Common Odoo Installation Paths:

1. **Standard Odoo installation:**
   ```bash
   /opt/odoo/odoo-server/addons/
   /usr/lib/python3/dist-packages/odoo/addons/
   ```

2. **Custom installation:**
   ```bash
   /home/odoo/odoo/addons/
   /var/www/odoo/addons/
   /opt/odoo/addons/
   ```

3. **Using Odoo.sh or managed hosting:**
   ```bash
   /home/odoo/src/user/
   ```

### How to Find Your Odoo Addons Path:

**Method 1: Check Odoo Configuration File**
```bash
# Find Odoo config file
sudo find / -name "odoo.conf" 2>/dev/null

# Then check the addons_path setting
sudo grep -i "addons_path" /path/to/odoo.conf
```

**Method 2: Check Running Odoo Process**
```bash
# Find Odoo process
ps aux | grep odoo

# Check the command line arguments for addons path
```

**Method 3: Check Odoo Installation Directory**
```bash
# Common locations
ls -la /opt/odoo/
ls -la /usr/lib/python3/dist-packages/odoo/
ls -la /var/lib/odoo/
```

**Method 4: Check Your Odoo Instance**
- Login to Odoo web interface
- Go to Settings → Technical → Parameters → System Parameters
- Look for `addons_path` or check your server logs

## Correct Command Examples:

Once you know your path, use one of these:

```bash
# Example 1: Standard installation
sudo chmod -R 755 /opt/odoo/odoo-server/addons/pos_product_groups

# Example 2: Custom installation
sudo chmod -R 755 /home/odoo/odoo/addons/pos_product_groups

# Example 3: If in user addons directory
sudo chmod -R 755 /home/odoo/src/user/pos_product_groups
```

## Better Alternative: Use chown First

Before setting permissions, ensure the files are owned by the Odoo user:

```bash
# Find the Odoo user (usually 'odoo' or 'odoo17')
# Check your Odoo process:
ps aux | grep odoo | head -1

# Then set ownership first:
sudo chown -R odoo:odoo /path/to/pos_product_groups

# Then set permissions:
sudo chmod -R 755 /path/to/pos_product_groups
```

## Complete Permission Setup Commands:

```bash
# 1. Navigate to addons directory
cd /path/to/odoo/addons

# 2. Set ownership (replace 'odoo' with your actual Odoo user)
sudo chown -R odoo:odoo pos_product_groups

# 3. Set directory permissions (755 = rwxr-xr-x)
sudo find pos_product_groups -type d -exec chmod 755 {} \;

# 4. Set file permissions (644 = rw-r--r--)
sudo find pos_product_groups -type f -exec chmod 644 {} \;

# OR use the simpler recursive command:
sudo chmod -R 755 pos_product_groups
```

## Quick Verification:

After setting permissions, verify:

```bash
# Check ownership
ls -la /path/to/pos_product_groups

# Check permissions
ls -ld /path/to/pos_product_groups
```

## Security Notes:

- **755 for directories**: Allows Odoo to read and execute (navigate into)
- **644 for files**: Allows Odoo to read but not execute (for Python files, execute isn't needed)
- **Don't use 777**: Too permissive (security risk)
- **Owner should be Odoo user**: Ensures Odoo can read/write files

## Troubleshooting:

### If you get "Permission denied":
```bash
# Check if you're using sudo
sudo chmod -R 755 /path/to/pos_product_groups

# Check if directory exists
ls -la /path/to/odoo/addons/

# Check current permissions
ls -ld /path/to/pos_product_groups
```

### If Odoo can't find the module:
1. Check the path is in `addons_path` in Odoo config
2. Restart Odoo service after setting permissions
3. Update Apps List in Odoo interface

## Example: Complete Setup Process

```bash
# 1. Find your Odoo addons path
grep addons_path /etc/odoo/odoo.conf

# 2. Upload your module (via SFTP/SCP) to that path
# Example: /opt/odoo/addons/pos_product_groups/

# 3. Set ownership
sudo chown -R odoo:odoo /opt/odoo/addons/pos_product_groups

# 4. Set permissions
sudo chmod -R 755 /opt/odoo/addons/pos_product_groups

# 5. Verify
ls -la /opt/odoo/addons/pos_product_groups

# 6. Restart Odoo
sudo systemctl restart odoo
```








