#!/usr/bin/env python3
"""
Script to automatically update NSS-File-Format.md with functions and constants from scriptdefs.py.

Uses HTML comment placeholders to replace entire sections:
- <!-- SHARED_FUNCTIONS_START --> ... <!-- SHARED_FUNCTIONS_END -->
- <!-- K1_ONLY_FUNCTIONS_START --> ... <!-- K1_ONLY_FUNCTIONS_END -->
- <!-- TSL_ONLY_FUNCTIONS_START --> ... <!-- TSL_ONLY_FUNCTIONS_END -->
- <!-- SHARED_CONSTANTS_START --> ... <!-- SHARED_CONSTANTS_END -->
- <!-- K1_ONLY_CONSTANTS_START --> ... <!-- K1_ONLY_CONSTANTS_END -->
- <!-- TSL_ONLY_CONSTANTS_START --> ... <!-- TSL_ONLY_CONSTANTS_END -->
- <!-- TOC_START --> ... <!-- TOC_END -->
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "Libraries" / "PyKotor" / "src"))

try:
    from pykotor.common.script import DataType, ScriptConstant, ScriptFunction  # type: ignore[import]
    from pykotor.common import scriptdefs  # type: ignore[import]
except ImportError as e:
    print(f"Error importing PyKotor modules: {e}")
    print("Make sure you're running from the project root and dependencies are installed.")
    sys.exit(1)


def extract_routine_number(description: str) -> int | None:
    """Extract routine number from function description."""
    match = re.search(r"//\s*(\d+)[:.]", description)
    if match:
        return int(match.group(1))
    return None


def categorize_function(func: ScriptFunction) -> str:
    """Categorize a function into a section based on its name and description."""
    name_lower = func.name.lower()
    
    # Party management
    if any(x in name_lower for x in ['party', 'switchplayer', 'addavailable']):
        return "Party Management"
    
    # Global variables
    if any(x in name_lower for x in ['global', 'getglobal', 'setglobal']):
        return "Global Variables"
    
    # Player character
    if any(x in name_lower for x in ['getispc', 'getpcspeaker', 'player']):
        return "Player Character Functions"
    
    # Alignment
    if any(x in name_lower for x in ['alignment', 'align']):
        return "Alignment System"
    
    # Class
    if any(x in name_lower for x in ['class', 'getclass', 'setclass']):
        return "Class System"
    
    # Effects
    if any(x in name_lower for x in ['effect', 'applyeffect', 'geteffect', 'removeeffect']):
        return "Effects System"
    
    # Item properties
    if any(x in name_lower for x in ['itemproperty', 'createitemproperty', 'getitemproperty']):
        return "Item Properties"
    
    # Actions
    if name_lower.startswith('action'):
        return "Actions"
    
    # Skills and feats
    if any(x in name_lower for x in ['skill', 'feat', 'getskill', 'gethasfeat']):
        return "Skills and Feats"
    
    # Abilities and stats
    if any(x in name_lower for x in ['ability', 'getability', 'getstat']):
        return "Abilities and Stats"
    
    # Object query
    if any(x in name_lower for x in ['getobject', 'createobject', 'destroyobject', 'getnearest']):
        return "Object Query and Manipulation"
    
    # Item management
    if any(x in name_lower for x in ['item', 'createitem', 'getitem', 'giveitem', 'takeitem']):
        return "Item Management"
    
    # Local variables
    if any(x in name_lower for x in ['local', 'getlocal', 'setlocal']):
        return "Local Variables"
    
    # Module and area
    if any(x in name_lower for x in ['module', 'area', 'getarea', 'getmodule']):
        return "Module and Area Functions"
    
    # Combat
    if any(x in name_lower for x in ['combat', 'attack', 'attacker', 'killer']):
        return "Combat Functions"
    
    # Dialog
    if any(x in name_lower for x in ['conversation', 'dialog', 'bark', 'speak']):
        return "Dialog and Conversation Functions"
    
    # Sound
    if any(x in name_lower for x in ['sound', 'music', 'ambient', 'play']):
        return "Sound and Music Functions"
    
    # Default
    return "Other Functions"


def categorize_constant(const: ScriptConstant) -> str:
    """Categorize a constant into a section based on its name."""
    name_lower = const.name.lower()
    
    # Planet
    if name_lower.startswith('planet_'):
        return "Planet Constants"
    
    # NPC
    if name_lower.startswith('npc_'):
        return "NPC Constants"
    
    # Alignment
    if 'alignment' in name_lower:
        return "Alignment Constants"
    
    # Class type
    if 'class_type' in name_lower:
        return "Class Type Constants"
    
    # Object type
    if 'object_type' in name_lower:
        return "Object Type Constants"
    
    # Ability
    if name_lower.startswith('ability_'):
        return "Ability Constants"
    
    # VFX
    if name_lower.startswith('vfx_'):
        return "Visual Effects (VFX)"
    
    # Inventory
    if 'inventory' in name_lower:
        return "Inventory Constants"
    
    # Default
    return "Other Constants"


def title_to_anchor(title: str) -> str:
    """Convert a markdown title to an anchor link."""
    anchor = title.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'[-\s]+', '-', anchor)
    return anchor.strip('-')


def format_function_markdown(func: ScriptFunction, routine_num: int | None) -> str:
    """Format a function as markdown."""
    routine_str = f" - Routine {routine_num}" if routine_num else ""
    
    # Extract description
    desc_lines = []
    routine_num_line = None
    if func.description:
        for line in func.description.split('\n'):
            line = line.strip()
            if line.startswith('//'):
                line = line[2:].strip()
                if re.match(r'^\d+\.\s*\w+$', line):
                    routine_num_line = f"`{line}`"
                elif re.match(r'^\d+[:.]', line):
                    match = re.match(r'^(\d+)[:.]\s*(.*)$', line)
                    if match:
                        num, desc = match.groups()
                        if not routine_num_line:
                            routine_num_line = f"`{num}. {func.name}`"
                        if desc:
                            desc_lines.append(desc)
                elif line:
                    desc_lines.append(line)
    
    if routine_num is not None and not routine_num_line:
        routine_num_line = f"`{routine_num}. {func.name}`"
    
    # Build parameter list
    param_names = ', '.join([p.name for p in func.params])
    
    # Build markdown with anchor and header
    anchor = title_to_anchor(func.name)
    md = f"<a id=\"{anchor}\"></a>\n#### `{func.name}({param_names})`{routine_str}\n\n"
    
    if routine_num_line:
        md += f"- {routine_num_line}\n"
    
    if desc_lines:
        for line in desc_lines[:5]:
            if line:
                md += f"- {line}\n"
    
    if func.params:
        if desc_lines or routine_num_line:
            md += "\n"
        for param in func.params:
            default_str = f" (default: `{param.default}`)" if param.default is not None else ""
            md += f"- `{param.name}`: {param.datatype.value}{default_str}\n"
    
    return md + "\n"


def format_constant_markdown(const: ScriptConstant) -> str:
    """Format a constant as markdown."""
    value_str = str(const.value)
    if const.datatype == DataType.STRING:
        value_str = f'"{value_str}"'
    anchor = title_to_anchor(const.name)
    description = const.name.replace('_', ' ').title()
    return f"<a id=\"{anchor}\"></a>\n#### `{const.name}`\n\n({value_str}): {description}\n\n"


def generate_toc_entry(level: int, title: str, is_item: bool = False) -> str:
    """Generate a TOC entry."""
    anchor = title_to_anchor(title)
    if is_item:
        indent = '      '  # 6 spaces for items under subsections
        return f"{indent}- [`{title}`](#{anchor})"
    else:
        indent = '  ' * (level - 2)  # Level 2 = no indent, Level 3 = 2 spaces, Level 4 = 4 spaces
        return f"{indent}- [{title}](#{anchor})"


def build_section_content(items_by_category: dict, format_func, item_type: str) -> tuple[str, list[tuple[str, str]]]:
    """Build content for a section and return (content, toc_entries)."""
    content_parts = []
    toc_entries = []
    
    # Sort categories alphabetically
    for category in sorted(items_by_category.keys()):
        items = items_by_category[category]
        if not items:
            continue
        
        # Add category header
        category_anchor = title_to_anchor(category)
        content_parts.append(f"### {category}\n\n")
        toc_entries.append((category, False))
        
        # Sort items alphabetically
        items_sorted = sorted(items, key=lambda x: x.name.lower())
        
        # Add items
        for item in items_sorted:
            if item_type == "function":
                routine_num = extract_routine_number(item.description or item.raw)
                item_md = format_func(item, routine_num)
            else:
                item_md = format_func(item)
            content_parts.append(item_md)
            toc_entries.append((item.name, True))
    
    return ''.join(content_parts), toc_entries


def main():
    """Main function to update NSS-File-Format.md."""
    project_root = Path(__file__).parent.parent
    md_path = project_root / "wiki" / "NSS-File-Format.md"
    
    if not md_path.exists():
        print(f"Error: {md_path} not found")
        return 1
    
    # Read existing markdown
    print("Reading existing markdown...")
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Get all functions and constants
    print("Extracting functions and constants from scriptdefs.py...")
    k1_functions = scriptdefs.KOTOR_FUNCTIONS
    k1_constants = scriptdefs.KOTOR_CONSTANTS
    tsl_functions = scriptdefs.TSL_FUNCTIONS
    tsl_constants = scriptdefs.TSL_CONSTANTS
    
    print(f"K1: {len(k1_functions)} functions, {len(k1_constants)} constants")
    print(f"TSL: {len(tsl_functions)} functions, {len(tsl_constants)} constants")
    
    # Create sets for comparison
    k1_func_names = {f.name for f in k1_functions}
    tsl_func_names = {f.name for f in tsl_functions}
    k1_const_names = {c.name for c in k1_constants}
    tsl_const_names = {c.name for c in tsl_constants}
    
    # Categorize by game
    print("\nCategorizing items by game...")
    k1_only_funcs = defaultdict(list)
    tsl_only_funcs = defaultdict(list)
    shared_funcs = defaultdict(list)
    
    for func in k1_functions:
        category = categorize_function(func)
        if func.name in tsl_func_names:
            shared_funcs[category].append(func)
        else:
            k1_only_funcs[category].append(func)
    
    for func in tsl_functions:
        if func.name not in k1_func_names:
            category = categorize_function(func)
            tsl_only_funcs[category].append(func)
    
    k1_only_consts = defaultdict(list)
    tsl_only_consts = defaultdict(list)
    shared_consts = defaultdict(list)
    
    for const in k1_constants:
        category = categorize_constant(const)
        if const.name in tsl_const_names:
            shared_consts[category].append(const)
        else:
            k1_only_consts[category].append(const)
    
    for const in tsl_constants:
        if const.name not in k1_const_names:
            category = categorize_constant(const)
            tsl_only_consts[category].append(const)
    
    print(f"Shared: {sum(len(v) for v in shared_funcs.values())} functions, {sum(len(v) for v in shared_consts.values())} constants")
    print(f"K1-only: {sum(len(v) for v in k1_only_funcs.values())} functions, {sum(len(v) for v in k1_only_consts.values())} constants")
    print(f"TSL-only: {sum(len(v) for v in tsl_only_funcs.values())} functions, {sum(len(v) for v in tsl_only_consts.values())} constants")
    
    # Build content for each section
    print("\nBuilding section content...")
    toc_entries_by_section = {}
    
    shared_func_content, toc_entries_by_section['Shared Functions (K1 & TSL)'] = build_section_content(shared_funcs, format_function_markdown, "function")
    k1_func_content, toc_entries_by_section['K1-Only Functions'] = build_section_content(k1_only_funcs, format_function_markdown, "function")
    tsl_func_content, toc_entries_by_section['TSL-Only Functions'] = build_section_content(tsl_only_funcs, format_function_markdown, "function")
    
    shared_const_content, toc_entries_by_section['Shared Constants (K1 & TSL)'] = build_section_content(shared_consts, format_constant_markdown, "constant")
    k1_const_content, toc_entries_by_section['K1-Only Constants'] = build_section_content(k1_only_consts, format_constant_markdown, "constant")
    tsl_const_content, toc_entries_by_section['TSL-Only Constants'] = build_section_content(tsl_only_consts, format_constant_markdown, "constant")
    
    # Build TOC
    print("Building Table of Contents...")
    toc_lines = []
    
    # Add major sections
    for section_name in ['Shared Functions (K1 & TSL)', 'K1-Only Functions', 'TSL-Only Functions',
                          'Shared Constants (K1 & TSL)', 'K1-Only Constants', 'TSL-Only Constants']:
        toc_lines.append(generate_toc_entry(2, section_name, False))
        
        # Add subsections and items
        if section_name in toc_entries_by_section:
            current_subsection = None
            for name, is_item in toc_entries_by_section[section_name]:
                if not is_item:
                    # Subsection
                    current_subsection = name
                    toc_lines.append(generate_toc_entry(3, name, False))
                else:
                    # Item (function/constant)
                    toc_lines.append(generate_toc_entry(4, name, True))
    
    toc_content = '\n'.join(toc_lines)
    
    # Replace placeholders in markdown
    print("\nReplacing placeholders in markdown...")
    
    # TOC
    toc_pattern = r'<!-- TOC_START -->.*?<!-- TOC_END -->'
    if re.search(toc_pattern, md_content, re.DOTALL):
        md_content = re.sub(toc_pattern, f'<!-- TOC_START -->\n{toc_content}\n<!-- TOC_END -->', md_content, flags=re.DOTALL)
        print("  ✓ TOC replaced")
    else:
        print("  ✗ TOC placeholders not found")
    
    # Shared Functions
    pattern = r'<!-- SHARED_FUNCTIONS_START -->.*?<!-- SHARED_FUNCTIONS_END -->'
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f'<!-- SHARED_FUNCTIONS_START -->\n\n{shared_func_content}<!-- SHARED_FUNCTIONS_END -->', md_content, flags=re.DOTALL)
        print("  ✓ Shared Functions replaced")
    else:
        print("  ✗ Shared Functions placeholders not found")
    
    # K1 Functions
    pattern = r'<!-- K1_ONLY_FUNCTIONS_START -->.*?<!-- K1_ONLY_FUNCTIONS_END -->'
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f'<!-- K1_ONLY_FUNCTIONS_START -->\n\n{k1_func_content}<!-- K1_ONLY_FUNCTIONS_END -->', md_content, flags=re.DOTALL)
        print("  ✓ K1-Only Functions replaced")
    else:
        print("  ✗ K1-Only Functions placeholders not found")
    
    # TSL Functions
    pattern = r'<!-- TSL_ONLY_FUNCTIONS_START -->.*?<!-- TSL_ONLY_FUNCTIONS_END -->'
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f'<!-- TSL_ONLY_FUNCTIONS_START -->\n\n{tsl_func_content}<!-- TSL_ONLY_FUNCTIONS_END -->', md_content, flags=re.DOTALL)
        print("  ✓ TSL-Only Functions replaced")
    else:
        print("  ✗ TSL-Only Functions placeholders not found")
    
    # Shared Constants
    pattern = r'<!-- SHARED_CONSTANTS_START -->.*?<!-- SHARED_CONSTANTS_END -->'
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f'<!-- SHARED_CONSTANTS_START -->\n\n{shared_const_content}<!-- SHARED_CONSTANTS_END -->', md_content, flags=re.DOTALL)
        print("  ✓ Shared Constants replaced")
    else:
        print("  ✗ Shared Constants placeholders not found")
    
    # K1 Constants
    pattern = r'<!-- K1_ONLY_CONSTANTS_START -->.*?<!-- K1_ONLY_CONSTANTS_END -->'
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f'<!-- K1_ONLY_CONSTANTS_START -->\n\n{k1_const_content}<!-- K1_ONLY_CONSTANTS_END -->', md_content, flags=re.DOTALL)
        print("  ✓ K1-Only Constants replaced")
    else:
        print("  ✗ K1-Only Constants placeholders not found")
    
    # TSL Constants
    pattern = r'<!-- TSL_ONLY_CONSTANTS_START -->.*?<!-- TSL_ONLY_CONSTANTS_END -->'
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f'<!-- TSL_ONLY_CONSTANTS_START -->\n\n{tsl_const_content}<!-- TSL_ONLY_CONSTANTS_END -->', md_content, flags=re.DOTALL)
        print("  ✓ TSL-Only Constants replaced")
    else:
        print("  ✗ TSL-Only Constants placeholders not found")
    
    # Write updated markdown
    print(f"\nWriting updated markdown to {md_path}...")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
