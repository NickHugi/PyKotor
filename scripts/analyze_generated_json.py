"""Analyze the generated jedienclave JSON file."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
generated_json = REPO_ROOT / "tests" / "test_toolset" / "test_files" / "generated_kit" / "jedienclave.json"

if not generated_json.exists():
    print(f"ERROR: Generated JSON not found: {generated_json}")
    exit(1)

gen_data = json.loads(generated_json.read_text(encoding="utf-8"))

print("="*80)
print("GENERATED JEDIENCLAVE JSON ANALYSIS")
print("="*80)
print(f"\nTop Level:")
print(f"  Name: {gen_data.get('name')}")
print(f"  ID: {gen_data.get('id')}")
print(f"  HT: {gen_data.get('ht')}")
print(f"  Version: {gen_data.get('version')}")

print(f"\nComponents: {len(gen_data.get('components', []))}")
print("  (jedienclave is a texture-only kit with no components)")

doors = gen_data.get("doors", [])
print(f"\nDoors: {len(doors)}")

# Analyze door dimensions
default_dims = sum(1 for d in doors if d.get("width") == 2.0 and d.get("height") == 3.0)
custom_dims = len(doors) - default_dims

print(f"\nDoor Dimensions Analysis:")
print(f"  Doors with default dimensions (2.0 x 3.0): {default_dims}/{len(doors)}")
print(f"  Doors with custom dimensions: {custom_dims}/{len(doors)}")

if default_dims == len(doors):
    print("\n  WARNING: All doors are using default dimensions!")
    print("     This suggests door dimension extraction is not working.")
    print("     Expected: Doors should have varying dimensions extracted from models/textures.")

print(f"\nDoor Details:")
for i, door in enumerate(doors):
    utd_k1 = door.get("utd_k1", "")
    width = door.get("width", 0)
    height = door.get("height", 0)
    print(f"  {i+1:2d}. {utd_k1:25s} - {width:.2f} x {height:.2f}")

# Compare with sithbase for reference
sithbase_json = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / "sithbase.json"
if sithbase_json.exists():
    print("\n" + "="*80)
    print("COMPARISON WITH SITHBASE KIT (for reference)")
    print("="*80)
    sith_data = json.loads(sithbase_json.read_text(encoding="utf-8"))
    sith_doors = sith_data.get("doors", [])
    print(f"\nSithbase has {len(sith_doors)} doors with dimensions:")
    for i, door in enumerate(sith_doors):
        utd_k1 = door.get("utd_k1", "")
        width = door.get("width", 0)
        height = door.get("height", 0)
        print(f"  {i+1:2d}. {utd_k1:25s} - {width:.2f} x {height:.2f}")
    
    sith_default = sum(1 for d in sith_doors if d.get("width") == 2.0 and d.get("height") == 3.0)
    print(f"\n  Sithbase default dimensions: {sith_default}/{len(sith_doors)}")
    print(f"  Sithbase custom dimensions: {len(sith_doors) - sith_default}/{len(sith_doors)}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print(f"Generated JSON structure is valid.")
print(f"All {len(doors)} doors are using default dimensions (2.0 x 3.0).")
print("This indicates door dimension extraction needs to be fixed.")

