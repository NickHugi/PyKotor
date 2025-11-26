"""Script to investigate module structure and understand kit connections.

This script examines:
- LYT files to see room/component structure
- ARE files to understand area properties
- GIT files to see instance data
- RIM contents to find all resources
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[1]
LIBS_PATH = REPO_ROOT / "Libraries"
PYKOTOR_PATH = LIBS_PATH / "PyKotor" / "src"
UTILITY_PATH = LIBS_PATH / "Utility" / "src"

if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))
if str(UTILITY_PATH) not in sys.path:
    sys.path.insert(0, str(UTILITY_PATH))

from pykotor.extract.installation import Installation
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.formats.lyt.lyt_auto import read_lyt
from pykotor.resource.formats.gff.gff_auto import read_gff
from pykotor.resource.type import ResourceType
from pykotor.common.module import Module


def investigate_module(module_name: str, installation: Installation):
    """Investigate a module's structure."""
    print(f"\n{'='*80}")
    print(f"Investigating module: {module_name}")
    print(f"{'='*80}\n")
    
    # Load module
    try:
        module = Module(module_name, installation, use_dot_mod=False)
    except Exception as e:
        print(f"ERROR: Failed to load module '{module_name}': {e}")
        return
    
    # Get RIM files
    rims_path = installation.rims_path()
    modules_path = installation.module_path()
    
    main_rim_path = rims_path / f"{module_name}.rim" if rims_path.exists() else None
    data_rim_path = rims_path / f"{module_name}_s.rim" if rims_path.exists() else None
    
    if main_rim_path is None or not main_rim_path.exists():
        main_rim_path = modules_path / f"{module_name}.rim" if modules_path.exists() else None
    if data_rim_path is None or not data_rim_path.exists():
        data_rim_path = modules_path / f"{module_name}_s.rim" if modules_path.exists() else None
    
    print(f"Main RIM: {main_rim_path}")
    print(f"Data RIM: {data_rim_path}\n")
    
    # Read RIM files
    main_rim = read_rim(main_rim_path) if main_rim_path and main_rim_path.exists() else None
    data_rim = read_rim(data_rim_path) if data_rim_path and data_rim_path.exists() else None
    
    # Collect all resources
    all_resources = {}
    if main_rim:
        for resource in main_rim:
            key = (resource.resname.lower(), resource.restype)
            if key not in all_resources:
                all_resources[key] = resource.data()
    
    if data_rim:
        for resource in data_rim:
            key = (resource.resname.lower(), resource.restype)
            if key not in all_resources:
                all_resources[key] = resource.data()
    
    print(f"Total resources in RIMs: {len(all_resources)}\n")
    
    # Find LYT file
    lyt_data = None
    lyt_resname = None
    for (resname, restype), data in all_resources.items():
        if restype == ResourceType.LYT:
            lyt_data = data
            lyt_resname = resname
            break
    
    if lyt_data:
        print(f"Found LYT file: {lyt_resname}")
        lyt = read_lyt(lyt_data)
        print(f"  Rooms: {len(lyt.rooms)}")
        print(f"  Tracks: {len(lyt.tracks)}")
        print(f"  Obstacles: {len(lyt.obstacles)}")
        print(f"  Door Hooks: {len(lyt.doorhooks)}\n")
        
        print("Room Models:")
        room_models = set()
        for room in lyt.rooms:
            model_name = room.model.lower()
            room_models.add(model_name)
            print(f"  - {model_name} at ({room.position.x:.2f}, {room.position.y:.2f}, {room.position.z:.2f})")
        print()
        
        # Find MDL/MDX/WOK for each room
        print("Room Components (MDL/MDX/WOK):")
        for model_name in sorted(room_models):
            mdl_key = (model_name, ResourceType.MDL)
            mdx_key = (model_name, ResourceType.MDX)
            wok_key = (model_name, ResourceType.WOK)
            
            has_mdl = mdl_key in all_resources
            has_mdx = mdx_key in all_resources
            has_wok = wok_key in all_resources
            
            print(f"  {model_name}:")
            print(f"    MDL: {'✓' if has_mdl else '✗'}")
            print(f"    MDX: {'✓' if has_mdx else '✗'}")
            print(f"    WOK: {'✓' if has_wok else '✗'}")
            
            # Get textures/lightmaps from MDL
            if has_mdl:
                from pykotor.tools.model import iterate_textures, iterate_lightmaps
                mdl_data = all_resources[mdl_key]
                textures = set(iterate_textures(mdl_data))
                lightmaps = set(iterate_lightmaps(mdl_data))
                print(f"    Textures referenced: {len(textures)}")
                print(f"    Lightmaps referenced: {len(lightmaps)}")
                if textures:
                    print(f"      Sample textures: {list(textures)[:5]}")
                if lightmaps:
                    print(f"      Sample lightmaps: {list(lightmaps)[:5]}")
        print()
    else:
        print("WARNING: No LYT file found!\n")
    
    # Find ARE file
    are_data = None
    are_resname = None
    for (resname, restype), data in all_resources.items():
        if restype == ResourceType.ARE:
            are_data = data
            are_resname = resname
            break
    
    if are_data:
        print(f"Found ARE file: {are_resname}")
        are = read_gff(are_data)
        # Check for rooms list
        if are.root.get_list("Rooms"):
            rooms_list = are.root.get_list("Rooms")
            print(f"  ARE Rooms: {len(rooms_list)}")
            for i, room_struct in enumerate(rooms_list):
                room_name = room_struct.get_string("RoomName", "")
                print(f"    Room {i}: {room_name}")
        print()
    
    # Find GIT file
    git_data = None
    git_resname = None
    for (resname, restype), data in all_resources.items():
        if restype == ResourceType.GIT:
            git_data = data
            git_resname = resname
            break
    
    if git_data:
        print(f"Found GIT file: {git_resname}")
        git = read_gff(git_data)
        # Count instances
        door_list = git.root.get_list("Door List") if git.root.exists("Door List") else None
        if door_list:
            print(f"  Doors: {len(door_list)}")
        print()
    
    # Use Module class to get all resources
    print("Module.all_resources() analysis:")
    module_resources = module.all_resources()
    print(f"  Total unique resources: {len(module_resources)}")
    
    # Count by type
    type_counts = {}
    for res_ident, _ in module_resources.items():
        restype = res_ident.restype
        type_counts[restype] = type_counts.get(restype, 0) + 1
    
    print("\n  Resources by type:")
    for restype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"    {restype.extension}: {count}")
    
    # Find all textures and lightmaps
    print("\n  Textures and Lightmaps:")
    textures_found = set()
    lightmaps_found = set()
    
    for res_ident, loc_list in module_resources.items():
        if res_ident.restype in (ResourceType.TPC, ResourceType.TGA):
            resname_lower = str(res_ident.resname).lower()
            if "_lm" in resname_lower or resname_lower.endswith("_lm") or resname_lower.startswith("l_"):
                lightmaps_found.add(res_ident.resname)
            else:
                textures_found.add(res_ident.resname)
    
    print(f"    Textures: {len(textures_found)}")
    print(f"    Lightmaps: {len(lightmaps_found)}")
    
    # Check for TXI files
    txi_count = 0
    for res_ident, _ in module_resources.items():
        if res_ident.restype == ResourceType.TXI:
            txi_count += 1
    
    print(f"    TXI files: {txi_count}")
    
    # Compare with what's in RIMs
    print("\n  Comparison with RIM contents:")
    rim_textures = set()
    rim_lightmaps = set()
    rim_txis = set()
    
    for (resname, restype), _ in all_resources.items():
        if restype == ResourceType.TPC:
            if "_lm" in resname or resname.endswith("_lm") or resname.startswith("l_"):
                rim_lightmaps.add(resname)
            else:
                rim_textures.add(resname)
        elif restype == ResourceType.TGA:
            if "_lm" in resname or resname.endswith("_lm") or resname.startswith("l_"):
                rim_lightmaps.add(resname)
            else:
                rim_textures.add(resname)
        elif restype == ResourceType.TXI:
            rim_txis.add(resname)
    
    print(f"    Textures in RIMs: {len(rim_textures)}")
    print(f"    Lightmaps in RIMs: {len(rim_lightmaps)}")
    print(f"    TXI in RIMs: {len(rim_txis)}")
    
    # Find missing
    module_texture_names = {str(t).lower() for t in textures_found}
    module_lightmap_names = {str(l).lower() for l in lightmaps_found}
    
    missing_textures = module_texture_names - {t.lower() for t in rim_textures}
    missing_lightmaps = module_lightmap_names - {l.lower() for l in rim_lightmaps}
    
    if missing_textures:
        print(f"\n    Missing textures from RIMs ({len(missing_textures)}):")
        for tex in sorted(list(missing_textures))[:10]:
            print(f"      - {tex}")
        if len(missing_textures) > 10:
            print(f"      ... and {len(missing_textures) - 10} more")
    
    if missing_lightmaps:
        print(f"\n    Missing lightmaps from RIMs ({len(missing_lightmaps)}):")
        for lm in sorted(list(missing_lightmaps))[:10]:
            print(f"      - {lm}")
        if len(missing_lightmaps) > 10:
            print(f"      ... and {len(missing_lightmaps) - 10} more")


if __name__ == "__main__":
    k1_path = os.environ.get("K1_PATH")
    if not k1_path:
        print("ERROR: K1_PATH environment variable not set!")
        sys.exit(1)
    
    installation = Installation(k1_path)
    investigate_module("danm13", installation)

