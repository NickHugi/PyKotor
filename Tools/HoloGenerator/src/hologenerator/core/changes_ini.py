"""
Changes.ini generator for HoloPatcher.

This module converts diff results into HoloPatcher-compatible changes.ini format.
"""

from __future__ import annotations

import re
import sys
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Add the PyKotor library to the path
if getattr(sys, "frozen", False) is False:
    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = Path(__file__).parents[5] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)

from pykotor.resource.formats import gff, twoda, tlk, ssf

if TYPE_CHECKING:
    from hologenerator.core.differ import DiffResult, FileChange


class ChangesIniGenerator:
    """Generates changes.ini files from diff results."""
    
    def __init__(self):
        self.gff_extensions = set(gff.GFFContent.get_extensions())
    
    def generate_from_diff(self, diff_result: DiffResult) -> str:
        """Generate a changes.ini file from diff results.
        
        Args:
        ----
            diff_result: The diff results to convert
            
        Returns:
        -------
            str: The generated changes.ini content
        """
        ini_sections = {}
        
        # Process each change
        for change in diff_result.changes:
            if change.change_type == "added":
                self._process_added_file(change, ini_sections)
            elif change.change_type == "modified":
                self._process_modified_file(change, ini_sections)
            # Note: Removed files are typically handled by the mod overriding them
        
        # Generate the INI content
        return self._generate_ini_content(ini_sections)
    
    def _process_added_file(self, change: FileChange, ini_sections: dict[str, Any]):
        """Process an added file change."""
        # Added files go to InstallList
        if "InstallList" not in ini_sections:
            ini_sections["InstallList"] = {}
        
        # Determine the destination folder
        path_parts = Path(change.path).parts
        if len(path_parts) > 1:
            destination = path_parts[0]  # Override, Modules, etc.
            filename = str(Path(*path_parts[1:]))
        else:
            destination = "Override"
            filename = change.path
        
        # Add to install list
        install_key = f"File{len(ini_sections['InstallList']) + 1}"
        ini_sections["InstallList"][install_key] = destination
        
        # Create file section
        ini_sections[destination] = ini_sections.get(destination, {})
        ini_sections[destination][f"File{len(ini_sections[destination]) + 1}"] = filename
    
    def _process_modified_file(self, change: FileChange, ini_sections: dict[str, Any]):
        """Process a modified file change."""
        if change.resource_type in self.gff_extensions:
            self._process_gff_change(change, ini_sections)
        elif change.resource_type == "2da":
            self._process_2da_change(change, ini_sections)
        elif change.resource_type == "tlk":
            self._process_tlk_change(change, ini_sections)
        elif change.resource_type == "ssf":
            self._process_ssf_change(change, ini_sections)
        else:
            # For other file types, treat as replacement
            self._process_replacement_file(change, ini_sections)
    
    def _process_gff_change(self, change: FileChange, ini_sections: dict[str, Any]):
        """Process GFF file changes."""
        if "GFFList" not in ini_sections:
            ini_sections["GFFList"] = {}
        
        filename = Path(change.path).name
        gff_key = f"File{len(ini_sections['GFFList']) + 1}"
        ini_sections["GFFList"][gff_key] = filename
        
        # Create GFF file section
        ini_sections[filename] = {}
        
        # Parse diff to extract field changes
        if change.diff_lines:
            self._parse_gff_diff(change.diff_lines, ini_sections[filename])
    
    def _process_2da_change(self, change: FileChange, ini_sections: dict[str, Any]):
        """Process 2DA file changes."""
        if "2DAList" not in ini_sections:
            ini_sections["2DAList"] = {}
        
        filename = Path(change.path).name
        twoda_key = f"File{len(ini_sections['2DAList']) + 1}"
        ini_sections["2DAList"][twoda_key] = filename
        
        # Create 2DA file section
        ini_sections[filename] = {}
        
        # Parse diff to extract row/column changes
        if change.diff_lines:
            self._parse_2da_diff(change.diff_lines, ini_sections[filename])
    
    def _process_tlk_change(self, change: FileChange, ini_sections: dict[str, Any]):
        """Process TLK file changes."""
        if "TLKList" not in ini_sections:
            ini_sections["TLKList"] = {}
        
        # Parse diff to extract string changes
        if change.diff_lines:
            self._parse_tlk_diff(change.diff_lines, ini_sections["TLKList"])
    
    def _process_ssf_change(self, change: FileChange, ini_sections: dict[str, Any]):
        """Process SSF file changes."""
        if "SSFList" not in ini_sections:
            ini_sections["SSFList"] = {}
        
        filename = Path(change.path).name
        ssf_key = f"File{len(ini_sections['SSFList']) + 1}"
        ini_sections["SSFList"][ssf_key] = filename
        
        # Create SSF file section
        ini_sections[filename] = {}
        
        # Parse diff to extract sound changes
        if change.diff_lines:
            self._parse_ssf_diff(change.diff_lines, ini_sections[filename])
    
    def _process_replacement_file(self, change: FileChange, ini_sections: dict[str, Any]):
        """Process files that need to be replaced entirely."""
        if "InstallList" not in ini_sections:
            ini_sections["InstallList"] = {}
        
        path_parts = Path(change.path).parts
        if len(path_parts) > 1:
            destination = path_parts[0]
            filename = str(Path(*path_parts[1:]))
        else:
            destination = "Override"
            filename = change.path
        
        # Add to install list with replace flag
        install_key = f"Replace{len(ini_sections['InstallList']) + 1}"
        ini_sections["InstallList"][install_key] = destination
        
        # Create file section
        ini_sections[destination] = ini_sections.get(destination, {})
        ini_sections[destination][f"Replace{len(ini_sections[destination]) + 1}"] = filename
    
    def _parse_gff_diff(self, diff_lines: list[str], gff_section: dict[str, Any]):
        """Parse GFF diff lines to extract field modifications."""
        # This is a simplified implementation
        # In a full implementation, this would parse the actual GFF structure changes
        modification_counter = 1
        
        for line in diff_lines:
            if line.startswith('+ ') or line.startswith('- '):
                # Simple field modification detection
                field_key = f"ModifyField{modification_counter}"
                gff_section[field_key] = f"FieldModification{modification_counter}"
                
                # Create field modification section
                # This would need more sophisticated parsing in practice
                modification_counter += 1
    
    def _parse_2da_diff(self, diff_lines: list[str], twoda_section: dict[str, Any]):
        """Parse 2DA diff lines to extract row/column modifications."""
        modification_counter = 1
        
        for line in diff_lines:
            if line.startswith('+ ') or line.startswith('- '):
                # Detect row changes
                if '\t' in line:  # Tab-separated 2DA data
                    row_key = f"ChangeRow{modification_counter}"
                    twoda_section[row_key] = f"RowModification{modification_counter}"
                    modification_counter += 1
    
    def _parse_tlk_diff(self, diff_lines: list[str], tlk_section: dict[str, Any]):
        """Parse TLK diff lines to extract string modifications."""
        for line in diff_lines:
            if line.startswith('+ ') and 'Entry' in line:
                # Extract entry number and text
                match = re.search(r'Entry (\d+):', line)
                if match:
                    entry_num = match.group(1)
                    # This would need more sophisticated parsing
                    tlk_section[f"StrRef{entry_num}"] = "Modified"
    
    def _parse_ssf_diff(self, diff_lines: list[str], ssf_section: dict[str, Any]):
        """Parse SSF diff lines to extract sound modifications."""
        for line in diff_lines:
            if line.startswith('+ ') or line.startswith('- '):
                # Extract sound name and ResRef
                if ':' in line:
                    parts = line[2:].split(':', 1)  # Remove +/- prefix
                    if len(parts) == 2:
                        sound_name = parts[0].strip()
                        resref = parts[1].strip()
                        ssf_section[sound_name] = resref
    
    def _generate_ini_content(self, ini_sections: dict[str, Any]) -> str:
        """Generate the final INI content from sections."""
        output = StringIO()
        
        # Write settings section first
        output.write("[Settings]\n")
        output.write("WindowCaption=Generated Mod Configuration\n")
        output.write("ConfirmMessage=This mod was generated from a KOTOR installation diff.\n")
        output.write("\n")
        
        # Write each section
        for section_name, section_data in ini_sections.items():
            output.write(f"[{section_name}]\n")
            
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    output.write(f"{key}={value}\n")
            else:
                output.write(f"{section_data}\n")
            
            output.write("\n")
        
        return output.getvalue()


