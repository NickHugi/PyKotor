"""Investigate where kit resources come from and what references them.

Uses Installation class to find resources across the entire game installation.
"""

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

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from pykotor.extract.installation import Installation, SearchLocation
from pykotor.extract.file import ResourceIdentifier
from pykotor.common.module import Module
from pykotor.tools.model import iterate_lightmaps, iterate_textures
from pykotor.resource.type import ResourceType

k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
inst = Installation(k1_path)
module = Module("danm13", inst, use_dot_mod=False)

# Missing resources to investigate
missing_lms = [
    "m03af_01a_lm13", "m03af_03a_lm13",
    "m03mg_01a_lm13",
    "m10aa_01a_lm13", "m10ac_28a_lm13",
    "m14ab_02a_lm13",
    "m15aa_01a_lm13",
    "m22aa_03a_lm13", "m22ab_12a_lm13",
    "m28ab_19a_lm13",
    "m33ab_01_lm13",
    "m36aa_01_lm13",
    "m44ab_27a_lm13",
]

missing_textures = [
    "h_f_lo01headtest", "i_datapad", "lda_bark04", "lda_flr07", "lda_flr08",
    "lda_flr11", "lda_grass07", "lda_grate01", "lda_ivy01", "lda_leaf02",
    "lda_lite01", "lda_rock06", "lda_sky0001", "lda_sky0002", "lda_sky0003",
    "lda_sky0004", "lda_sky0005", "lda_trim02", "lda_trim03", "lda_trim04",
    "lda_unwal07",
]

print("=" * 80)
print("Investigating missing resources in jedienclave kit")
print("=" * 80)

# 1. Check models in danm13
print("\n1. Checking danm13 models for references...")
all_lightmaps_from_models = set()
all_textures_from_models = set()

for mdl in module.models():
    try:
        mdl_data = mdl.data()
        if mdl_data:
            for lm in iterate_lightmaps(mdl_data):
                all_lightmaps_from_models.add(lm.lower())
            for tex in iterate_textures(mdl_data):
                all_textures_from_models.add(tex.lower())
    except Exception as e:
        pass

print(f"  Found {len(all_lightmaps_from_models)} lightmaps and {len(all_textures_from_models)} textures from danm13 models")

# 2. Check if missing resources exist in installation and where
print("\n2. Checking if missing resources exist in installation...")
print("\nMissing lightmaps:")
for lm in missing_lms:
    locations = inst.locations(
        [ResourceIdentifier(resname=lm, restype=rt) for rt in (ResourceType.TPC, ResourceType.TGA)],
        [
            SearchLocation.OVERRIDE,
            SearchLocation.TEXTURES_GUI,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.CHITIN,
        ],
    )
    if locations:
        print(f"  {lm}:")
        for res_ident, loc_list in locations.items():
            for loc in loc_list[:2]:  # Show first 2 locations
                source = "RIM" if ".rim" in str(loc.filepath).lower() else "BIF" if ".bif" in str(loc.filepath).lower() else "Other"
                print(f"    - {source}: {loc.filepath.name} (in {loc.filepath.parent.name})")
        # Check if referenced by danm13 models
        if lm.lower() in all_lightmaps_from_models:
            print(f"    -> Referenced by danm13 models: YES")
        else:
            print(f"    -> Referenced by danm13 models: NO")
    else:
        print(f"  {lm}: NOT FOUND in installation")

print("\nMissing textures:")
for tex in missing_textures[:10]:  # Check first 10
    locations = inst.locations(
        [ResourceIdentifier(resname=tex, restype=rt) for rt in (ResourceType.TPC, ResourceType.TGA)],
        [
            SearchLocation.OVERRIDE,
            SearchLocation.TEXTURES_GUI,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.CHITIN,
        ],
    )
    if locations:
        print(f"  {tex}:")
        for res_ident, loc_list in locations.items():
            for loc in loc_list[:2]:
                source = "RIM" if ".rim" in str(loc.filepath).lower() else "BIF" if ".bif" in str(loc.filepath).lower() else "Other"
                print(f"    - {source}: {loc.filepath.name} (in {loc.filepath.parent.name})")
        if tex.lower() in all_textures_from_models:
            print(f"    -> Referenced by danm13 models: YES")
        else:
            print(f"    -> Referenced by danm13 models: NO")
    else:
        print(f"  {tex}: NOT FOUND in installation")

