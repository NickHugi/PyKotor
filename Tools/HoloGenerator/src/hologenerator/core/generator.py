"""
Configuration Generator for HoloPatcher

This module provides functionality to generate changes.ini files for HoloPatcher
based on the differences between two KOTOR installations.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

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

from hologenerator.core.differ import KotorDiffer
from hologenerator.core.changes_ini import ChangesIniGenerator

if TYPE_CHECKING:
    from pathlib import Path as PathType


class ConfigurationGenerator:
    """Main class for generating HoloPatcher configuration files."""

    def __init__(self):
        self.differ = KotorDiffer()
        self.generator = ChangesIniGenerator()

    def generate_config(
        self,
        path1: PathType,
        path2: PathType,
        output_path: PathType | None = None,
    ) -> str:
        """Generate a changes.ini configuration from two KOTOR installations.
        
        Args:
        ----
            path1: Path to the first KOTOR installation (original)
            path2: Path to the second KOTOR installation (modified)
            output_path: Optional path to save the generated changes.ini
            
        Returns:
        -------
            str: The generated changes.ini content
        """
        # Run the differ to get changes
        diff_results = self.differ.diff_installations(path1, path2)
        
        # Generate the changes.ini content
        changes_ini_content = self.generator.generate_from_diff(diff_results)
        
        # Save to file if output path provided
        if output_path:
            output_path.write_text(changes_ini_content, encoding='utf-8')
        
        return changes_ini_content
    
    def generate_from_files(
        self,
        file1: PathType,
        file2: PathType,
    ) -> str:
        """Generate a configuration snippet from two individual files.
        
        Args:
        ----
            file1: Path to the first file (original)
            file2: Path to the second file (modified)
            
        Returns:
        -------
            str: The generated changes.ini content snippet
        """
        # Compare the files
        change = self.differ.diff_files(file1, file2)
        
        if not change:
            return ""
        
        # Create a minimal diff result
        from hologenerator.core.differ import DiffResult
        diff_result = DiffResult()
        diff_result.add_change(change)
        
        # Generate the changes.ini content
        return self.generator.generate_from_diff(diff_result)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate changes.ini for HoloPatcher")
    parser.add_argument("path1", help="Path to the first KOTOR installation (original)")
    parser.add_argument("path2", help="Path to the second KOTOR installation (modified)")
    parser.add_argument("-o", "--output", help="Output path for changes.ini file", default="changes.ini")
    
    args = parser.parse_args()
    
    generator = ConfigurationGenerator()
    result = generator.generate_config(Path(args.path1), Path(args.path2), Path(args.output))
    print(f"Generated changes.ini with {len(result.splitlines())} lines")