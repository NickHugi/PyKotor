#!/usr/bin/env python3
"""Extract GFF generic type sections from GFF-File-Format.md into separate files."""

import re
from pathlib import Path

wiki_dir = Path("wiki")
gff_file = wiki_dir / "GFF-File-Format.md"

# Map section headers to their start lines (from grep output)
section_starts = {
    "ARE": 385,
    "DLG": 674,
    "GIT": 818,
    "GUI": 1130,
    "IFO": 1658,
    "JRL": 1930,
    "PTH": 1988,
    "UTC": 2025,
    "UTD": 2194,
    "UTE": 2414,
    "UTI": 2497,
    "UTM": 2733,
    "UTP": 2741,
    "UTS": 3005,
    "UTT": 3079,
    "UTW": 3163,
}

# Read the full file
with open(gff_file, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Create output files for each section
section_names = list(section_starts.keys())
section_names.append("END")  # Add end marker

for i, section_name in enumerate(section_names[:-1]):
    start_line = section_starts[section_name] - 1  # Convert to 0-based index
    next_section = section_names[i + 1]
    
    if next_section != "END":
        end_line = section_starts[next_section] - 1
    else:
        end_line = len(lines)  # End of file
    
    # Extract section content
    section_lines = lines[start_line:end_line]
    section_content = "".join(section_lines)
    
    # Remove "Implementation Details" section if it exists (should only be in UTW)
    if "## Implementation Details" in section_content:
        section_content = section_content.split("## Implementation Details")[0].rstrip()
        # Remove trailing "---" if present
        section_content = re.sub(r"\n---+?\s*$", "", section_content, flags=re.MULTILINE)
    
    # Extract the title from the first line (e.g., "### ARE (Area)" -> "ARE (Area)")
    lines_list = section_content.split("\n")
    first_header_line = None
    for i, line in enumerate(lines_list):
        if line.strip().startswith("### "):
            first_header_line = i
            break
    
    if first_header_line is not None:
        title_line = lines_list[first_header_line]
        full_title = re.match(r"^### (.+)$", title_line).group(1)
        
        # Change the first ### header to # for page title
        lines_list[first_header_line] = f"# {full_title}"
        
        # Change all other headers: #### becomes ##, ### becomes ##
        for i in range(len(lines_list)):
            if i != first_header_line:
                if lines_list[i].strip().startswith("#### "):
                    lines_list[i] = lines_list[i].replace("#### ", "## ", 1)
                elif lines_list[i].strip().startswith("### "):
                    lines_list[i] = lines_list[i].replace("### ", "## ", 1)
        
        # Rebuild content
        section_content = "\n".join(lines_list)
        
        # Add link back to main GFF file right after the title
        section_content = section_content.replace(
            f"# {full_title}\n",
            f"# {full_title}\n\nPart of the [GFF File Format Documentation](GFF-File-Format).\n\n",
            1
        )
    else:
        # Fallback
        section_content = re.sub(r"^### ", "## ", section_content, flags=re.MULTILINE)
    
    # Determine file name
    if section_name == "DLG":
        filename = "GFF-DLG.md"
    elif section_name == "GIT":
        filename = "GFF-GIT.md"
    elif section_name == "GUI":
        filename = "GFF-GUI.md"
    elif section_name == "IFO":
        filename = "GFF-IFO.md"
    elif section_name == "JRL":
        filename = "GFF-JRL.md"
    elif section_name == "PTH":
        filename = "GFF-PTH.md"
    else:
        filename = f"GFF-{section_name}.md"
    
    output_file = wiki_dir / filename
    
    # Write the file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(section_content)
    
    print(f"Created {filename} (lines {start_line+1}-{end_line})")

