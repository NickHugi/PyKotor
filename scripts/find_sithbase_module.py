"""Script to find which module contains sithbase components."""
import os
import sys
from pathlib import Path

# Add paths for imports
REPO_ROOT = Path(__file__).parent.parent
PYKOTOR_PATH = REPO_ROOT / "Libraries" / "PyKotor" / "src"
if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))

from pykotor.extract.installation import Installation
from pykotor.resource.formats.rim import read_rim

# Get K1_PATH
K1_PATH = os.getenv("K1_PATH")
if not K1_PATH:
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("K1_PATH="):
                K1_PATH = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

if not K1_PATH or not Path(K1_PATH).exists():
    print(f"ERROR: K1_PATH not set or invalid! (value: {K1_PATH})")
    sys.exit(1)

print(f"Checking installation: {K1_PATH}")
inst = Installation(K1_PATH)

# Components to search for
target_components = ["armory_1", "barracks_1", "control_1", "control_2", "hall_1", "hall_2"]

# Also search for LSI textures (Leviathan - Sith ship)
lsi_textures = ["lsi_floor01b", "lsi_flr03b", "lsi_flr04b", "lsi_win01bmp"]

modules_path = inst.module_path()
rims = [f.stem for f in modules_path.glob("*.rim") if not f.stem.endswith("_s")]

print(f"\nChecking {len(rims)} modules for sithbase components...")
print(f"Target components: {', '.join(target_components)}\n")

found_modules = []
for mod_name in sorted(set(rims)):
    try:
        rim_path = modules_path / f"{mod_name}.rim"
        if not rim_path.exists():
            continue
        
        rim = read_rim(rim_path)
        resnames = [str(r.resref).lower() for r in rim]
        
        # Check if any target components are in this module
        found_components = [comp for comp in target_components if comp in resnames]
        if found_components:
            found_modules.append((mod_name, found_components))
            print(f"  Found in {mod_name}: {', '.join(found_components)}")
    except Exception as e:
        pass

print(f"\n{'='*60}")
if found_modules:
    print(f"Found {len(found_modules)} module(s) with sithbase components:")
    for mod_name, components in found_modules:
        print(f"  {mod_name}: {len(components)} components")
    # Use the module with the most components
    best_match = max(found_modules, key=lambda x: len(x[1]))
    print(f"\nBest match: {best_match[0]} (has {len(best_match[1])} components)")
else:
    print("No modules found with sithbase components in main RIM files")
    print("Trying alternative search in _s.rim files...")
    
    # Try _s.rim files
    for mod_name in sorted(set(rims)):
        try:
            s_rim_path = modules_path / f"{mod_name}_s.rim"
            if not s_rim_path.exists():
                continue
            
            s_rim = read_rim(s_rim_path)
            resnames = [str(r.resref).lower() for r in s_rim]
            
            found_components = [comp for comp in target_components if comp in resnames]
            if found_components:
                found_modules.append((mod_name, found_components))
                print(f"  Found in {mod_name}_s.rim: {', '.join(found_components)}")
        except Exception:
            pass
    
    if not found_modules:
        print("\nStill no matches. Checking for similar component names...")
        # Check for components with similar patterns
        for mod_name in sorted(set(rims))[:30]:
            try:
                rim_path = modules_path / f"{mod_name}.rim"
                s_rim_path = modules_path / f"{mod_name}_s.rim"
                
                all_resnames = []
                if rim_path.exists():
                    rim = read_rim(rim_path)
                    all_resnames.extend([str(r.resref).lower() for r in rim])
                if s_rim_path.exists():
                    s_rim = read_rim(s_rim_path)
                    all_resnames.extend([str(r.resref).lower() for r in s_rim])
                
                # Look for any components with "armory", "barracks", "control", "hall" in name
                matches = [r for r in all_resnames if any(keyword in r for keyword in ["armory", "barracks", "control", "hall", "buffer", "disassembly", "elevator", "generic", "junction", "medical", "reception"])]
                # Also check for LSI textures (Leviathan)
                lsi_matches = [r for r in all_resnames if r.startswith("lsi_")]
                if matches or lsi_matches:
                    print(f"  {mod_name}: Found {len(matches)} components, {len(lsi_matches)} LSI textures (e.g., {matches[0] if matches else lsi_matches[0] if lsi_matches else 'N/A'})")
                    if lsi_matches and not found_modules:
                        # If we find LSI textures, this might be a Leviathan module
                        print(f"    -> Potential Leviathan module (has LSI textures)")
            except Exception:
                pass

