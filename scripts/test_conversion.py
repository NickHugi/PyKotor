#!/usr/bin/env python3
"""Test the conversion function."""
import re

def convert_old_format_to_headers(content: str) -> str:
    """Convert old format (**`FunctionName`** and - `CONSTANT_NAME`) to header format (####)."""
    lines = content.split('\n')
    new_lines = []
    converted_count = 0
    
    for i, line in enumerate(lines):
        # Skip if already a header
        if line.strip().startswith('####'):
            new_lines.append(line)
            continue
        
        # Convert function definitions from **`FunctionName(...)`** to #### `FunctionName(...)`
        func_match = re.search(r'\*\*`(\w+)\(([^)]*)\)`\*\*', line)
        if func_match:
            func_name = func_match.group(1)
            params = func_match.group(2)
            # Extract any trailing content (like - Routine X or **(K1 & TSL)**)
            trailing = line[func_match.end():].strip()
            # Rebuild as header
            new_line = f"#### `{func_name}({params})`"
            if trailing:
                new_line += f" {trailing}"
            new_lines.append(new_line)
            converted_count += 1
            print(f"Line {i+1}: Converting function {func_name}")
            continue
        
        # Convert constant definitions from - `CONSTANT_NAME` (value): Description to #### `CONSTANT_NAME`
        const_match = re.match(r'^- `(\w+)`\s*\(([^)]+)\):\s*(.*)$', line.strip())
        if const_match:
            const_name = const_match.group(1)
            value = const_match.group(2)
            description = const_match.group(3).strip()
            # Extract game tag if present
            game_tag = ""
            if '**(K1 & TSL)**' in description:
                game_tag = " **(K1 & TSL)**"
                description = description.replace('**(K1 & TSL)**', '').strip()
            elif '**(K1)**' in description:
                game_tag = " **(K1)**"
                description = description.replace('**(K1)**', '').strip()
            elif '**(TSL)**' in description:
                game_tag = " **(TSL)**"
                description = description.replace('**(TSL)**', '').strip()
            # Rebuild as header
            new_line = f"#### `{const_name}`{game_tag}\n\n"
            new_line += f"({value}): {description}" if description else f"({value})"
            new_lines.append(new_line)
            converted_count += 1
            print(f"Line {i+1}: Converting constant {const_name}")
            continue
        
        # Regular line
        new_lines.append(line)
    
    print(f"\nTotal converted: {converted_count}")
    return '\n'.join(new_lines)

# Test with a sample
test_content = """**`SwitchPlayerCharacter(int nNPC)`** - Routine 11

- Switches the main character to a specified NPC

- `ALIGNMENT_ALL` (0): All alignments
"""

result = convert_old_format_to_headers(test_content)
print("\nResult:")
print(result)

