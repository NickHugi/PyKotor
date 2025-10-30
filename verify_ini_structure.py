"""Verify the generated changes.ini structure against expected format."""
from __future__ import annotations

import re

from pathlib import Path


def verify_ini_structure(ini_path: str) -> dict[str, list[str]]:
    """Verify INI structure and report issues.

    Returns:
        Dictionary of issue categories to list of specific issues
    """
    issues: dict[str, list[str]] = {
        "missing_sections": [],
        "missing_keys": [],
        "malformed_sections": [],
        "empty_required_sections": [],
        "warnings": [],
    }

    ini_file = Path(ini_path)
    if not ini_file.exists():
        issues["missing_sections"].append(f"INI file not found: {ini_path}")
        return issues

    content = ini_file.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Track found sections
    found_sections: set[str] = set()
    current_section: str | None = None
    section_content: dict[str, list[str]] = {}

    for line in lines:
        line_stripped = line.strip()

        # Section header
        if line_stripped.startswith("[") and line_stripped.endswith("]"):
            current_section = line_stripped[1:-1]
            found_sections.add(current_section)
            section_content[current_section] = []
        elif current_section and line_stripped and not line_stripped.startswith(";"):
            section_content[current_section].append(line_stripped)

    # Check for required sections
    required_sections = {
        "Settings": [
            "FileExists", "WindowCaption", "ConfirmMessage", "LogLevel",
            "InstallerMode", "BackupFiles", "PlaintextLog", "LookupGameFolder",
            "LookupGameNumber", "SaveProcessedScripts"
        ],
        "TLKList": [],  # Can be empty but must exist
        "2DAList": [],  # Can be empty but must exist
        "GFFList": [],  # Can be empty but must exist
        "SSFList": [],  # Can be empty but must exist
        "CompileList": [],  # Can be empty but must exist
        "InstallList": [],  # Can be empty but must exist
    }

    for section, required_keys in required_sections.items():
        if section not in found_sections:
            issues["missing_sections"].append(f"Missing required section: [{section}]")
        elif required_keys:
            # Check for required keys in Settings
            section_lines = section_content.get(section, [])
            section_keys = {line.split("=")[0] for line in section_lines if "=" in line}

            for key in required_keys:
                if key not in section_keys:
                    issues["missing_keys"].append(f"[{section}] missing required key: {key}")

    # Check TLK-related sections
    if "TLKList" in found_sections:
        tlk_list_content = section_content.get("TLKList", [])
        # Should have Replace0=append.tlk if there are TLK modifications
        if tlk_list_content:
            has_replace = any("Replace0=" in line for line in tlk_list_content)
            if not has_replace:
                issues["warnings"].append("[TLKList] exists but has no Replace0 entry")

        # Check for append.tlk section
        if "append.tlk" not in found_sections and tlk_list_content:  # Only warn if TLKList has content
            issues["warnings"].append("[append.tlk] section not found but [TLKList] has entries")

    # Check 2DA sections
    if "2DAList" in found_sections:
        twoda_list_content = section_content.get("2DAList", [])
        if twoda_list_content:
            # Parse Table entries from 2DAList
            table_pattern = re.compile(r"Table\d+=(.+\.2da)")
            for line in twoda_list_content:
                match = table_pattern.match(line)
                if match:
                    table_name = match.group(1)
                    if table_name not in found_sections:
                        issues["missing_sections"].append(f"2DA table section missing: [{table_name}]")

    # Check for meaningful 2DA row section names
    row_sections = [s for s in found_sections if s.startswith(("add_row_", "change_row_"))]
    if row_sections:
        issues["malformed_sections"].append(
            f"Found {len(row_sections)} 2DA row sections with generic names (should be table_row_label_0 format)"
        )
        issues["malformed_sections"].extend(row_sections[:5])  # Show first 5 examples

    # Summary
    print("\n" + "=" * 80)
    print("INI STRUCTURE VERIFICATION RESULTS")
    print("=" * 80)
    print(f"INI file: {ini_path}")
    print(f"Total sections found: {len(found_sections)}")
    print(f"Total lines: {len(lines)}")

    for category, issue_list in issues.items():
        if issue_list:
            print(f"\n{category.upper().replace('_', ' ')}:")
            for issue in issue_list:
                print(f"  - {issue}")

    if not any(issues.values()):
        print("\n✓ All checks passed!")
    else:
        print(f"\n✗ Found {sum(len(v) for v in issues.values())} total issues")

    return issues


if __name__ == "__main__":
    import sys

    ini_path = sys.argv[1] if len(sys.argv) > 1 else "tslpatchdata/changes.ini"
    print(f"Verifying INI structure: {ini_path}")

    issues = verify_ini_structure(ini_path)

    # Exit with error if there are critical issues
    has_critical = bool(issues["missing_sections"] or issues["missing_keys"])
    sys.exit(1 if has_critical else 0)

