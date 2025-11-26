#!/usr/bin/env python3
"""Add HTML comment placeholders to NSS-File-Format.md"""

from pathlib import Path

project_root = Path(__file__).parent.parent
md_path = project_root / "wiki" / "NSS-File-Format.md"

with open(md_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find key sections
toc_start = None
shared_funcs_start = None
tsl_consts_start = None
compilation_start = None

for i, line in enumerate(lines):
    if '## Table of Contents' in line:
        toc_start = i
    elif '## Shared Functions (K1 & TSL)' in line:
        shared_funcs_start = i
    elif '## TSL-Only Constants' in line:
        tsl_consts_start = i
    elif '## Compilation Process' in line:
        compilation_start = i

if toc_start is None:
    print("Error: Could not find '## Table of Contents' section")
    exit(1)
if shared_funcs_start is None:
    print("Error: Could not find '## Shared Functions (K1 & TSL)' section")
    exit(1)
if tsl_consts_start is None:
    print("Error: Could not find '## TSL-Only Constants' section")
    exit(1)
if compilation_start is None:
    print("Error: Could not find '## Compilation Process' section")
    exit(1)

print(f"TOC starts at line {toc_start + 1}")
print(f"Shared Functions (K1 & TSL) at line {shared_funcs_start + 1}")
print(f"TSL-Only Constants at line {tsl_consts_start + 1}")
print(f"Compilation Process at line {compilation_start + 1}")

# Build new content
new_lines = []

# Keep everything up to TOC
new_lines.extend(lines[:toc_start + 1])
new_lines.append('\n')
new_lines.append('<!-- TOC_START -->\n')
new_lines.append('<!-- TOC_END -->\n')
new_lines.append('\n')

# Skip to PyKotor Implementation (find it)
pykotor_impl = None
for i in range(toc_start, shared_funcs_start):
    if '## PyKotor Implementation' in lines[i]:
        pykotor_impl = i
        break

if pykotor_impl:
    # Find the end of PyKotor Implementation section
    pykotor_end = shared_funcs_start
    new_lines.extend(lines[pykotor_impl:pykotor_end])

# Add function sections with placeholders
new_lines.append('\n## Shared Functions (K1 & TSL)\n\n')
new_lines.append('<!-- SHARED_FUNCTIONS_START -->\n')
new_lines.append('<!-- SHARED_FUNCTIONS_END -->\n')
new_lines.append('\n')

new_lines.append('## K1-Only Functions\n\n')
new_lines.append('<!-- K1_ONLY_FUNCTIONS_START -->\n')
new_lines.append('<!-- K1_ONLY_FUNCTIONS_END -->\n')
new_lines.append('\n')

new_lines.append('## TSL-Only Functions\n\n')
new_lines.append('<!-- TSL_ONLY_FUNCTIONS_START -->\n')
new_lines.append('<!-- TSL_ONLY_FUNCTIONS_END -->\n')
new_lines.append('\n')

# Add constant sections with placeholders
new_lines.append('## Shared Constants (K1 & TSL)\n\n')
new_lines.append('<!-- SHARED_CONSTANTS_START -->\n')
new_lines.append('<!-- SHARED_CONSTANTS_END -->\n')
new_lines.append('\n')

new_lines.append('## K1-Only Constants\n\n')
new_lines.append('<!-- K1_ONLY_CONSTANTS_START -->\n')
new_lines.append('<!-- K1_ONLY_CONSTANTS_END -->\n')
new_lines.append('\n')

new_lines.append('## TSL-Only Constants\n\n')
new_lines.append('<!-- TSL_ONLY_CONSTANTS_START -->\n')
new_lines.append('<!-- TSL_ONLY_CONSTANTS_END -->\n')
new_lines.append('\n')

# Add library sections with placeholders
new_lines.append('## KOTOR Library Files\n\n')
new_lines.append('<!-- KOTOR_LIBRARY_START -->\n')
new_lines.append('<!-- KOTOR_LIBRARY_END -->\n')
new_lines.append('\n')

new_lines.append('## TSL Library Files\n\n')
new_lines.append('<!-- TSL_LIBRARY_START -->\n')
new_lines.append('<!-- TSL_LIBRARY_END -->\n')
new_lines.append('\n')

# Check if library sections already exist
kotor_lib_start = None
tsl_lib_start = None
for i in range(tsl_consts_start, compilation_start):
    if '## KOTOR Library Files' in lines[i]:
        kotor_lib_start = i
    elif '## TSL Library Files' in lines[i]:
        tsl_lib_start = i

# If library sections don't exist, add them before Compilation Process
if kotor_lib_start is None or tsl_lib_start is None:
    # Add library sections with placeholders before Compilation Process
    new_lines.append('## KOTOR Library Files\n\n')
    new_lines.append('<!-- KOTOR_LIBRARY_START -->\n')
    new_lines.append('<!-- KOTOR_LIBRARY_END -->\n')
    new_lines.append('\n')
    
    new_lines.append('## TSL Library Files\n\n')
    new_lines.append('<!-- TSL_LIBRARY_START -->\n')
    new_lines.append('<!-- TSL_LIBRARY_END -->\n')
    new_lines.append('\n')

# Add everything from Compilation Process onwards
new_lines.extend(lines[compilation_start:])

# Write new file
with open(md_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"\nPlaceholders added! New file has {len(new_lines)} lines (was {len(lines)} lines)")

