#!/usr/bin/env python3
"""
HoloGenerator Command Line Interface

Main entry point for the HoloGenerator tool that creates changes.ini files
for HoloPatcher from KOTOR installation differences.
"""

from __future__ import annotations

import sys
from argparse import ArgumentParser
from pathlib import Path

# Add the PyKotor library to the path
if getattr(sys, "frozen", False) is False:
    def update_sys_path(path):
        working_dir = str(path)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.append(working_dir)

    pykotor_path = Path(__file__).parents[4] / "Libraries" / "PyKotor" / "src" / "pykotor"
    if pykotor_path.exists():
        update_sys_path(pykotor_path.parent)

from hologenerator.core.generator import ConfigurationGenerator

CURRENT_VERSION = "1.0.0"


def main():
    """Main entry point for the CLI."""
    print(f"HoloGenerator version {CURRENT_VERSION}")
    print("KOTOR Configuration Generator for HoloPatcher")
    print()
    
    parser = ArgumentParser(
        description="Generate changes.ini files for HoloPatcher from KOTOR installation differences"
    )
    
    # Positional arguments for installation paths
    parser.add_argument(
        "path1", 
        nargs="?",
        help="Path to the first KOTOR installation (original)"
    )
    parser.add_argument(
        "path2", 
        nargs="?",
        help="Path to the second KOTOR installation (modified)"
    )
    
    # Options
    parser.add_argument(
        "-o", "--output",
        help="Output path for changes.ini file",
        default="changes.ini"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI interface"
    )
    parser.add_argument(
        "--file-mode",
        action="store_true",
        help="Compare individual files instead of installations"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"HoloGenerator {CURRENT_VERSION}"
    )
    
    args = parser.parse_args()
    
    # Handle GUI mode
    if args.gui:
        try:
            from hologenerator.gui.main import main as gui_main
            gui_main()
            return
        except ImportError as e:
            print(f"GUI mode not available: {e}")
            print("Please ensure tkinter is installed.")
            sys.exit(1)
    
    # Validate arguments for CLI mode
    if not args.path1:
        path1 = input("Path to the first KOTOR installation (original): ").strip()
        if not path1:
            print("Error: First path is required")
            sys.exit(1)
        args.path1 = path1
    
    if not args.path2:
        path2 = input("Path to the second KOTOR installation (modified): ").strip()
        if not path2:
            print("Error: Second path is required")
            sys.exit(1)
        args.path2 = path2
    
    # Convert to Path objects
    path1 = Path(args.path1).resolve()
    path2 = Path(args.path2).resolve()
    output_path = Path(args.output)
    
    # Validate paths
    if not path1.exists():
        print(f"Error: Path '{path1}' does not exist")
        sys.exit(1)
    
    if not path2.exists():
        print(f"Error: Path '{path2}' does not exist")
        sys.exit(1)
    
    # Initialize generator
    generator = ConfigurationGenerator()
    
    try:
        print(f"Comparing:")
        print(f"  Original: {path1}")
        print(f"  Modified: {path2}")
        print()
        
        if args.file_mode:
            print("Generating configuration from individual files...")
            result = generator.generate_from_files(path1, path2)
        else:
            print("Generating configuration from installations...")
            result = generator.generate_config(path1, path2, output_path)
        
        if result:
            lines_count = len(result.splitlines())
            print(f"Configuration generated successfully!")
            print(f"Output saved to: {output_path}")
            print(f"Lines generated: {lines_count}")
            
            # Show a preview of the first few lines
            print("\nPreview:")
            print("-" * 40)
            lines = result.splitlines()
            for line in lines[:10]:
                print(line)
            if len(lines) > 10:
                print(f"... and {len(lines) - 10} more lines")
        else:
            print("No differences found between the paths.")
            print("The installations appear to be identical.")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()