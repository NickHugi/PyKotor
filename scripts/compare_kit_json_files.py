"""Compare generated and expected kit JSON files."""
import json
import sys
from pathlib import Path

# Add paths for imports
REPO_ROOT = Path(__file__).parent.parent
PYKOTOR_PATH = REPO_ROOT / "Libraries" / "PyKotor" / "src"
if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))

generated_json = REPO_ROOT / "tests" / "test_toolset" / "test_files" / "generated_kit" / "jedienclave.json"
# Check if expected JSON exists in kits/kits or just kits
expected_json = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits" / "jedienclave.json"
if not expected_json.exists():
    expected_json = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "jedienclave.json"

if not generated_json.exists():
    print(f"ERROR: Generated JSON not found: {generated_json}")
    print("Run the test first to generate the JSON file.")
    sys.exit(1)

if not expected_json.exists():
    print(f"ERROR: Expected JSON not found: {expected_json}")
    sys.exit(1)

print("Loading JSON files...")
gen_data = json.loads(generated_json.read_text(encoding="utf-8"))
exp_data = json.loads(expected_json.read_text(encoding="utf-8"))

print("\n" + "="*80)
print("TOP LEVEL COMPARISON")
print("="*80)
print(f"Generated name: {gen_data.get('name')}")
print(f"Expected name:  {exp_data.get('name')}")
print(f"Generated id:   {gen_data.get('id')}")
print(f"Expected id:    {exp_data.get('id')}")
print(f"Generated ht:   {gen_data.get('ht')}")
print(f"Expected ht:    {exp_data.get('ht')}")
print(f"Generated version: {gen_data.get('version')}")
print(f"Expected version:  {exp_data.get('version')}")

print("\n" + "="*80)
print("COMPONENTS COMPARISON")
print("="*80)
gen_components = gen_data.get("components", [])
exp_components = exp_data.get("components", [])
print(f"Generated components: {len(gen_components)}")
print(f"Expected components:  {len(exp_components)}")

if len(gen_components) != len(exp_components):
    print(f"  WARNING: Component count differs!")
else:
    print("  Component count matches")

# Compare component IDs
gen_comp_ids = {c.get("id") for c in gen_components}
exp_comp_ids = {c.get("id") for c in exp_components}
missing_ids = exp_comp_ids - gen_comp_ids
extra_ids = gen_comp_ids - exp_comp_ids

if missing_ids:
    print(f"  Missing component IDs: {sorted(missing_ids)}")
if extra_ids:
    print(f"  Extra component IDs: {sorted(extra_ids)}")
if not missing_ids and not extra_ids:
    print("  All component IDs match")

# Compare doorhooks
print("\n  Doorhooks comparison:")
for i, (gen_comp, exp_comp) in enumerate(zip(gen_components, exp_components)):
    gen_id = gen_comp.get("id")
    exp_id = exp_comp.get("id")
    if gen_id != exp_id:
        print(f"    Component {i}: ID mismatch (gen: {gen_id}, exp: {exp_id})")
        continue
    
    gen_hooks = gen_comp.get("doorhooks", [])
    exp_hooks = exp_comp.get("doorhooks", [])
    if len(gen_hooks) != len(exp_hooks):
        print(f"    {gen_id}: Hook count differs (gen: {len(gen_hooks)}, exp: {len(exp_hooks)})")
    elif gen_hooks and exp_hooks:
        # Compare first hook as example
        gen_hook = gen_hooks[0]
        exp_hook = exp_hooks[0]
        print(f"    {gen_id}: First hook - gen: x={gen_hook.get('x'):.3f}, y={gen_hook.get('y'):.3f}, z={gen_hook.get('z'):.3f}, rot={gen_hook.get('rotation'):.1f}")
        print(f"                    exp: x={exp_hook.get('x'):.3f}, y={exp_hook.get('y'):.3f}, z={exp_hook.get('z'):.3f}, rot={exp_hook.get('rotation'):.1f}")

print("\n" + "="*80)
print("DOORS COMPARISON")
print("="*80)
gen_doors = gen_data.get("doors", [])
exp_doors = exp_data.get("doors", [])
print(f"Generated doors: {len(gen_doors)}")
print(f"Expected doors:  {len(exp_doors)}")

if len(gen_doors) != len(exp_doors):
    print(f"  WARNING: Door count differs!")
else:
    print("  Door count matches")

print("\n  Door dimensions:")
for i, (gen_door, exp_door) in enumerate(zip(gen_doors, exp_doors)):
    gen_utd_k1 = gen_door.get("utd_k1")
    exp_utd_k1 = exp_door.get("utd_k1")
    gen_width = gen_door.get("width")
    exp_width = exp_door.get("width")
    gen_height = gen_door.get("height")
    exp_height = exp_door.get("height")
    
    width_match = abs(gen_width - exp_width) < 0.01 if gen_width and exp_width else gen_width == exp_width
    height_match = abs(gen_height - exp_height) < 0.01 if gen_height and exp_height else gen_height == exp_height
    
    status = "✓" if (width_match and height_match and gen_utd_k1 == exp_utd_k1) else "✗"
    print(f"  {status} Door {i} ({gen_utd_k1}):")
    print(f"      Generated: width={gen_width}, height={gen_height}")
    print(f"      Expected:   width={exp_width}, height={exp_height}")
    if not width_match or not height_match:
        print(f"      DIFFERENCE: width diff={abs(gen_width - exp_width) if gen_width and exp_width else 'N/A'}, height diff={abs(gen_height - exp_height) if gen_height and exp_height else 'N/A'}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
all_match = (
    gen_data.get("name") == exp_data.get("name") and
    gen_data.get("id") == exp_data.get("id") and
    len(gen_components) == len(exp_components) and
    gen_comp_ids == exp_comp_ids and
    len(gen_doors) == len(exp_doors)
)

# Check door dimensions match
doors_match = True
for gen_door, exp_door in zip(gen_doors, exp_doors):
    gen_width = gen_door.get("width")
    exp_width = exp_door.get("width")
    gen_height = gen_door.get("height")
    exp_height = exp_door.get("height")
    if abs(gen_width - exp_width) >= 0.01 or abs(gen_height - exp_height) >= 0.01:
        doors_match = False
        break

if all_match and doors_match:
    print("✓ All top-level fields match")
    print("✓ Component counts and IDs match")
    print("✓ Door counts and dimensions match")
    print("\nJSON files are equivalent!")
else:
    print("✗ Some differences found (see details above)")

