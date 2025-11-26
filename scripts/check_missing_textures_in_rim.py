"""Check if missing textures are in RIM files."""

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
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.type import ResourceType
from pykotor.common.module import Module

k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
inst = Installation(k1_path)

missing_textures = [
    "p_carthh01", "plc_chair1", "p_bastillah01", "pheyea", "w_vbroswrd01"
]

print("Checking if missing textures are in RIM files or module resources:")
print("=" * 80)

# Check RIM files directly
rims_path = inst.rims_path()
modules_path = inst.module_path()

main_rim_path = modules_path / "danm13.rim" if modules_path.exists() else None
data_rim_path = modules_path / "danm13_s.rim" if modules_path.exists() else None

if main_rim_path and main_rim_path.exists():
    main_rim = read_rim(main_rim_path)
    print(f"\nChecking {main_rim_path.name}:")
    for resource in main_rim:
        resname_lower = str(resource.resref).lower()
        if resname_lower in [t.lower() for t in missing_textures]:
            print(f"  Found: {resource.resref}.{resource.restype.extension}")

if data_rim_path and data_rim_path.exists():
    data_rim = read_rim(data_rim_path)
    print(f"\nChecking {data_rim_path.name}:")
    for resource in data_rim:
        resname_lower = str(resource.resref).lower()
        if resname_lower in [t.lower() for t in missing_textures]:
            print(f"  Found: {resource.resref}.{resource.restype.extension}")

# Check module resources
module = Module("danm13", inst, use_dot_mod=False)
print(f"\nChecking module resources:")
for res_ident, loc_list in module.resources().items():
    resname_lower = res_ident.resname.lower()
    if resname_lower in [t.lower() for t in missing_textures] and res_ident.restype in (ResourceType.TPC, ResourceType.TGA):
        print(f"  Found: {res_ident.resname}.{res_ident.restype.extension}")

# Check if they're referenced by models
print(f"\nChecking if referenced by models:")
all_texture_refs = set()
for model_resource in module.models():
    try:
        model_data = model_resource.data()
        if model_data:
            from pykotor.tools.model import iterate_textures
            all_texture_refs.update(iterate_textures(model_data))
    except Exception:
        pass

for tex in missing_textures:
    if tex.lower() in [t.lower() for t in all_texture_refs]:
        print(f"  {tex}: Referenced by models")
    else:
        print(f"  {tex}: NOT referenced by models")

