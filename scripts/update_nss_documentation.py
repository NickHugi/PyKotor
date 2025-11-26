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
- <!-- KOTOR_LIBRARY_START --> ... <!-- KOTOR_LIBRARY_END -->
- <!-- TSL_LIBRARY_START --> ... <!-- TSL_LIBRARY_END -->
- <!-- TOC_START --> ... <!-- TOC_END -->
"""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Callable
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "Libraries" / "PyKotor" / "src"))

try:
    from pykotor.common.script import DataType, ScriptConstant, ScriptFunction  # type: ignore[import]
    from pykotor.common import scriptdefs, scriptlib  # type: ignore[import]
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
    if any(x in name_lower for x in ["party", "switchplayer", "addavailable"]):
        return "Party Management"
    
    # Global variables
    if any(x in name_lower for x in ["global", "getglobal", "setglobal"]):
        return "Global Variables"
    
    # Player character
    if any(x in name_lower for x in ["getispc", "getpcspeaker", "player"]):
        return "Player Character Functions"
    
    # Alignment
    if any(x in name_lower for x in ["alignment", "align"]):
        return "Alignment System"
    
    # Class
    if any(x in name_lower for x in ["class", "getclass", "setclass"]):
        return "Class System"
    
    # Effects
    if any(x in name_lower for x in ["effect", "applyeffect", "geteffect", "removeeffect"]):
        return "Effects System"
    
    # Item properties
    if any(x in name_lower for x in ["itemproperty", "createitemproperty", "getitemproperty"]):
        return "Item Properties"
    
    # Actions
    if name_lower.startswith("action"):
        return "Actions"
    
    # Skills and feats
    if any(x in name_lower for x in ["skill", "feat", "getskill", "gethasfeat"]):
        return "Skills and Feats"
    
    # Abilities and stats
    if any(x in name_lower for x in ["ability", "getability", "getstat"]):
        return "Abilities and Stats"
    
    # Object query
    if any(x in name_lower for x in ["getobject", "createobject", "destroyobject", "getnearest"]):
        return "Object Query and Manipulation"
    
    # Item management
    if any(x in name_lower for x in ["item", "createitem", "getitem", "giveitem", "takeitem"]):
        return "Item Management"
    
    # Local variables
    if any(x in name_lower for x in ["local", "getlocal", "setlocal"]):
        return "Local Variables"
    
    # Module and area
    if any(x in name_lower for x in ["module", "area", "getarea", "getmodule"]):
        return "Module and Area Functions"
    
    # Combat
    if any(x in name_lower for x in ["combat", "attack", "attacker", "killer"]):
        return "Combat Functions"
    
    # Dialog
    if any(x in name_lower for x in ["conversation", "dialog", "bark", "speak"]):
        return "Dialog and Conversation Functions"
    
    # Sound
    if any(x in name_lower for x in ["sound", "music", "ambient", "play"]):
        return "Sound and Music Functions"
    
    # Default
    return "Other Functions"


def categorize_constant(const: ScriptConstant) -> str:
    """Categorize a constant into a section based on its name."""
    name_lower = const.name.lower()
    
    # Planet
    if name_lower.startswith("planet_"):
        return "Planet Constants"
    
    # NPC
    if name_lower.startswith("npc_"):
        return "NPC Constants"
    
    # Alignment
    if "alignment" in name_lower:
        return "Alignment Constants"
    
    # Class type
    if "class_type" in name_lower:
        return "Class Type Constants"
    
    # Object type
    if "object_type" in name_lower:
        return "Object Type Constants"
    
    # Ability
    if name_lower.startswith("ability_"):
        return "Ability Constants"
    
    # VFX
    if name_lower.startswith("vfx_"):
        return "Visual Effects (VFX)"
    
    # Inventory
    if "inventory" in name_lower:
        return "Inventory Constants"
    
    # Default
    return "Other Constants"


def title_to_anchor(title: str) -> str:
    """Convert a markdown title to an anchor link."""
    anchor = title.lower()
    anchor = re.sub(r"[^\w\s-]", "", anchor)
    anchor = re.sub(r"[-\s]+", "-", anchor)
    return anchor.strip("-")


def parse_gitmodules() -> dict[str, str]:
    """Parse .gitmodules to get vendor path -> repo name mapping."""
    gitmodules_path = project_root / ".gitmodules"
    vendor_to_repo: dict[str, str] = {}

    if not gitmodules_path.exists():
        return vendor_to_repo

    content = gitmodules_path.read_text(encoding="utf-8")

    # Match [submodule "vendor/..."] followed by url
    pattern = r'\[submodule "vendor/([^"]+)"\]\s*\n\s*path = vendor/([^\n]+)\s*\n\s*url = https://github\.com/([^/\n]+)/([^/\n\.]+)'
    matches = re.finditer(pattern, content, re.MULTILINE)

    for match in matches:
        submodule_name, path, org, repo = match.groups()
        # Extract repo name (remove .git if present)
        repo_name = repo.replace(".git", "")
        vendor_to_repo[f"vendor/{path}"] = repo_name

    return vendor_to_repo


def get_tracked_files(vendor_path: Path) -> set[Path]:
    """
    Get all tracked files in a vendor submodule using git ls-files.
    This respects .gitignore automatically since git only tracks non-ignored files.
    Returns set of Path objects relative to vendor_path.
    """
    tracked_files: set[Path] = set()

    if not vendor_path.exists():
        return tracked_files

    # Check if this is a git repository
    git_dir = vendor_path / ".git"
    if not git_dir.exists():
        # Not a git repo, return empty set (we'll skip it)
        return tracked_files

    try:
        # Use git ls-files to get all tracked files (respects .gitignore)
        # -z: null-terminated output for parsing
        cmd = ["git", "-C", str(vendor_path), "ls-files", "-z"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            # Split by null character and filter out empty strings
            files = [f for f in result.stdout.split("\0") if f.strip()]
            for file_str in files:
                file_path = vendor_path / file_str
                if file_path.is_file():
                    tracked_files.add(file_path.relative_to(vendor_path))
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        # Git not available or not a git repo, return empty set
        pass

    return tracked_files


def find_vendor_references(
    name: str,
    vendor_to_repo: dict[str, str],
    verbose: bool = True,
) -> list[tuple[str, str, int]]:
    """
    Search vendor directory for mentions of name using ripgrep.
    Only searches files that are tracked by git (respects .gitignore).
    Returns list of (repo_name, relpath, line_number) tuples.
    Ripgrep is extremely fast (written in Rust, uses memory-mapped files, parallel processing).
    """
    references: list[tuple[str, str, int]] = []
    vendor_dir: Path = project_root / "vendor"

    if not vendor_dir.exists():
        return references

    # Use ripgrep (rg) - it's extremely fast and respects .gitignore by default
    # This means it will automatically skip files ignored by each vendor project's .gitignore
    try:
        # -n: show line numbers
        # -T: skip binary files (--type-not is not valid, use -T)
        # -i: case insensitive (functions/constants might be referenced in different cases)
        # -w: word boundary (match whole words only)
        # -F: fixed string (treat pattern as literal, not regex - avoids escaping issues)
        # Note: ripgrep respects .gitignore by default, so we don't need --no-ignore
        # It will automatically respect each vendor submodule's .gitignore file
        cmd: list[str] = ["rg", "-n", "-i", "-w", "-F", name, str(vendor_dir)]
        if verbose:
            print(f"    → Searching for: {name}")
        
        # Use errors='replace' to handle encoding issues gracefully
        result: subprocess.CompletedProcess[str] | None = None
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='replace'  # Replace invalid UTF-8 with replacement characters
            )
        except subprocess.TimeoutExpired:
            if verbose:
                print(f"    ⚠ Timeout searching for: {name}")
            return references
        except Exception as e:
            if verbose:
                print(f"    ⚠ Error running ripgrep for {name}: {e}")
            return references

        # Check if result is valid
        if result is None or result.stdout is None:
            return references

        # ripgrep returns 0 if matches found, 1 if no matches, 2+ for errors
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if not line.strip():
                    continue
                # Format: path:line:content
                # On Windows, paths can contain colons (e.g., G:\path\to\file.py:123:content)
                # Split from the RIGHT to handle Windows drive letters correctly
                try:
                    # rsplit with maxsplit=2 gives us: [path, line, content]
                    parts = line.rsplit(":", 2)
                    if len(parts) < 2:
                        continue
                    
                    file_path_str = parts[0]
                    line_num = int(parts[1])
                    
                    # Filter out files containing 'nwscript' or 'scriptlib' in their path
                    file_path_lower = file_path_str.lower()
                    if "nwscript" in file_path_lower or "scriptlib" in file_path_lower:
                        continue
                    
                    # Filter out specific files
                    # Normalize path separators for comparison
                    normalized_path = file_path_str.replace("\\", "/").lower()
                    if "northernlights/assets/scripts/ncs/constants.cs" in normalized_path:
                        continue
                    if "kotormessageinjector/kotormessageinjector/kotorhelpers_constants.cs" in normalized_path:
                        continue
                    
                    # ripgrep returns paths like: .\HoloLSP\file.py or HoloLSP\file.py or ./HoloLSP/file.py
                    # Or absolute paths like: G:\GitHub\PyKotor\vendor\HoloLSP\file.py
                    # Strip leading .\ or ./ if present
                    if file_path_str.startswith(".\\") or file_path_str.startswith("./"):
                        file_path_str = file_path_str[2:]
                    
                    # Filter out HoloLSP vendor subfolder
                    if file_path_str.lower().startswith("hololsp") or file_path_str.lower().startswith("hololsp\\") or file_path_str.lower().startswith("hololsp/"):
                        continue
                    
                    # Convert to absolute path by joining with vendor_dir
                    file_path = (vendor_dir / file_path_str).resolve()
                    
                    # Get path relative to vendor directory
                    try:
                        relpath_from_vendor = file_path.relative_to(vendor_dir.resolve())
                    except ValueError:
                        # Path is not within vendor directory, skip
                        continue
                    
                    # relpath_from_vendor is like: HoloLSP/vendor/pykotor/common/scriptlib.py
                    # Find which vendor submodule by checking first directory component
                    parts_list = relpath_from_vendor.parts
                    if not parts_list:
                        continue
                    
                    vendor_subdir_name = parts_list[0]  # e.g., "HoloLSP"
                    
                    # Skip HoloLSP vendor subfolder entirely
                    if vendor_subdir_name.lower() == "hololsp":
                        continue
                    
                    # Find the matching vendor_path_key (e.g., "vendor/HoloLSP")
                    vendor_subfolder: str | None = None
                    for vendor_path_key in vendor_to_repo.keys():
                        if Path(vendor_path_key).name == vendor_subdir_name:
                            vendor_subfolder = vendor_path_key
                            break

                    if vendor_subfolder and vendor_subfolder in vendor_to_repo:
                        repo_name = vendor_to_repo[vendor_subfolder]
                        # Get path relative to vendor subfolder
                        # Remove the first directory component (the submodule name)
                        subfolder_relpath = Path(*parts_list[1:]) if len(parts_list) > 1 else Path(".")
                        references.append((repo_name, str(subfolder_relpath), line_num))
                        # Log when a reference is found (limit to first 10 to avoid spam)
                        if verbose and len(references) <= 10:
                            print(f"    ✓ Found in {repo_name}/{subfolder_relpath}:{line_num}")
                except (ValueError, IndexError, Exception):
                    # Silently skip parse errors - they're usually from edge cases
                    continue
        elif result.returncode > 1:
            # Error occurred (not just "no matches found")
            if verbose:
                stderr_msg = result.stderr[:200] if result.stderr else "Unknown error"
                print(f"    ⚠ ripgrep error (code {result.returncode}): {stderr_msg}")
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError, UnicodeDecodeError, AttributeError) as e:
        if verbose:
            print(f"    ⚠ Exception searching for {name}: {type(e).__name__}")
        # Fall through to manual search
    except Exception as e:
        # Catch-all for any other unexpected errors
        if verbose:
            print(f"    ⚠ Unexpected error searching for {name}: {type(e).__name__}: {e}")
        return references
    
    # Fall back to manual search if ripgrep not available or fails
    # Only do this if we haven't found any references yet
    if not references:
        try:
            # Use git ls-files to get tracked files (respects .gitignore)
            name_lower = name.lower()
            for vendor_path_str, repo_name in vendor_to_repo.items():
                vendor_path_obj: Path = project_root / vendor_path_str
                if not vendor_path_obj.exists():
                    continue

                # Get tracked files (respects .gitignore)
                tracked_files = get_tracked_files(vendor_path_obj)

                if not tracked_files:
                    # Not a git repo or git not available, skip
                    continue

                # Search only tracked files
                for rel_file_path in tracked_files:
                    # Filter out specific files
                    normalized_path = str(rel_file_path).replace("\\", "/").lower()
                    if "northernlights/assets/scripts/ncs/constants.cs" in normalized_path:
                        continue
                    if "kotormessageinjector/kotormessageinjector/kotorhelpers_constants.cs" in normalized_path:
                        continue
                    
                    file_path_obj = vendor_path_obj / rel_file_path
                    if not file_path_obj.is_file():
                        continue
                    try:
                        if file_path_obj.stat().st_size > 10 * 1024 * 1024:  # Skip files > 10MB
                            continue
                        with open(file_path_obj, "r", encoding="utf-8", errors="ignore") as f:
                            for line_num, line in enumerate(f, 1):
                                line_lower = line.lower()
                                # Simple whole-word matching: check if name appears as a word
                                if name_lower in line_lower:
                                    # Check if it's a whole word (preceded/followed by non-alphanumeric or at boundaries)
                                    idx = line_lower.find(name_lower)
                                    while idx != -1:
                                        # Check character before (if exists)
                                        before_ok = idx == 0 or not (line[idx - 1].isalnum() or line[idx - 1] == "_")
                                        # Check character after (if exists)
                                        after_idx = idx + len(name)
                                        after_ok = after_idx >= len(line) or not (line[after_idx].isalnum() or line[after_idx] == "_")

                                        if before_ok and after_ok:
                                            references.append((repo_name, str(rel_file_path), line_num))
                                            break  # Found match, move to next line

                                        # Find next occurrence
                                        idx = line_lower.find(name_lower, idx + 1)
                    except Exception:
                        continue
        except Exception as e:
            if verbose:
                print(f"    ⚠ Error in manual search fallback for {name}: {type(e).__name__}")
            # Continue anyway - we'll return what we have

    # Deduplicate and sort
    seen: set[tuple[str, str, int]] = set()
    unique_refs: list[tuple[str, str, int]] = []
    for ref in references:
        if ref not in seen:
            seen.add(ref)
            unique_refs.append(ref)

    # Sort by repo name, then file path, then line number
    unique_refs.sort(key=lambda x: (x[0], x[1], x[2]))

    return unique_refs


def format_references(
    references: list[tuple[str, str, int]],
) -> str:
    """Format references as markdown links."""
    if not references:
        return ""

    md = "\n**References**:\n\n"

    # Group by repo
    by_repo: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for repo_name, relpath, line_num in references:
        by_repo[repo_name].append((relpath, line_num))

    for repo_name in sorted(by_repo.keys()):
        file_refs = by_repo[repo_name]
        # Group by file
        by_file: dict[str, list[int]] = defaultdict(list)
        for relpath, line_num in file_refs:
            by_file[relpath].append(line_num)

        for relpath in sorted(by_file.keys()):
            line_nums = sorted(set(by_file[relpath]))
            # URL encode the path for GitHub
            encoded_path = quote(relpath.replace("\\", "/"), safe="/")
            # Display text should be vendor/<relpath>:<line_number>
            display_path = relpath.replace("\\", "/")
            # Format: vendor/reone/src/libs/resource/format/ssfreader.cpp:31
            url = f"https://github.com/th3w1zard1/{repo_name}/blob/master/{encoded_path}#L{line_nums[0]}"
            md += f"- [`vendor/{display_path}:{line_nums[0]}`]({url})\n"

    return md


def format_function_markdown(
    func: ScriptFunction,
    routine_num: int | None,
    references: str = "",
) -> str:
    """Format a function as markdown."""
    routine_str = f" - Routine {routine_num}" if routine_num else ""
    
    # Extract description
    desc_lines = []
    routine_num_line = None
    if func.description:
        for line in func.description.split("\n"):
            line = line.strip()
            if line.startswith("//"):
                line = line[2:].strip()
                if re.match(r"^\d+\.\s*\w+$", line):
                    routine_num_line = f"`{line}`"
                elif re.match(r"^\d+[:.]", line):
                    match = re.match(r"^(\d+)[:.]\s*(.*)$", line)
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
    param_names = ", ".join([p.name for p in func.params])
    
    # Build markdown with anchor and header
    anchor = title_to_anchor(func.name)
    md = f'<a id="{anchor}"></a>\n#### `{func.name}({param_names})`{routine_str}\n\n'
    
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
    
    if references:
        md += references

    return md + "\n"


def format_constant_markdown(
    const: ScriptConstant,
    references: str = "",
) -> str:
    """Format a constant as markdown."""
    value_str = str(const.value)
    if const.datatype == DataType.STRING:
        value_str = f'"{value_str}"'
    anchor = title_to_anchor(const.name)
    description = const.name.replace("_", " ").title()
    md = f'<a id="{anchor}"></a>\n#### `{const.name}`\n\n({value_str}): {description}\n'
    if references:
        md += references
    return md + "\n"


def format_library_markdown(
    lib_name: str,
    lib_content: bytes,
    references: str = "",
) -> str:
    """Format a library file as markdown."""
    anchor = title_to_anchor(lib_name)
    # Decode bytes to string, handling errors gracefully
    try:
        content_str = lib_content.decode("utf-8", errors="replace")
    except Exception:
        content_str = str(lib_content)

    # Extract first comment line if available for description
    lines = content_str.split("\n")
    description = lib_name.replace("_", " ").replace("k inc", "").replace("a ", "").strip().title()
    if lines and lines[0].strip().startswith("//"):
        first_comment = lines[0].strip()[2:].strip()
        if first_comment:
            description = first_comment

    md = f'<a id="{anchor}"></a>\n#### `{lib_name}`\n\n'
    md += f"**Description**: {description}\n\n"
    md += f'**Usage**: `#include "{lib_name}"`\n\n'
    md += "**Source Code**:\n\n```nss\n"
    # Limit source code display to first 50 lines to avoid huge blocks
    source_lines = content_str.split("\n")[:50]
    md += "\n".join(source_lines)
    total_lines = len(content_str.split("\n"))
    if total_lines > 50:
        remaining = total_lines - 50
        md += f"\n... ({remaining} more lines)"
    md += "\n```\n"

    if references:
        md += references

    return md + "\n"


def generate_toc_entry(level: int, title: str, is_item: bool = False) -> str:
    """Generate a TOC entry."""
    anchor = title_to_anchor(title)
    if is_item:
        indent = "      "  # 6 spaces for items under subsections
        return f"{indent}- [`{title}`](#{anchor})"
    else:
        indent = "  " * (level - 2)  # Level 2 = no indent, Level 3 = 2 spaces, Level 4 = 4 spaces
        return f"{indent}- [{title}](#{anchor})"


def build_section_content(
    items_by_category: dict[str, list[ScriptFunction | ScriptConstant]],
    format_func: Callable[..., str],
    item_type: str,
    vendor_to_repo: dict[str, str],
) -> tuple[str, list[tuple[str, bool]]]:
    """Build content for a section and return (content, toc_entries)."""
    content_parts: list[str] = []
    toc_entries: list[tuple[str, bool]] = []

    # Count total items for progress tracking
    total_items = sum(len(items) for items in items_by_category.values())
    processed_items = 0
    
    # Sort categories alphabetically
    for category in sorted(items_by_category.keys()):
        items = items_by_category[category]
        if not items:
            continue
        
        # Add category header
        content_parts.append(f"### {category}\n\n")
        toc_entries.append((category, False))
        
        # Sort items alphabetically
        items_sorted = sorted(items, key=lambda x: x.name.lower())
        
        # Add items
        for item in items_sorted:
            processed_items += 1
            # Show progress every 10 items or for first/last item
            if processed_items % 10 == 0 or processed_items == 1 or processed_items == total_items:
                print(f"  Processing {item_type} {processed_items}/{total_items}: {item.name}")

            # Find vendor references using ripgrep (fast!)
            try:
                refs: list[tuple[str, str, int]] = find_vendor_references(item.name, vendor_to_repo, verbose=True)
                refs_md = format_references(refs)
                if refs:
                    print(f"      → Found {len(refs)} reference(s) for {item.name}")
            except Exception as e:
                print(f"      ⚠ Error finding references for {item.name}: {type(e).__name__}")
                refs_md = ""
                refs = []

            if item_type == "function":
                routine_num = extract_routine_number(item.description or item.raw)
                item_md = format_func(item, routine_num, refs_md)
            else:
                item_md = format_func(item, refs_md)
            content_parts.append(item_md)
            toc_entries.append((item.name, True))
    
    return "".join(content_parts), toc_entries


def main():
    """Main function to update NSS-File-Format.md."""
    project_root: Path = Path(__file__).parent.parent
    md_path: Path = project_root / "wiki" / "NSS-File-Format.md"
    
    if not md_path.exists():
        print(f"Error: {md_path} not found")
        return 1
    
    # Read existing markdown
    print("Reading existing markdown...")
    md_content: str = md_path.read_text(encoding="utf-8")

    # Parse .gitmodules for vendor repo mappings
    print("Parsing .gitmodules for vendor repository mappings...")
    vendor_to_repo: dict[str, str] = parse_gitmodules()
    print(f"Found {len(vendor_to_repo)} vendor submodules")

    # Check if ripgrep is available
    try:
        subprocess.run(["rg", "--version"], capture_output=True, check=True, timeout=5)
        print("✓ Using ripgrep for fast searches")
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        print("⚠ Warning: ripgrep not found. Searches will be slower.")
        print("  Install ripgrep for best performance: https://github.com/BurntSushi/ripgrep#installation")
        print("  On Windows: `choco install ripgrep`  or  `scoop install ripgrep`")
    
    # Get all functions and constants
    print("Extracting functions and constants from scriptdefs.py...")
    k1_functions: list[ScriptFunction] = scriptdefs.KOTOR_FUNCTIONS
    k1_constants: list[ScriptConstant] = scriptdefs.KOTOR_CONSTANTS
    tsl_functions: list[ScriptFunction] = scriptdefs.TSL_FUNCTIONS
    tsl_constants: list[ScriptConstant] = scriptdefs.TSL_CONSTANTS
    
    print(f"K1: {len(k1_functions)} functions, {len(k1_constants)} constants")
    print(f"TSL: {len(tsl_functions)} functions, {len(tsl_constants)} constants")
    
    # Create sets for comparison
    k1_func_names: set[str] = {f.name for f in k1_functions}
    tsl_func_names: set[str] = {f.name for f in tsl_functions}
    k1_const_names: set[str] = {c.name for c in k1_constants}
    tsl_const_names: set[str] = {c.name for c in tsl_constants}
    
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
    print("\nBuilding section content (this may take a while as we search vendor directories)...")
    toc_entries_by_section: dict[str, list[tuple[str, bool]]] = {}

    print("\n[1/6] Processing Shared Functions...")
    shared_func_content, toc_entries_by_section["Shared Functions (K1 & TSL)"] = build_section_content(shared_funcs, format_function_markdown, "function", vendor_to_repo)

    print("\n[2/6] Processing K1-Only Functions...")
    k1_func_content, toc_entries_by_section["K1-Only Functions"] = build_section_content(k1_only_funcs, format_function_markdown, "function", vendor_to_repo)

    print("\n[3/6] Processing TSL-Only Functions...")
    tsl_func_content, toc_entries_by_section["TSL-Only Functions"] = build_section_content(tsl_only_funcs, format_function_markdown, "function", vendor_to_repo)

    print("\n[4/6] Processing Shared Constants...")
    shared_const_content, toc_entries_by_section["Shared Constants (K1 & TSL)"] = build_section_content(shared_consts, format_constant_markdown, "constant", vendor_to_repo)

    print("\n[5/6] Processing K1-Only Constants...")
    k1_const_content, toc_entries_by_section["K1-Only Constants"] = build_section_content(k1_only_consts, format_constant_markdown, "constant", vendor_to_repo)

    print("\n[6/6] Processing TSL-Only Constants...")
    tsl_const_content, toc_entries_by_section["TSL-Only Constants"] = build_section_content(tsl_only_consts, format_constant_markdown, "constant", vendor_to_repo)

    # Get library files
    print("\nExtracting library files from scriptlib.py...")
    kotor_libraries: list[str] = list(scriptlib.KOTOR_LIBRARY.keys())
    tsl_libraries: list[str] = list(scriptlib.TSL_LIBRARY.keys())
    print(f"KOTOR: {len(kotor_libraries)} library files")
    print(f"TSL: {len(tsl_libraries)} library files")

    # Build library content
    print("\nBuilding library content (searching vendor for references)...")
    kotor_lib_content_parts: list[str] = []
    tsl_lib_content_parts: list[str] = []
    
    # Sort libraries alphabetically
    total_libs = len(kotor_libraries) + len(tsl_libraries)
    lib_count = 0
    for lib_name in sorted(kotor_libraries):
        lib_count += 1
        print(f"  Processing library {lib_count}/{total_libs}: {lib_name}")
        lib_content = scriptlib.KOTOR_LIBRARY[lib_name]
        # Find vendor references for library file using ripgrep
        try:
            refs = find_vendor_references(lib_name, vendor_to_repo, verbose=True)
            refs_md = format_references(refs)
            if refs:
                print(f"      → Found {len(refs)} reference(s) for {lib_name}")
        except Exception as e:
            print(f"      ⚠ Error finding references for {lib_name}: {type(e).__name__}")
            refs_md = ""
        kotor_lib_content_parts.append(format_library_markdown(lib_name, lib_content, refs_md))

    for lib_name in sorted(tsl_libraries):
        lib_count += 1
        print(f"  Processing library {lib_count}/{total_libs}: {lib_name}")
        lib_content = scriptlib.TSL_LIBRARY[lib_name]
        # Find vendor references for library file using ripgrep
        try:
            refs = find_vendor_references(lib_name, vendor_to_repo, verbose=True)
            refs_md = format_references(refs)
            if refs:
                print(f"      → Found {len(refs)} reference(s) for {lib_name}")
        except Exception as e:
            print(f"      ⚠ Error finding references for {lib_name}: {type(e).__name__}")
            refs_md = ""
        tsl_lib_content_parts.append(format_library_markdown(lib_name, lib_content, refs_md))

    kotor_lib_content = "".join(kotor_lib_content_parts)
    tsl_lib_content = "".join(tsl_lib_content_parts)
    
    # Build TOC
    print("Building Table of Contents...")
    toc_lines: list[str] = []
    
    # Add major sections
    for section_name in [
        "Shared Functions (K1 & TSL)",
        "K1-Only Functions",
        "TSL-Only Functions",
        "Shared Constants (K1 & TSL)",
        "K1-Only Constants",
        "TSL-Only Constants",
        "KOTOR Library Files",
        "TSL Library Files",
    ]:
        toc_lines.append(generate_toc_entry(2, section_name, False))
        
        # Add subsections and items
        if section_name in toc_entries_by_section:
            for name, is_item in toc_entries_by_section[section_name]:
                if not is_item:
                    # Subsection
                    toc_lines.append(generate_toc_entry(3, name, False))
                else:
                    # Item (function/constant)
                    toc_lines.append(generate_toc_entry(4, name, True))
        elif section_name == "KOTOR Library Files":
            # Add library file entries
            for lib_name in sorted(kotor_libraries):
                toc_lines.append(generate_toc_entry(3, lib_name, True))
        elif section_name == "TSL Library Files":
            # Add library file entries
            for lib_name in sorted(tsl_libraries):
                toc_lines.append(generate_toc_entry(3, lib_name, True))

    toc_content = "\n".join(toc_lines) if toc_lines else ""
    
    # Replace placeholders in markdown
    print("\nReplacing placeholders in markdown...")
    
    # TOC - match with any content (including newlines) between placeholders
    toc_pattern = r"<!-- TOC_START -->.*?<!-- TOC_END -->"
    if re.search(toc_pattern, md_content, re.DOTALL):
        md_content = re.sub(toc_pattern, f"<!-- TOC_START -->\n{toc_content}\n<!-- TOC_END -->", md_content, flags=re.DOTALL)
        print(f"  ✓ TOC replaced ({len(toc_lines)} entries)")
    else:
        print("  ✗ TOC placeholders not found")
    
    # Shared Functions
    pattern = r"<!-- SHARED_FUNCTIONS_START -->.*?<!-- SHARED_FUNCTIONS_END -->"
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f"<!-- SHARED_FUNCTIONS_START -->\n\n{shared_func_content}<!-- SHARED_FUNCTIONS_END -->", md_content, flags=re.DOTALL)
        print("  ✓ Shared Functions replaced")
    else:
        print("  ✗ Shared Functions placeholders not found")
    
    # K1 Functions
    pattern = r"<!-- K1_ONLY_FUNCTIONS_START -->.*?<!-- K1_ONLY_FUNCTIONS_END -->"
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f"<!-- K1_ONLY_FUNCTIONS_START -->\n\n{k1_func_content}<!-- K1_ONLY_FUNCTIONS_END -->", md_content, flags=re.DOTALL)
        print("  ✓ K1-Only Functions replaced")
    else:
        print("  ✗ K1-Only Functions placeholders not found")
    
    # TSL Functions
    pattern = r"<!-- TSL_ONLY_FUNCTIONS_START -->.*?<!-- TSL_ONLY_FUNCTIONS_END -->"
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f"<!-- TSL_ONLY_FUNCTIONS_START -->\n\n{tsl_func_content}<!-- TSL_ONLY_FUNCTIONS_END -->", md_content, flags=re.DOTALL)
        print("  ✓ TSL-Only Functions replaced")
    else:
        print("  ✗ TSL-Only Functions placeholders not found")
    
    # Shared Constants
    pattern = r"<!-- SHARED_CONSTANTS_START -->.*?<!-- SHARED_CONSTANTS_END -->"
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f"<!-- SHARED_CONSTANTS_START -->\n\n{shared_const_content}<!-- SHARED_CONSTANTS_END -->", md_content, flags=re.DOTALL)
        print("  ✓ Shared Constants replaced")
    else:
        print("  ✗ Shared Constants placeholders not found")
    
    # K1 Constants
    pattern = r"<!-- K1_ONLY_CONSTANTS_START -->.*?<!-- K1_ONLY_CONSTANTS_END -->"
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f"<!-- K1_ONLY_CONSTANTS_START -->\n\n{k1_const_content}<!-- K1_ONLY_CONSTANTS_END -->", md_content, flags=re.DOTALL)
        print("  ✓ K1-Only Constants replaced")
    else:
        print("  ✗ K1-Only Constants placeholders not found")
    
    # TSL Constants
    pattern = r"<!-- TSL_ONLY_CONSTANTS_START -->.*?<!-- TSL_ONLY_CONSTANTS_END -->"
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f"<!-- TSL_ONLY_CONSTANTS_START -->\n\n{tsl_const_content}<!-- TSL_ONLY_CONSTANTS_END -->", md_content, flags=re.DOTALL)
        print("  ✓ TSL-Only Constants replaced")
    else:
        print("  ✗ TSL-Only Constants placeholders not found")
    
    # KOTOR Library Files
    pattern = r"<!-- KOTOR_LIBRARY_START -->.*?<!-- KOTOR_LIBRARY_END -->"
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f"<!-- KOTOR_LIBRARY_START -->\n\n{kotor_lib_content}<!-- KOTOR_LIBRARY_END -->", md_content, flags=re.DOTALL)
        print("  ✓ KOTOR Library Files replaced")
    else:
        print("  ✗ KOTOR Library Files placeholders not found")

    # TSL Library Files
    pattern = r"<!-- TSL_LIBRARY_START -->.*?<!-- TSL_LIBRARY_END -->"
    if re.search(pattern, md_content, re.DOTALL):
        md_content = re.sub(pattern, f"<!-- TSL_LIBRARY_START -->\n\n{tsl_lib_content}<!-- TSL_LIBRARY_END -->", md_content, flags=re.DOTALL)
        print("  ✓ TSL Library Files replaced")
    else:
        print("  ✗ TSL Library Files placeholders not found")

    # Write updated markdown
    print(f"\nWriting updated markdown to {md_path}...")
    md_path.write_text(md_content, encoding="utf-8")
    
    print("Done!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
