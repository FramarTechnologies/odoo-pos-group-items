#!/bin/bash
# Diagnostic script to find why module is "not installable"
# Run this on your Contabo server: bash DIAGNOSTIC_SCRIPT.sh

echo "=========================================="
echo "POS Product Groups - Installation Diagnostic"
echo "=========================================="
echo ""

# Get module path (adjust if needed)
MODULE_PATH=$(find /opt /usr /var /home -type d -name "pos_product_groups" -path "*/addons/*" 2>/dev/null | head -1)

if [ -z "$MODULE_PATH" ]; then
    echo "❌ ERROR: Module directory not found!"
    echo "Please specify the full path manually."
    exit 1
fi

echo "✓ Found module at: $MODULE_PATH"
echo ""

# Check file existence
echo "Checking required files..."
echo ""

FILES_OK=1

check_file() {
    if [ -f "$MODULE_PATH/$1" ]; then
        echo "  ✓ $1"
    else
        echo "  ✗ MISSING: $1"
        FILES_OK=0
    fi
}

check_file "__init__.py"
check_file "__manifest__.py"
check_file "models/__init__.py"
check_file "models/product_group.py"
check_file "models/product_template.py"
check_file "models/pos_order.py"
check_file "models/pos_session.py"
check_file "security/ir.model.access.csv"
check_file "views/product_group_views.xml"
check_file "views/product_template_views.xml"

echo ""

if [ $FILES_OK -eq 0 ]; then
    echo "❌ Some files are missing! Fix this first."
    exit 1
fi

# Check Python syntax
echo "Checking Python syntax..."
echo ""

cd "$MODULE_PATH" || exit 1

SYNTAX_OK=1

check_syntax() {
    if python3 -m py_compile "$1" 2>&1; then
        echo "  ✓ $1"
    else
        echo "  ✗ SYNTAX ERROR in $1"
        python3 -m py_compile "$1" 2>&1
        SYNTAX_OK=0
    fi
}

check_syntax "__init__.py"
check_syntax "models/__init__.py"
check_syntax "models/product_group.py"
check_syntax "models/product_template.py"
check_syntax "models/pos_order.py"
check_syntax "models/pos_session.py"

echo ""

if [ $SYNTAX_OK -eq 0 ]; then
    echo "❌ Python syntax errors found! Fix these first."
    exit 1
fi

# Check file permissions
echo "Checking file permissions..."
echo ""

if [ -r "__manifest__.py" ]; then
    echo "  ✓ Manifest file is readable"
else
    echo "  ✗ Manifest file is NOT readable"
    echo "  Fix with: chmod 644 __manifest__.py"
fi

# Check Odoo logs for errors
echo ""
echo "Checking recent Odoo logs for errors..."
echo ""

LOG_FILE="/var/log/odoo/odoo-server.log"
if [ -f "$LOG_FILE" ]; then
    echo "Recent errors related to pos_product_groups:"
    echo "-------------------------------------------"
    tail -500 "$LOG_FILE" | grep -i "pos_product_groups\|not installable\|error\|exception\|traceback" -A 5 -B 2 | tail -50
else
    echo "  ⚠ Log file not found at $LOG_FILE"
    echo "  Try: sudo find /var/log -name '*odoo*.log'"
fi

echo ""
echo "=========================================="
echo "Diagnostic complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Fix any errors found above"
echo "2. Restart Odoo: sudo systemctl restart odoo"
echo "3. In Odoo: Apps → Update Apps List"
echo "4. Try installing again"
echo ""







