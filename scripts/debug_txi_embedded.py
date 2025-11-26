"""Check if TXI files are embedded in TPC files."""

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
from pykotor.resource.formats.tpc import read_tpc

k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
inst = Installation(k1_path)

test_textures = ["lda_bark04", "lda_flr11", "lda_grass07"]

print("Checking if TXI is embedded in TPC files:")
for tex_name in test_textures:
    print(f"\n{tex_name}:")
    
    # First, find the TPC file
    tpc_results = inst.locations(
        [ResourceIdentifier(resname=tex_name, restype=rt) for rt in (ResourceType.TPC, ResourceType.TGA)],
        [
            SearchLocation.OVERRIDE,
            SearchLocation.TEXTURES_GUI,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.CHITIN,
        ],
    )
    
    for res_ident, loc_list in tpc_results.items():
        if loc_list and res_ident.restype == ResourceType.TPC:
            loc = loc_list[0]
            print(f"  Found TPC: {loc.filepath.name}")
            # Read TPC and check for embedded TXI
            try:
                with loc.filepath.open("rb") as f:
                    f.seek(loc.offset)
                    tpc_data = f.read(loc.size)
                tpc = read_tpc(tpc_data)
                if tpc.txi and tpc.txi.strip():
                    print(f"    Embedded TXI: YES ({len(tpc.txi)} chars)")
                else:
                    print(f"    Embedded TXI: NO")
            except Exception as e:
                print(f"    Error reading TPC: {e}")
    
    # Also check standalone TXI
    txi_results = inst.locations(
        [ResourceIdentifier(resname=tex_name, restype=ResourceType.TXI)],
        [
            SearchLocation.OVERRIDE,
            SearchLocation.TEXTURES_GUI,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.CHITIN,
        ],
    )
    for res_ident, loc_list in txi_results.items():
        if loc_list:
            print(f"  Found standalone TXI: {len(loc_list)} locations")
            for loc in loc_list[:2]:
                print(f"    - {loc.filepath.name}")
        else:
            print(f"  Standalone TXI: NOT FOUND (empty list)")

