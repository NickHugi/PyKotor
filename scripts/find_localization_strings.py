#!/usr/bin/env python3
"""Script to find all hardcoded English strings that need localization."""
from __future__ import annotations

import re
from pathlib import Path

def find_strings_in_file(file_path: Path) -> list[tuple[int, str]]:
    """Find hardcoded English strings in a Python file."""
    strings = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Patterns to find strings that are likely user-facing
    patterns = [
        r'QMessageBox\.(?:critical|warning|information|question)\([^,)]+,\s*"([^"]+)"',  # QMessageBox messages
        r'QMessageBox\.(?:critical|warning|information|question)\([^,)]+,\s*\'([^\']+)\'',  # QMessageBox messages
        r'\.setText\(["\']([A-Z][^"\']+)["\']',  # setText calls
        r'\.setTitle\(["\']([A-Z][^"\']+)["\']',  # setTitle calls
        r'\.setWindowTitle\(["\']([A-Z][^"\']+)["\']',  # setWindowTitle calls
        r'\.setToolTip\(["\']([A-Z][^"\']+)["\']',  # setToolTip calls
        r'\.setPlaceholderText\(["\']([A-Z][^"\']+)["\']',  # setPlaceholderText calls
        r'QMessageBox\([^,)]+,\s*"([^"]+)"',  # QMessageBox constructor
        r'QMessageBox\([^,)]+,\s*\'([^\']+)\'',  # QMessageBox constructor
    ]
    
    for i, line in enumerate(lines, 1):
        # Skip comments and docstrings
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        
        # Skip lines that already use tr() or translate()
        if 'tr(' in line or 'translate(' in line:
            continue
        
        for pattern in patterns:
            matches = re.finditer(pattern, line)
            for match in matches:
                text = match.group(1)
                # Filter out very short strings, paths, URLs, technical terms
                if (len(text) > 3 and 
                    not text.startswith('http') and
                    not '\\' in text and
                    not '/' in text and
                    text[0].isupper() and  # Start with capital (likely user-facing)
                    any(c.isalpha() for c in text)):  # Contains letters
                    strings.append((i, text))
    
    return strings

def main():
    """Scan toolset directory for hardcoded strings."""
    toolset_path = Path(__file__).parent.parent / "Tools" / "HolocronToolset" / "src" / "toolset"
    
    all_strings = {}
    
    for py_file in toolset_path.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
        
        strings = find_strings_in_file(py_file)
        if strings:
            rel_path = py_file.relative_to(toolset_path.parent.parent)
            all_strings[str(rel_path)] = strings
    
    # Print results
    for file_path, strings in sorted(all_strings.items()):
        print(f"\n{file_path}:")
        for line_num, text in strings:
            print(f"  Line {line_num}: {text}")

if __name__ == "__main__":
    main()

