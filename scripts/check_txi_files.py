"""Check if TXI files exist in installation for specific textures."""

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

missing_txis = [
    "lda_bark04", "lda_flr11", "lda_grass07", "lda_grate01", "lda_ivy01",
    "lda_leaf02", "lda_lite01", "lda_rock06", "lda_sky0001", "lda_sky0002",
    "lda_sky0003", "lda_sky0004", "lda_sky0005", "lda_trim02", "lda_trim03",
    "lda_trim04", "lda_unwal07", "lda_wall02", "lda_wall03", "lda_wall04",
]

print("Checking if TXI files exist in installation:")
for tex_name in missing_txis[:10]:
    locations = inst.locations(
        [ResourceIdentifier(resname=tex_name, restype=ResourceType.TXI)],
        [
            SearchLocation.OVERRIDE,
            SearchLocation.TEXTURES_GUI,
            SearchLocation.TEXTURES_TPA,
            SearchLocation.CHITIN,
        ],
    )
    if locations:
        print(f"  {tex_name}.txi: FOUND")
        for res_ident, loc_list in locations.items():
            for loc in loc_list[:1]:
                print(f"    - {loc.filepath.name} (in {loc.filepath.parent.name})")
    else:
        print(f"  {tex_name}.txi: NOT FOUND")

