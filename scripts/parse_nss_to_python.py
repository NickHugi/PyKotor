"""Parse NSS files and generate Python scriptdefs.py entries.

This script parses k1_nwscript.nss and k2_nwscript.nss files and generates
the exact Python code needed for scriptdefs.py, ensuring 1:1 matching including
all documentation and typos.
"""

from __future__ import annotations

import re
from pathlib import Path


def parse_constant(line: str) -> tuple[str, str, str] | None:
    """Parse a constant definition line.
    
    Returns (datatype, name, value) or None if not a constant.
    """
    # Match: int NAME = VALUE;
    # Match: float NAME = VALUE;
    # Match: string NAME = "VALUE";
    match = re.match(r'^\s*(int|float|string)\s+(\w+)\s*=\s*(.+?);\s*$', line)
    if not match:
        return None
    
    datatype_str, name, value_str = match.groups()
    
    # Clean up value
    value_str = value_str.strip()
    
    # Handle string values
    if datatype_str == 'string':
        # Remove quotes
        value_str = value_str.strip('"')
        return (datatype_str, name, f'"{value_str}"')
    
    # Handle float values (may have 'f' suffix)
    if datatype_str == 'float':
        value_str = value_str.rstrip('f').strip()
        return (datatype_str, name, value_str)
    
    # Handle int values
    return (datatype_str, name, value_str)


def parse_function(lines: list[str], start_idx: int) -> tuple[dict, int] | None:
    """Parse a function definition.
    
    Returns (function_dict, next_line_idx) or None if not a function.
    """
    # Look for function signature: returntype name(params);
    # May have comments before it
    
    idx = start_idx
    comments = []
    
    # Collect comments before function
    while idx < len(lines):
        line = lines[idx].strip()
        if line.startswith('//'):
            comments.append(line)
            idx += 1
        elif line.startswith('//'):
            comments.append(line)
            idx += 1
        else:
            break
    
    if idx >= len(lines):
        return None
    
    # Look for function signature
    func_line = lines[idx].strip()
    
    # Match function signature: returntype name(params);
    # May span multiple lines
    func_match = re.match(
        r'^\s*(void|int|float|string|object|vector|location|event|effect|itemproperty|talent|action)\s+(\w+)\s*\((.*?)\)\s*;?\s*$',
        func_line
    )
    
    if not func_match:
        # Try to find function on current or next few lines
        combined = ' '.join(lines[idx:idx+3])
        func_match = re.search(
            r'(void|int|float|string|object|vector|location|event|effect|itemproperty|talent|action)\s+(\w+)\s*\((.*?)\)',
            combined
        )
        if func_match:
            returntype = func_match.group(1)
            name = func_match.group(2)
            params_str = func_match.group(3)
            # Extract the full line
            end_match = re.search(r'\)\s*;', combined)
            if end_match:
                idx += combined[:end_match.end()].count('\n')
        else:
            return None
    else:
        returntype = func_match.group(1)
        name = func_match.group(2)
        params_str = func_match.group(3)
        idx += 1
    
    # Parse parameters
    params = []
    if params_str.strip():
        param_parts = []
        depth = 0
        current = ''
        for char in params_str:
            if char == '(':
                depth += 1
                current += char
            elif char == ')':
                depth -= 1
                current += char
            elif char == ',' and depth == 0:
                param_parts.append(current.strip())
                current = ''
            else:
                current += char
        if current.strip():
            param_parts.append(current.strip())
        
        for param_str in param_parts:
            param_str = param_str.strip()
            if not param_str:
                continue
            
            # Match: datatype name = default
            param_match = re.match(
                r'^\s*(void|int|float|string|object|vector|location|event|effect|itemproperty|talent|action)\s+(\w+)(?:\s*=\s*(.+))?\s*$',
                param_str
            )
            if param_match:
                ptype, pname, pdefault = param_match.groups()
                params.append({
                    'type': ptype,
                    'name': pname,
                    'default': pdefault.strip() if pdefault else None
                })
    
    # Combine comments into description
    description = '\r\n'.join(comments) + f'\r\n{returntype} {name}({params_str});'
    raw = description
    
    return ({
        'returntype': returntype,
        'name': name,
        'params': params,
        'description': description,
        'raw': raw
    }, idx)


