"""Compare generated kit JSON with expected structure from other kits."""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

def main():
    """Compare generated jedienclave JSON with other kit JSONs."""
    generated_json = REPO_ROOT / "tests" / "test_toolset" / "test_files" / "generated_kit" / "jedienclave.json"
    kits_dir = REPO_ROOT / "Tools" / "HolocronToolset" / "src" / "toolset" / "kits" / "kits"
    
    # Load generated JSON
    if not generated_json.exists():
        print("ERROR: Generated JSON not found!")
        return
    
    gen_data = json.loads(generated_json.read_text(encoding="utf-8"))
    print("=== Generated JSON Structure ===")
    print(f"Name: {gen_data.get('name')}")
    print(f"ID: {gen_data.get('id')}")
    print(f"HT: {gen_data.get('ht')}")
    print(f"Version: {gen_data.get('version')}")
    print(f"Components: {len(gen_data.get('components', []))}")
    print(f"Doors: {len(gen_data.get('doors', []))}")
    
    # Compare with other kit JSONs
    print("\n=== Comparison with Other Kits ===")
    for kit_json in kits_dir.glob("*.json"):
        if kit_json.name == "jedienclave.json":
            continue
        
        print(f"\n--- {kit_json.name} ---")
        other_data = json.loads(kit_json.read_text(encoding="utf-8"))
        
        # Check structure
        print(f"  Has 'name': {('name' in other_data)}")
        print(f"  Has 'id': {('id' in other_data)}")
        print(f"  Has 'ht': {('ht' in other_data)}")
        print(f"  Has 'version': {('version' in other_data)}")
        print(f"  Has 'components': {('components' in other_data)}")
        print(f"  Has 'doors': {('doors' in other_data)}")
        print(f"  Components count: {len(other_data.get('components', []))}")
        print(f"  Doors count: {len(other_data.get('doors', []))}")
        
        # Check door structure
        if other_data.get('doors'):
            first_door = other_data['doors'][0]
            print(f"  Door fields: {list(first_door.keys())}")
            if 'width' in first_door and 'height' in first_door:
                print(f"  First door width: {first_door.get('width')}")
                print(f"  First door height: {first_door.get('height')}")
    
    # Check generated JSON structure
    print("\n=== Generated JSON Validation ===")
    issues = []
    
    # Required fields
    required_fields = ['name', 'id', 'ht', 'version']
    for field in required_fields:
        if field not in gen_data:
            issues.append(f"Missing required field: {field}")
    
    # Check doors structure
    if 'doors' not in gen_data:
        issues.append("Missing 'doors' field")
    else:
        for i, door in enumerate(gen_data['doors']):
            if 'utd_k1' not in door:
                issues.append(f"Door {i} missing 'utd_k1'")
            if 'utd_k2' not in door:
                issues.append(f"Door {i} missing 'utd_k2'")
            if 'width' not in door:
                issues.append(f"Door {i} missing 'width'")
            if 'height' not in door:
                issues.append(f"Door {i} missing 'height'")
    
    # Check components structure
    if 'components' not in gen_data:
        issues.append("Missing 'components' field")
    else:
        for i, comp in enumerate(gen_data['components']):
            if 'name' not in comp:
                issues.append(f"Component {i} missing 'name'")
            if 'id' not in comp:
                issues.append(f"Component {i} missing 'id'")
            if 'native' not in comp:
                issues.append(f"Component {i} missing 'native'")
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[OK] All required fields present")
        print("[OK] Structure matches expected format")
    
    # Check door dimensions
    print("\n=== Door Dimensions Analysis ===")
    all_default = True
    for door in gen_data.get('doors', []):
        width = door.get('width', 0)
        height = door.get('height', 0)
        if width != 2.0 or height != 3.0:
            all_default = False
            print(f"  {door.get('utd_k1', 'unknown')}: width={width}, height={height}")
    
    if all_default:
        print("  [WARNING] All doors using default dimensions (2.0, 3.0)")
        print("  [WARNING] This suggests door dimension extraction is not working")
        print("  [WARNING] Reason: 'genericdoors.2da' not found in installation")

if __name__ == "__main__":
    main()