# 3. Check what modules these lightmaps belong to
print("\n3. Analyzing lightmap module origins...")
module_lightmaps = {}
for lm in missing_lms:
    # Extract module prefix (e.g., m03af from m03af_01a_lm13)
    parts = lm.split("_")
    if parts:
        module_prefix = parts[0]  # e.g., "m03af"
        if module_prefix not in module_lightmaps:
            module_lightmaps[module_prefix] = []
        module_lightmaps[module_prefix].append(lm)

print("  Lightmaps grouped by module prefix:")
for mod_prefix, lms in sorted(module_lightmaps.items()):
    print(f"    {mod_prefix}: {len(lms)} lightmaps")
    # Try to find if this module exists
    try:
        test_module = Module(mod_prefix, inst, use_dot_mod=False)
        print(f"      -> Module '{mod_prefix}' exists")
    except:
        print(f"      -> Module '{mod_prefix}' not found or invalid")

# 4. Check if these are shared/common resources
print("\n4. Checking if resources are in common/shared locations...")
common_locations = [
    SearchLocation.CHITIN,
    SearchLocation.TEXTURES_TPA,
    SearchLocation.TEXTURES_GUI,
]

for lm in missing_lms[:3]:  # Check first 3
    print(f"\n  {lm}:")
    for search_loc in common_locations:
        locations = inst.locations(
            [ResourceIdentifier(resname=lm, restype=rt) for rt in (ResourceType.TPC, ResourceType.TGA)],
            [search_loc],
        )
        if locations:
            print(f"    Found in {search_loc.name}")
            for res_ident, loc_list in locations.items():
                for loc in loc_list[:1]:
                    print(f"      - {loc.filepath.name}")

# 5. Check sithbase "always" folder to understand its purpose
print("\n5. Checking sithbase 'always' folder...")
sithbase_always = Path("Tools/HolocronToolset/src/toolset/kits/kits/sithbase/always")
if sithbase_always.exists():
    always_files = list(sithbase_always.iterdir())
    print(f"  Found {len(always_files)} files in sithbase/always:")
    for f in always_files[:10]:
        print(f"    - {f.name}")
        # Check if this resource exists in installation
        try:
            res_ident = ResourceIdentifier.from_path(f.name)
            locations = inst.locations(
                [ResourceIdentifier(resname=res_ident.resname, restype=res_ident.restype)],
                [
                    SearchLocation.OVERRIDE,
                    SearchLocation.CHITIN,
                ],
            )
            if locations:
                for res_id, loc_list in locations.items():
                    for loc in loc_list[:1]:
                        source = "RIM" if ".rim" in str(loc.filepath).lower() else "BIF" if ".bif" in str(loc.filepath).lower() else "Other"
                        print(f"      -> Found in installation: {source} ({loc.filepath.parent.name})")
        except:
            pass

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nMissing lightmaps NOT referenced by danm13 models: {len([lm for lm in missing_lms if lm.lower() not in all_lightmaps_from_models])}")
print(f"Missing textures NOT referenced by danm13 models: {len([tex for tex in missing_textures if tex.lower() not in all_textures_from_models])}")

print("\nConclusion:")
print("  - These resources are likely shared/common resources that were manually")
print("    included in the jedienclave kit for convenience, even though they're")
print("    not directly referenced by danm13 models.")
print("  - They may be used by other modules that share resources with danm13,")
print("    or they may be common textures/lightmaps used across multiple areas.")
