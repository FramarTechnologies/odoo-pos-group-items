#!/bin/bash
# Debug script to find the exact error preventing module installation
# Run this on your Contabo server

echo "=========================================="
echo "Debugging Module Load Issue"
echo "=========================================="
echo ""

# Find module directory
MODULE_DIR=$(find /opt /usr /var /home -type d -name "pos_product_groups" -path "*/addons/*" 2>/dev/null | head -1)

if [ -z "$MODULE_DIR" ]; then
    echo "ERROR: Module directory not found!"
    echo "Please run: find / -type d -name 'pos_product_groups' 2>/dev/null"
    exit 1
fi

echo "Found module at: $MODULE_DIR"
echo ""

cd "$MODULE_DIR" || exit 1

echo "=== Step 1: Check Manifest File ==="
echo ""

if [ ! -f "__manifest__.py" ]; then
    echo "ERROR: __manifest__.py not found!"
    exit 1
fi

# Try to parse manifest as Python
echo "Checking manifest syntax..."
python3 -c "
import sys
import ast
try:
    with open('__manifest__.py', 'r') as f:
        content = f.read()
    # Remove the encoding line if present
    if content.startswith('# -*- coding:'):
        content = content.split('\\n', 1)[1]
    manifest = ast.literal_eval(content)
    print('✓ Manifest syntax is valid')
    print(f'  - installable: {manifest.get(\"installable\", \"MISSING\")}')
    print(f'  - depends: {manifest.get(\"depends\", [])}')
    if not manifest.get('installable', False):
        print('  ⚠ WARNING: installable is False or missing!')
except Exception as e:
    print(f'✗ ERROR in manifest: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

echo ""
echo "=== Step 2: Check Python File Syntax ==="
echo ""

check_py_file() {
    if python3 -m py_compile "$1" 2>&1; then
        echo "  ✓ $1"
        return 0
    else
        echo "  ✗ SYNTAX ERROR in $1"
        python3 -m py_compile "$1" 2>&1
        return 1
    fi
}

ERRORS=0

check_py_file "__init__.py" || ERRORS=$((ERRORS + 1))
check_py_file "models/__init__.py" || ERRORS=$((ERRORS + 1))
check_py_file "models/product_group.py" || ERRORS=$((ERRORS + 1))
check_py_file "models/product_template.py" || ERRORS=$((ERRORS + 1))
check_py_file "models/pos_order.py" || ERRORS=$((ERRORS + 1))
check_py_file "models/pos_session.py" || ERRORS=$((ERRORS + 1))

echo ""

if [ $ERRORS -gt 0 ]; then
    echo "✗ Found $ERRORS Python syntax error(s). Fix these first!"
    exit 1
fi

echo "=== Step 3: Check Import Errors ==="
echo ""

echo "Testing imports (this might fail if Odoo isn't in Python path):"
echo ""

# Try to import the module
python3 << 'PYTHON_EOF'
import sys
import os

# Try to find Odoo
odoo_paths = [
    '/usr/lib/python3/dist-packages',
    '/opt/odoo',
    '/usr/local/lib/python3*/dist-packages',
    '/var/lib/odoo',
]

for path in odoo_paths:
    if os.path.exists(path):
        sys.path.insert(0, path)

try:
    # Try to import odoo first
    import odoo
    print("✓ Odoo found")
    print(f"  Location: {odoo.__file__}")
except ImportError:
    print("⚠ Odoo not found in Python path")
    print("  This is normal if Odoo is installed differently")
    print("  Checking module files manually instead...")
    
    # Check if we can at least read the files
    module_dir = os.getcwd()
    files_to_check = [
        '__init__.py',
        'models/__init__.py',
        'models/product_group.py',
    ]
    
    all_ok = True
    for file in files_to_check:
        filepath = os.path.join(module_dir, file)
        if os.path.exists(filepath):
            print(f"  ✓ {file} exists")
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                    compile(content, filepath, 'exec')
                print(f"    ✓ {file} compiles")
            except SyntaxError as e:
                print(f"    ✗ {file} has syntax error: {e}")
                all_ok = False
        else:
            print(f"  ✗ {file} missing")
            all_ok = False
    
    if all_ok:
        print("\n✓ All checked files are valid")
    else:
        print("\n✗ Some files have errors")
    
    sys.exit(0)

# If we got here, Odoo is available, try importing the module
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.getcwd())))
    from odoo.addons import pos_product_groups
    print("✓ Module imports successfully!")
except Exception as e:
    print(f"✗ ERROR importing module: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

echo ""
echo "=== Step 4: Check File Permissions ==="
echo ""

if [ -r "__manifest__.py" ]; then
    echo "✓ Manifest is readable"
else
    echo "✗ Manifest is NOT readable"
    echo "  Fix with: chmod 644 __manifest__.py"
fi

if [ -r "__init__.py" ]; then
    echo "✓ __init__.py is readable"
else
    echo "✗ __init__.py is NOT readable"
fi

echo ""
echo "=== Step 5: Check Odoo Logs for Specific Errors ==="
echo ""

LOG_FILE="/var/log/odoo/odoo-server.log"
if [ -f "$LOG_FILE" ]; then
    echo "Searching for errors related to pos_product_groups..."
    echo "---------------------------------------------------"
    # Look for errors, exceptions, or tracebacks
    grep -i "pos_product_groups\|Traceback\|Exception\|Error" "$LOG_FILE" | tail -20 || echo "No specific errors found in recent logs"
else
    echo "⚠ Log file not found at $LOG_FILE"
    echo "  Try: sudo find /var/log -name '*odoo*.log'"
fi

echo ""
echo "=========================================="
echo "Diagnostic Complete"
echo "=========================================="
echo ""
echo "If no errors found above, the issue might be:"
echo "1. Module not in Odoo's addons_path"
echo "2. Odoo cache needs clearing"
echo "3. Module state in database is corrupted"
echo ""
echo "Next steps:"
echo "- Check Odoo config: grep addons_path /etc/odoo/odoo.conf"
echo "- Clear Odoo cache (if exists): rm -rf /tmp/odoo*"
echo "- Check module state in database"







