"""Debug TXI lookup to understand why it's failing."""

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
from pykotor.resource.type import ResourceType

k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
inst = Installation(k1_path)

# Test textures that are failing
test_textures = [
    "lda_bark04", "lda_flr11", "lda_grass07", "lda_grate01", "lda_ivy01",
    "lda_leaf02", "lda_lite01", "lda_rock06", "lda_sky0001", "lda_sky0002",
    "lda_sky0003", "lda_sky0004", "lda_sky0005", "lda_trim02", "lda_trim03",
    "lda_trim04", "lda_unwal07", "lda_wall02", "lda_wall03", "lda_wall04",
]

print("=" * 80)
print("Testing TXI lookup for failing textures")
print("=" * 80)

for tex_name in test_textures[:5]:  # Test first 5
    print(f"\nTesting texture: {tex_name}")
    
    # Test 1: Direct lookup with lowercase
    print(f"  1. Lookup with lowercase '{tex_name}':")
    try:
        results = inst.locations(
            [ResourceIdentifier(resname=tex_name, restype=ResourceType.TXI)],
            [
                SearchLocation.OVERRIDE,
                SearchLocation.TEXTURES_GUI,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.CHITIN,
            ],
        )
        print(f"     Results dict: {results}")
        if results:
            for res_ident, loc_list in results.items():
                print(f"     Found: {res_ident} -> {len(loc_list)} locations")
                print(f"     Location list type: {type(loc_list)}, value: {loc_list}")
                if loc_list:
                    for loc in loc_list[:2]:
                        print(f"       - {loc.filepath.name} (offset: {loc.offset}, size: {loc.size})")
                else:
                    print(f"       WARNING: loc_list is empty or None!")
        else:
            print(f"     No results returned (results is empty dict)")
    except Exception as e:
        print(f"     Exception: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Check if ResourceIdentifier is case-sensitive
    print(f"  2. Check ResourceIdentifier case handling:")
    ri1 = ResourceIdentifier(resname=tex_name, restype=ResourceType.TXI)
    ri2 = ResourceIdentifier(resname=tex_name.upper(), restype=ResourceType.TXI)
    ri3 = ResourceIdentifier(resname=tex_name.capitalize(), restype=ResourceType.TXI)
    print(f"     '{tex_name}' == '{tex_name.upper()}': {ri1 == ri2}")
    print(f"     '{tex_name}' == '{tex_name.capitalize()}': {ri1 == ri3}")
    
    # Test 3: Try with different case variations
    print(f"  3. Try different case variations:")
    for variant in [tex_name, tex_name.upper(), tex_name.capitalize()]:
        try:
            results = inst.locations(
                [ResourceIdentifier(resname=variant, restype=ResourceType.TXI)],
                [
                    SearchLocation.OVERRIDE,
                    SearchLocation.TEXTURES_GUI,
                    SearchLocation.TEXTURES_TPA,
                    SearchLocation.CHITIN,
                ],
            )
            if results:
                print(f"     '{variant}': FOUND")
                break
            else:
                print(f"     '{variant}': NOT FOUND")
        except Exception as e:
            print(f"     '{variant}': Exception - {e}")

