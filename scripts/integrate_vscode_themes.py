#!/usr/bin/env python3
"""Script to integrate VS Code themes into theme_manager.py and delete JSON files."""
from __future__ import annotations

import json
import re
from pathlib import Path

def strip_json_comments(text: str) -> str:
    """Strip JavaScript-style comments from JSON."""
    lines = text.split('\n')
    result = []
    in_string = False
    escape_next = False
    
    for line in lines:
        new_line = []
        i = 0
        while i < len(line):
            char = line[i]
            
            if escape_next:
                new_line.append(char)
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                escape_next = True
                new_line.append(char)
                i += 1
                continue
            
            if char == '"' and (i == 0 or line[i-1] != '\\'):
                in_string = not in_string
            
            if not in_string:
                # Check for // comment
                if char == '/' and i + 1 < len(line) and line[i+1] == '/':
                    break  # Rest of line is comment
                # Check for /* comment
                if char == '/' and i + 1 < len(line) and line[i+1] == '*':
                    # Skip until */
                    i += 2
                    while i + 1 < len(line):
                        if line[i] == '*' and line[i+1] == '/':
                            i += 2
                            break
                        i += 1
                    continue
            
            new_line.append(char)
            i += 1
        
        result.append(''.join(new_line))
    
    return '\n'.join(result)

def fix_json_trailing_commas(text: str) -> str:
    """Remove trailing commas before closing braces/brackets."""
    # Remove trailing commas before }
    text = re.sub(r',(\s*})', r'\1', text)
    # Remove trailing commas before ]
    text = re.sub(r',(\s*])', r'\1', text)
    return text

def parse_hex_color(color_str: str) -> tuple[int, int, int] | None:
    """Parse a hex color string and return RGB tuple."""
    if not color_str or not isinstance(color_str, str):
        return None
    
    color_str = color_str.strip()
    
    # Remove alpha channel if present
    if len(color_str) == 9 and color_str.startswith("#"):
        color_str = color_str[:7]
    
    # Handle shorthand hex
    if len(color_str) == 4 and color_str.startswith("#"):
        r, g, b = color_str[1], color_str[2], color_str[3]
        color_str = f"#{r}{r}{g}{g}{b}{b}"
    
    # Parse hex
    try:
        if color_str.startswith("#") and len(color_str) == 7:
            r = int(color_str[1:3], 16)
            g = int(color_str[3:5], 16)
            b = int(color_str[5:7], 16)
            return (r, g, b)
    except Exception:
        pass
    
    return None

def extract_theme_colors(theme_data: dict | list) -> dict[str, str] | None:
    """Extract key colors from VS Code theme for palette creation."""
    # Handle case where theme_data might be a list
    if isinstance(theme_data, list):
        # Find first dict with colors
        for item in theme_data:
            if isinstance(item, dict) and "colors" in item:
                theme_data = item
                break
        else:
            return None
    
    if not isinstance(theme_data, dict):
        return None
    
    colors = theme_data.get("colors", {})
    if not colors:
        return None
    
    # Ensure colors is a dict
    if not isinstance(colors, dict):
        return None
    
    # Extract key colors with fallbacks
    def get_color(key: str, fallback: str | None = None) -> str:
        result = colors.get(key)
        if result and isinstance(result, str) and result.startswith("#"):
            return result
        if fallback:
            return fallback
        return ""
    
    bg = get_color("editor.background") or get_color("sideBar.background") or get_color("activityBar.background", "#1E1E1E")
    secondary_bg = get_color("sideBar.background") or get_color("activityBar.background") or bg
    text = get_color("foreground") or get_color("editor.foreground") or get_color("input.foreground", "#FFFFFF")
    tooltip = get_color("editorHoverWidget.background") or get_color("editorWidget.background") or secondary_bg
    highlight = get_color("editor.selectionBackground") or get_color("list.activeSelectionBackground") or get_color("focusBorder") or get_color("button.background", "#0078D4")
    bright_text = get_color("foreground", "#FFFFFF")
    
    return {
        "primary_bg": bg,
        "secondary_bg": secondary_bg,
        "text": text,
        "tooltip": tooltip,
        "highlight": highlight,
        "bright_text": bright_text,
    }

def sanitize_theme_name(filename: str) -> str:
    """Convert theme filename to valid Python dict key."""
    name = Path(filename).stem.lower()
    # Replace spaces and special chars with hyphens
    name = re.sub(r'[^\w\-]', '-', name)
    # Remove multiple hyphens
    name = re.sub(r'-+', '-', name)
    # Remove leading/trailing hyphens
    name = name.strip('-')
    return name

