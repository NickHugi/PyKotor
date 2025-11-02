from __future__ import annotations

import os
import re

from pathlib import Path


def fix_ini_comments(content: str) -> str:
    """Replace # comments with ; comments within ```ini blocks."""
    lines = content.split("\n")
    new_lines: list[str] = []
    in_ini_block = False

    for line in lines:
        this_line = line.rstrip()
        if this_line.strip().startswith("```ini"):
            in_ini_block = True
            new_lines.append(this_line)
        elif this_line.strip().startswith("```") and in_ini_block:
            in_ini_block = False
            new_lines.append(this_line)
        elif in_ini_block:
            # Replace # at start of line (with optional whitespace) with ;
            if re.match(r"^(\s*)# (.+)$", this_line):
                this_line = re.sub(r"^(\s*)# ", r"\1; ", this_line)
            # Replace inline # comments (but be careful not to match markdown headers)
            elif "#" in line and not line.strip().startswith("#"):
                # Replace inline # comments (where # is followed by space and text)
                this_line = re.sub(r"(\S)\s+# ([^#]+)$", r"\1  ; \2", this_line)
            new_lines.append(this_line)
        else:
            new_lines.append(this_line)

    return "\n".join(new_lines)


def process_wiki_files():
    """Process all markdown files in the wiki directory."""
    wiki_dir = Path("wiki")

    # Use scandir for full case-insensitive .md match (cross platform)
    for entry in os.scandir(wiki_dir):
        entry_path: Path = Path(entry.path)
        if not entry.is_file():
            print(f"  Skipping {entry_path.name} (not a file)")
            continue
        if entry_path.suffix.lower() != ".md":
            print(f"  Skipping {entry_path.name} (not markdown)")
            continue
        print(f"Processing {entry_path.name}...")
        content: str = entry_path.read_text(encoding="utf-8")
        new_content: str = fix_ini_comments(content)

        entry_path.write_text(new_content, encoding="utf-8")

        print(f"  Done: {entry_path.name}")


if __name__ == "__main__":
    process_wiki_files()
