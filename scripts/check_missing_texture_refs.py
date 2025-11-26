"""Check if missing textures are referenced by models or in module resources."""

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

from pykotor.extract.installation import Installation
from pykotor.common.module import Module
from pykotor.tools.model import iterate_textures
from pykotor.resource.type import ResourceType

k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
inst = Installation(k1_path)
module = Module("danm13", inst, use_dot_mod=False)

missing = ["p_carthh01", "plc_chair1", "p_bastillah01", "pheyea", "w_vbroswrd01"]

print("Checking if missing textures are referenced by models:")
all_texture_refs = set()
for model_resource in module.models():
    try:
        model_data = model_resource.data()
        if model_data:
            all_texture_refs.update(iterate_textures(model_data))
    except Exception:
        pass

for tex in missing:
    found_in_models = tex.lower() in [t.lower() for t in all_texture_refs]
    print(f"  {tex}: {'Referenced by models' if found_in_models else 'NOT referenced by models'}")

print("\nChecking if in module resources:")
for res_ident, loc_list in module.resources().items():
    if res_ident.resname.lower() in [t.lower() for t in missing] and res_ident.restype in (ResourceType.TPC, ResourceType.TGA):
        print(f"  {res_ident.resname}.{res_ident.restype.extension}: FOUND in module resources")

print("\nChecking expected kit - which have TGA files:")
expected_kit = Path("Tools/HolocronToolset/src/toolset/kits/kits/jedienclave/textures")
for tex in missing:
    has_tga = (expected_kit / f"{tex}.tga").exists()
    has_txi = (expected_kit / f"{tex}.txi").exists()
    print(f"  {tex}: TGA={has_tga}, TXI={has_txi}")