class GFFPatcher:
    """Helper class for generating GFF patches."""
    
    @staticmethod
    def generate_field_patch(field_path: str, old_value: Any, new_value: Any) -> dict[str, str]:
        """Generate a field modification patch."""
        return {
            "FieldPath": field_path,
            "FieldType": GFFPatcher._determine_field_type(new_value),
            "Value": str(new_value)
        }
    
    @staticmethod
    def _determine_field_type(value: Any) -> str:
        """Determine the GFF field type from a value."""
        if isinstance(value, bool):
            return "UINT8"
        elif isinstance(value, int):
            if -32768 <= value <= 32767:
                return "INT16"
            elif 0 <= value <= 65535:
                return "UINT16"
            elif -2147483648 <= value <= 2147483647:
                return "INT32"
            else:
                return "UINT32"
        elif isinstance(value, float):
            return "FLOAT"
        elif isinstance(value, str):
            return "EXOSTRING"
        else:
            return "EXOSTRING"  # Default fallback


class TwoDAPatcher:
    """Helper class for generating 2DA patches."""
    
    @staticmethod
    def generate_row_patch(row_index: int, column: str, old_value: str, new_value: str) -> dict[str, str]:
        """Generate a row modification patch."""
        return {
            "RowIndex": str(row_index),
            "ColumnLabel": column,
            "Value": new_value
        }
    
    @staticmethod
    def generate_add_row_patch(row_data: dict[str, str]) -> dict[str, str]:
        """Generate an add row patch."""
        return {
            "RowLabel": row_data.get("RowLabel", "NewRow"),
            **{f"Col_{col}": value for col, value in row_data.items() if col != "RowLabel"}
        }