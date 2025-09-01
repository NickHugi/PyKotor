#!/usr/bin/env python3
"""
Integration test demonstrating the configuration generator functionality.

This script creates mock KOTOR installation directories and demonstrates
the complete workflow from diff to changes.ini generation.
"""

from __future__ import annotations

import sys
import tempfile
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

from kotordiff.config_generator import ConfigurationGenerator
from kotordiff.differ import DiffResult, FileChange


def create_mock_kotor_install(base_path: Path, name: str) -> Path:
    """Create a mock KOTOR installation directory."""
    install_path = base_path / name
    install_path.mkdir(exist_ok=True)
    
    # Create essential KOTOR files
    (install_path / "chitin.key").touch()
    (install_path / "dialog.tlk").write_text("Mock TLK content", encoding='utf-8')
    
    # Create directories
    (install_path / "Override").mkdir(exist_ok=True)
    (install_path / "Modules").mkdir(exist_ok=True)
    (install_path / "Lips").mkdir(exist_ok=True)
    
    # Create some sample files
    (install_path / "Override" / "test.utc").write_text("Mock UTC content", encoding='utf-8')
    (install_path / "Override" / "test.2da").write_text("2DA V2.b\n\n\tcol1\tcol2\n0\tvalue1\tvalue2", encoding='utf-8')
    
    return install_path


def create_modified_install(original_path: Path, modified_path: Path):
    """Create a modified version of the original installation."""
    import shutil
    
    # Copy original to modified
    if modified_path.exists():
        shutil.rmtree(modified_path)
    shutil.copytree(original_path, modified_path)
    
    # Make some modifications
    # 1. Modify an existing file
    (modified_path / "Override" / "test.utc").write_text("Modified UTC content", encoding='utf-8')
    
    # 2. Add a new file
    (modified_path / "Override" / "newfile.uti").write_text("New UTI content", encoding='utf-8')
    
    # 3. Modify 2DA file
    (modified_path / "Override" / "test.2da").write_text("2DA V2.b\n\n\tcol1\tcol2\tcol3\n0\tvalue1\tvalue2\tnewvalue\n1\tnew1\tnew2\tnew3", encoding='utf-8')


def demonstrate_config_generation():
    """Demonstrate the complete configuration generation process."""
    print("KOTOR Configuration Generator - Integration Test")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        print("1. Creating mock KOTOR installations...")
        original_path = create_mock_kotor_install(base_path, "original_kotor")
        modified_path = base_path / "modified_kotor"
        create_modified_install(original_path, modified_path)
        
        print(f"   Original: {original_path}")
        print(f"   Modified: {modified_path}")
        
        print("\n2. Running configuration generator...")
        generator = ConfigurationGenerator()
        
        output_path = base_path / "changes.ini"
        try:
            result = generator.generate_config(original_path, modified_path, output_path)
            
            print(f"   Configuration generated successfully!")
            print(f"   Output file: {output_path}")
            print(f"   Content length: {len(result)} characters")
            print(f"   Number of lines: {len(result.splitlines())}")
            
            print("\n3. Generated changes.ini content:")
            print("-" * 30)
            print(result)
            print("-" * 30)
            
            print("\n4. Analyzing generated configuration...")
            lines = result.splitlines()
            sections = [line for line in lines if line.startswith('[') and line.endswith(']')]
            print(f"   Found {len(sections)} sections: {', '.join(sections)}")
            
            if "[InstallList]" in result:
                print("   ✓ InstallList section generated (for new files)")
            if "[GFFList]" in result:
                print("   ✓ GFFList section generated (for modified GFF files)")
            if "[2DAList]" in result:
                print("   ✓ 2DAList section generated (for modified 2DA files)")
            
            print("\n5. Validation complete!")
            print("   The generated changes.ini should be compatible with HoloPatcher")
            
        except Exception as e:
            print(f"   Error during generation: {e}")
            raise


def demonstrate_differ_only():
    """Demonstrate just the differ functionality."""
    print("\nDemonstrating differ functionality separately...")
    print("=" * 40)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        base_path = Path(tmpdir)
        
        # Create test installations
        original_path = create_mock_kotor_install(base_path, "original")
        modified_path = base_path / "modified"
        create_modified_install(original_path, modified_path)
        
        # Test the differ
        from kotordiff.differ import KotorDiffer
        differ = KotorDiffer()
        
        print("Running diff analysis...")
        diff_result = differ.diff_installations(original_path, modified_path)
        
        print(f"Found {len(diff_result.changes)} changes:")
        for i, change in enumerate(diff_result.changes, 1):
            print(f"  {i}. {change.path} ({change.change_type}) - {change.resource_type}")
            if change.diff_lines:
                print(f"     Diff lines: {len(change.diff_lines)}")
        
        if diff_result.errors:
            print(f"Errors encountered: {len(diff_result.errors)}")
            for error in diff_result.errors:
                print(f"  - {error}")


def demonstrate_ini_generator():
    """Demonstrate the INI generator with mock data."""
    print("\nDemonstrating INI generator with mock data...")
    print("=" * 40)
    
    from kotordiff.generators.changes_ini import ChangesIniGenerator
    
    # Create mock diff results
    diff_result = DiffResult()
    
    # Add some mock changes
    diff_result.add_change(FileChange(
        path="Override/test.utc",
        change_type="modified",
        resource_type="utc",
        diff_lines=["- old field", "+ new field"]
    ))
    
    diff_result.add_change(FileChange(
        path="Override/newfile.uti",
        change_type="added",
        resource_type="uti"
    ))
    
    diff_result.add_change(FileChange(
        path="Override/test.2da",
        change_type="modified",
        resource_type="2da",
        diff_lines=["+ 1\tnew1\tnew2\tnew3"]
    ))
    
    # Generate INI
    generator = ChangesIniGenerator()
    ini_content = generator.generate_from_diff(diff_result)
    
    print("Generated INI content:")
    print("-" * 20)
    print(ini_content)
    print("-" * 20)


if __name__ == "__main__":
    try:
        demonstrate_differ_only()
        demonstrate_ini_generator()
        demonstrate_config_generation()
        
        print("\n" + "=" * 50)
        print("✓ All demonstrations completed successfully!")
        print("✓ The configuration generator is working as expected!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)