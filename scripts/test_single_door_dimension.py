"""Test door dimension extraction for a single door."""
import os
import sys
from pathlib import Path

# Add paths for imports
REPO_ROOT = Path(__file__).parent.parent
PYKOTOR_PATH = REPO_ROOT / "Libraries" / "PyKotor" / "src"
if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))

from pykotor.extract.installation import Installation, SearchLocation
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.rim import read_rim
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.type import ResourceType
from pykotor.tools import door as door_tools
from pykotor.resource.formats.mdl import read_mdl
from pykotor.resource.formats.twoda import read_2da
from utility.common.geometry import Vector3

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

print(f"Installation: {K1_PATH}")
inst = Installation(K1_PATH)

# Load danm13_s.rim to get doors
modules_path = inst.module_path()
data_rim_path = modules_path / "danm13_s.rim"

if not data_rim_path.exists():
    print(f"ERROR: {data_rim_path} not found!")
    sys.exit(1)

print(f"Loading {data_rim_path.name}...")
data_rim = read_rim(data_rim_path)

# Find first door UTD
door_utds = []
for resource in data_rim:
    if resource.restype == ResourceType.UTD:
        door_utds.append((str(resource.resref), resource.data))

if not door_utds:
    print("ERROR: No UTD doors found")
    sys.exit(1)

print(f"\nFound {len(door_utds)} doors. Testing: {door_utds[0][0]}")
door_name, door_data = door_utds[0]
utd = read_utd(door_data)

print(f"\nDoor: {door_name}")
print(f"  Appearance ID: {utd.appearance_id}")

# Load genericdoors.2da
print("\nLoading genericdoors.2da...")
genericdoors_2da = None
try:
    location_results = inst.locations(
        [ResourceIdentifier(resname="genericdoors", restype=ResourceType.TwoDA)],
        order=[SearchLocation.OVERRIDE, SearchLocation.CHITIN],
    )
    for res_ident, loc_list in location_results.items():
        if loc_list:
            loc = loc_list[0]
            if loc.filepath and Path(loc.filepath).exists():
                with loc.filepath.open("rb") as f:
                    f.seek(loc.offset)
                    data = f.read(loc.size)
                genericdoors_2da = read_2da(data)
                print(f"  Loaded from: {loc.filepath}")
                break
except Exception as e:
    print(f"  ERROR: {e}")

if genericdoors_2da is None:
    print("  Trying resource() fallback...")
    try:
        result = inst.resource("genericdoors", ResourceType.TwoDA)
        if result and result.data:
            genericdoors_2da = read_2da(result.data)
            print("  Loaded via resource()")
    except Exception as e:
        print(f"  ERROR: {e}")

if genericdoors_2da is None:
    print("\nERROR: Could not load genericdoors.2da!")
    sys.exit(1)

# Get model name
print("\nGetting model name...")
try:
    model_name = door_tools.get_model(utd, inst, genericdoors=genericdoors_2da)
    print(f"  Model name: {model_name}")
    if not model_name:
        print("  ERROR: Model name is None or empty!")
        sys.exit(1)
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Load MDL
print(f"\nLoading MDL: {model_name}...")
try:
    mdl_result = inst.resource(model_name, ResourceType.MDL)
    if not mdl_result or not mdl_result.data:
        print("  ERROR: MDL not found or has no data")
        sys.exit(1)
    mdl = read_mdl(mdl_result.data)
    print("  MDL loaded successfully")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Calculate bounding box
print("\nCalculating bounding box...")
bb_min = Vector3(1000000, 1000000, 1000000)
bb_max = Vector3(-1000000, -1000000, -1000000)

nodes_to_check = [mdl.root]
mesh_count = 0
vertex_count = 0

while nodes_to_check:
    node = nodes_to_check.pop()
    if node.mesh:
        mesh_count += 1
        # Use mesh bounding box if available
        if node.mesh.bb_min and node.mesh.bb_max:
            bb_min.x = min(bb_min.x, node.mesh.bb_min.x)
            bb_min.y = min(bb_min.y, node.mesh.bb_min.y)
            bb_min.z = min(bb_min.z, node.mesh.bb_min.z)
            bb_max.x = max(bb_max.x, node.mesh.bb_max.x)
            bb_max.y = max(bb_max.y, node.mesh.bb_max.y)
            bb_max.z = max(bb_max.z, node.mesh.bb_max.z)
        # Fallback: calculate from vertex positions
        elif node.mesh.vertex_positions:
            for vertex in node.mesh.vertex_positions:
                vertex_count += 1
                bb_min.x = min(bb_min.x, vertex.x)
                bb_min.y = min(bb_min.y, vertex.y)
                bb_min.z = min(bb_min.z, vertex.z)
                bb_max.x = max(bb_max.x, vertex.x)
                bb_max.y = max(bb_max.y, vertex.y)
                bb_max.z = max(bb_max.z, vertex.z)

    nodes_to_check.extend(node.children)

print(f"  Processed {mesh_count} meshes, {vertex_count} vertices")
print(f"  Bounding box: min={bb_min}, max={bb_max}")

if bb_min.x < 1000000:
    width = abs(bb_max.y - bb_min.y)
    height = abs(bb_max.z - bb_min.z)
    depth = abs(bb_max.x - bb_min.x)
    
    print(f"\nCalculated dimensions:")
    print(f"  Width (Y): {width:.3f}")
    print(f"  Height (Z): {height:.3f}")
    print(f"  Depth (X): {depth:.3f}")
    
    if 0.1 < width < 50.0 and 0.1 < height < 50.0:
        print(f"\nSUCCESS: Valid dimensions: {width:.2f} x {height:.2f}")
    else:
        print(f"\nWARNING: Dimensions out of range")
else:
    print("\nERROR: Invalid bounding box")