def generate_palette_entry(theme_name: str, theme_colors: dict, theme_type: str = "dark") -> str:
    """Generate Python code entry for theme configuration."""
    primary = theme_colors.get("primary_bg", "#2D2D2D")
    secondary = theme_colors.get("secondary_bg", "#1E1E1E")
    text = theme_colors.get("text", "#FFFFFF")
    tooltip = theme_colors.get("tooltip", secondary)
    highlight = theme_colors.get("highlight", "#0078D4")
    bright_text = theme_colors.get("bright_text", "#FFFFFF")
    
    # Create comment from theme name
    comment = theme_name.replace("-", " ").replace("_", " ").title()
    if theme_type:
        comment += f" ({theme_type})"
    
    entry = f'''            "{theme_name}": {{
                "style": "Fusion",
                # {comment}
                "palette": lambda: self.create_palette("{primary}", "{secondary}", "{text}", "{tooltip}", "{highlight}", "{bright_text}"),
            }},'''
    
    return entry

def process_themes():
    """Process all VS Code theme files and integrate them."""
    base_path = Path(__file__).parent.parent / "Tools" / "HolocronToolset" / "src" / "resources" / "extra_themes"
    theme_manager_path = Path(__file__).parent.parent / "Tools" / "HolocronToolset" / "src" / "toolset" / "gui" / "common" / "style" / "theme_manager.py"
    
    if not base_path.exists():
        print(f"Error: extra_themes path not found: {base_path}")
        return
    
    if not theme_manager_path.exists():
        print(f"Error: theme_manager.py not found: {theme_manager_path}")
        return
    
    # Find all JSON theme files
    theme_files = sorted([
        f for f in base_path.glob("*.json")
        if "config" not in f.stem.lower()
        and "settings" not in f.stem.lower()
        and "template" not in f.stem.lower()
    ])
    
    print(f"Found {len(theme_files)} theme files to process")
    
    # Read current theme_manager.py
    with open(theme_manager_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find where to insert themes (before the closing brace of configs dict)
    # Look for the pattern: last entry }, closing }, then "# Try to find theme" comment
    # First, find the last theme entry in the configs dict
    lines = content.split('\n')
    insertion_point = None
    indent = "            "
    
    # Look backwards from end for the pattern
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i]
        # Look for the comment "# Try to find theme" or "# If not found in built-ins"
        if "# Try to find theme" in line or "# If not found in built-ins" in line:
            # Go backwards to find the closing brace of configs
            for j in range(i - 1, -1, -1):
                if lines[j].strip() == "}":
                    # This is the closing brace - insert before this
                    insertion_point = sum(len(l) + 1 for l in lines[:j])  # +1 for newline
                    break
            break
    
    if insertion_point is None:
        # Try finding by looking for pattern: "},\n        }\n        # Try"
        pattern = r'(\},\s*\n)(\s+)\}\s*\n(\s+)# Try to find theme'
        match = re.search(pattern, content)
        if match:
            insertion_point = match.end() - len(match.group(2)) - len("}") - len(match.group(3)) - len("# Try to find theme")
            indent = match.group(2)
        else:
            print("Error: Could not find insertion point in theme_manager.py")
            # Find last "},\n        }" pattern
            pattern = r'(\},\s*\n)(\s+)\}\s*\n(\s+)theme_lower'
            match = re.search(pattern, content)
            if match:
                insertion_point = match.start() + len(match.group(1))
                indent = match.group(2)
            else:
                return
    
    # Process each theme
    new_entries = []
    processed = 0
    failed = 0
    
    for theme_file in theme_files:
        try:
            with open(theme_file, "r", encoding="utf-8") as f:
                raw_content = f.read()
            
            # Strip comments and fix trailing commas
            cleaned_content = strip_json_comments(raw_content)
            cleaned_content = fix_json_trailing_commas(cleaned_content)
            
            # Handle bridge.json and similar files that are arrays
            if cleaned_content.strip().startswith('['):
                # It's an array, try to extract theme from array
                try:
                    array_data = json.loads(cleaned_content)
                    if isinstance(array_data, list) and len(array_data) > 0:
                        # Find dict with colors
                        for item in array_data:
                            if isinstance(item, dict):
                                if "colors" in item:
                                    theme_data = item
                                    break
                                elif "theme" in item and isinstance(item["theme"], dict) and "colors" in item["theme"]:
                                    theme_data = {"colors": item["theme"]["colors"], "type": item.get("theme", {}).get("type", "dark")}
                                    break
                        else:
                            print(f"  Skipping {theme_file.name}: Array structure but no colors found")
                            continue
                    else:
                        print(f"  Skipping {theme_file.name}: Empty array")
                        continue
                except json.JSONDecodeError:
                    pass
            
            # Try normal JSON parsing
            if 'theme_data' not in locals() or not theme_data:
                try:
                    theme_data = json.loads(cleaned_content)
                except json.JSONDecodeError:
                    # Try with more aggressive cleaning
                    cleaned_content = re.sub(r',\s*}', '}', cleaned_content)
                    cleaned_content = re.sub(r',\s*]', ']', cleaned_content)
                    # Remove any remaining problematic patterns
                    cleaned_content = re.sub(r':\s*undefined', ': null', cleaned_content)
                    cleaned_content = re.sub(r':\s*null,?\s*$', ': null', cleaned_content, flags=re.MULTILINE)
                    # Remove unquoted keys (try to quote them)
                    cleaned_content = re.sub(r'(\w+):', r'"\1":', cleaned_content)
                    # Fix common issues
                    cleaned_content = re.sub(r'"(\w+)":\s*\{', r'"\1": {', cleaned_content)  # Fix already-quoted
                    try:
                        theme_data = json.loads(cleaned_content)
                    except json.JSONDecodeError as e:
                        # Last resort: try to extract just the colors section manually via regex
                        colors_match = re.search(r'"colors"\s*:\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', cleaned_content, re.DOTALL)
                        if colors_match:
                            # Try to build a minimal theme structure
                            print(f"  Warning: {theme_file.name} has parsing issues, attempting manual color extraction")
                            # Extract individual color entries
                            color_entries = re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', colors_match.group(1))
                            if color_entries:
                                theme_data = {"colors": dict(color_entries), "type": "dark"}
                            else:
                                continue
                        else:
                            print(f"  Error: {theme_file.name} - {str(e)[:100]}")
                            continue
            
            theme_colors = extract_theme_colors(theme_data)
            if not theme_colors:
                print(f"  Skipping {theme_file.name}: No colors found")
                failed += 1
                continue
            
            theme_type = theme_data.get("type", "dark").lower()
            theme_name = sanitize_theme_name(theme_file.name)
            
            entry = generate_palette_entry(theme_name, theme_colors, theme_type)
            new_entries.append(entry)
            
            # Delete the JSON file
            theme_file.unlink()
            processed += 1
            
            if processed % 50 == 0:
                print(f"  Processed {processed} themes...")
                
        except Exception as e:
            print(f"  Error processing {theme_file.name}: {e}")
            failed += 1
            continue
    
    if not new_entries:
        print("No themes to add!")
        return
    
    # Find insertion point - right before the closing } of configs dict
    # Look for pattern: last entry ends with "},\n" then "\n        }\n" then comment
    pattern = r'(\},\s*\n)(\s+)\}\s*\n(\s+)# Try to find theme'
    match = re.search(pattern, content)
    
    if match:
        # Insert before the closing }
        insertion_point = match.start() + len(match.group(1))
        indent = match.group(2)
    else:
        # Try alternative - look for the closing brace before "theme_lower"
        pattern = r'(\},\s*\n)(\s+)\}\s*\n\s+theme_lower'
        match = re.search(pattern, content)
        if match:
            insertion_point = match.start() + len(match.group(1))
            indent = match.group(2)
        else:
            print("Error: Could not determine insertion point")
            print("Searching for last theme entry manually...")
            # Find last "},\n            }," pattern
            lines = content.split('\n')
            for i in range(len(lines) - 1, max(0, len(lines) - 50), -1):
                if re.match(r'^\s+"\w+":\s*\{$', lines[i]):
                    # Found a theme entry start, now find its end
                    for j in range(i, min(len(lines), i + 10)):
                        if '},\n' in lines[j] or (j + 1 < len(lines) and lines[j].strip() == '},' and lines[j+1].strip() == '}'):
                            # This might be the last entry
                            # Look ahead for closing brace
                            if j + 2 < len(lines) and 'theme_lower' in lines[j+2]:
                                # Calculate insertion point
                                insertion_point = sum(len(l) + 1 for l in lines[:j+1])
                                indent = "            "
                                break
                    if insertion_point:
                        break
            if not insertion_point:
                print("  Still could not find insertion point. Aborting.")
                return
    
    # Insert all new entries before the closing brace
    new_content = (
        content[:insertion_point] +
        "\n".join(new_entries) + "\n" + indent +
        content[insertion_point:]
    )
    
    # Write updated file
    with open(theme_manager_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"\nCompleted!")
    print(f"  Processed: {processed} themes")
    print(f"  Failed: {failed} themes")
    print(f"  Added {len(new_entries)} theme entries to theme_manager.py")

if __name__ == "__main__":
    process_themes()