def parse_nss_file(nss_path: Path) -> tuple[list, list]:
    """Parse an NSS file and return (constants, functions)."""
    constants = []
    functions = []
    
    with open(nss_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n\r')
        
        # Skip empty lines and pure comment blocks
        if not line.strip() or line.strip().startswith('//') and '=' not in line:
            i += 1
            continue
        
        # Try to parse as constant
        const = parse_constant(line)
        if const:
            datatype, name, value = const
            constants.append({
                'datatype': datatype,
                'name': name,
                'value': value
            })
            i += 1
            continue
        
        # Try to parse as function
        func_result = parse_function(lines, i)
        if func_result:
            func_dict, next_idx = func_result
            functions.append(func_dict)
            i = next_idx
            continue
        
        i += 1
    
    return constants, functions


def generate_python_constant(const: dict) -> str:
    """Generate Python code for a constant."""
    datatype_map = {
        'int': 'DataType.INT',
        'float': 'DataType.FLOAT',
        'string': 'DataType.STRING'
    }
    
    dt = datatype_map.get(const['datatype'], f'DataType.{const["datatype"].upper()}')
    name = const['name']
    value = const['value']
    
    return f'    ScriptConstant({dt}, "{name}", {value}),'


def generate_python_function(func: dict) -> str:
    """Generate Python code for a function."""
    datatype_map = {
        'void': 'DataType.VOID',
        'int': 'DataType.INT',
        'float': 'DataType.FLOAT',
        'string': 'DataType.STRING',
        'object': 'DataType.OBJECT',
        'vector': 'DataType.VECTOR',
        'location': 'DataType.LOCATION',
        'event': 'DataType.EVENT',
        'effect': 'DataType.EFFECT',
        'itemproperty': 'DataType.ITEMPROPERTY',
        'talent': 'DataType.TALENT',
        'action': 'DataType.ACTION'
    }
    
    returntype = datatype_map.get(func['returntype'], f'DataType.{func["returntype"].upper()}')
    name = func['name']
    
    # Generate params
    params_list = []
    for param in func['params']:
        ptype = datatype_map.get(param['type'], f'DataType.{param["type"].upper()}')
        pname = param['name']
        pdefault = param['default']
        
        if pdefault:
            # Clean up default value
            pdefault = pdefault.rstrip('f').strip()
            if param['type'] == 'string':
                pdefault = pdefault.strip('"')
                pdefault = f'"{pdefault}"'
            params_list.append(f'ScriptParam({ptype}, "{pname}", {pdefault})')
        else:
            params_list.append(f'ScriptParam({ptype}, "{pname}", None)')
    
    params_str = '[' + ', '.join(params_list) + ']'
    
    # Escape description and raw
    description = func['description'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    raw = func['raw'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
    
    return f'''    ScriptFunction(
        {returntype},
        "{name}",
        {params_str},
        "{description}",
        "{raw}",
    ),'''


if __name__ == '__main__':
    # Parse K1
    k1_path = Path('vendor/NorthernLights/Scripts/k1_nwscript.nss')
    if k1_path.exists():
        print(f"Parsing {k1_path}...")
        k1_constants, k1_functions = parse_nss_file(k1_path)
        print(f"Found {len(k1_constants)} constants and {len(k1_functions)} functions")
        
        # Generate Python code
        print("\n# KOTOR_CONSTANTS = [")
        for const in k1_constants:
            print(generate_python_constant(const))
        print("]")
        
        print("\n# KOTOR_FUNCTIONS = [")
        for func in k1_functions[:5]:  # Just show first 5
            print(generate_python_function(func))
        print("...")
    else:
        print(f"File not found: {k1_path}")

