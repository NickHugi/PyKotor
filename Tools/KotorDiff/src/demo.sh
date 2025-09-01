#!/bin/bash
"""
Demonstration script showing how to use the enhanced KotorDiff with configuration generation.

This script creates sample KOTOR installations and demonstrates various usage scenarios.
"""

# Create sample installations
echo "Creating sample KOTOR installations for demonstration..."

# Create original installation
mkdir -p /tmp/kotor_original
echo "Original KOTOR" > /tmp/kotor_original/chitin.key
echo "Original TLK content" > /tmp/kotor_original/dialog.tlk
mkdir -p /tmp/kotor_original/Override
echo "Original UTC content" > /tmp/kotor_original/Override/test.utc
echo -e "2DA V2.b\n\n\tcol1\tcol2\n0\tvalue1\tvalue2" > /tmp/kotor_original/Override/test.2da

# Create modified installation
mkdir -p /tmp/kotor_modified
echo "Modified KOTOR" > /tmp/kotor_modified/chitin.key
echo "Modified TLK content" > /tmp/kotor_modified/dialog.tlk
mkdir -p /tmp/kotor_modified/Override
echo "Modified UTC content" > /tmp/kotor_modified/Override/test.utc
echo -e "2DA V2.b\n\n\tcol1\tcol2\tcol3\n0\tvalue1\tvalue2\tnewvalue\n1\tnew1\tnew2\tnew3" > /tmp/kotor_modified/Override/test.2da
echo "New UTI content" > /tmp/kotor_modified/Override/newfile.uti

echo "Sample installations created:"
echo "  Original: /tmp/kotor_original"
echo "  Modified: /tmp/kotor_modified"
echo ""

# Set Python path for testing
export PYTHONPATH="/home/runner/work/PyKotor/PyKotor/Libraries/PyKotor/src"
cd /home/runner/work/PyKotor/PyKotor/Tools/KotorDiff/src

echo "=== BASIC DIFF (Original functionality) ==="
python -m kotordiff --path1=/tmp/kotor_original --path2=/tmp/kotor_modified --logging=False

echo ""
echo "=== DIFF WITH CONFIG GENERATION ==="
python -m kotordiff --path1=/tmp/kotor_original --path2=/tmp/kotor_modified --generate-config --config-output=/tmp/changes.ini --logging=False

echo ""
echo "=== GENERATED CHANGES.INI ==="
if [ -f /tmp/changes.ini ]; then
    echo "Generated changes.ini file:"
    echo "--- Content ---"
    cat /tmp/changes.ini
    echo "--- End Content ---"
    echo ""
    echo "File size: $(wc -c < /tmp/changes.ini) bytes"
    echo "Number of lines: $(wc -l < /tmp/changes.ini)"
else
    echo "❌ changes.ini file was not generated"
fi

echo ""
echo "=== HELP OUTPUT ==="
python -m kotordiff --help

echo ""
echo "=== CLEANUP ==="
rm -rf /tmp/kotor_original /tmp/kotor_modified /tmp/changes.ini

echo "✓ Demonstration complete!"