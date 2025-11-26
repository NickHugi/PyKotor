"""Check appearance_ids of all doors in danm13_s.rim."""
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
from pykotor.resource.generics.utd import read_utd
from pykotor.resource.type import ResourceType

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
    print(f"ERROR: K1_PATH not set or invalid!")
    sys.exit(1)

inst = Installation(K1_PATH)
modules_path = inst.module_path()
data_rim_path = modules_path / "danm13_s.rim"

if not data_rim_path.exists():
    print(f"ERROR: {data_rim_path} not found!")
    sys.exit(1)

data_rim = read_rim(data_rim_path)

# Find all door UTDs
door_utds = []
for resource in data_rim:
    if resource.restype == ResourceType.UTD:
        door_data = resource.data
        utd = read_utd(door_data)
        door_utds.append((str(resource.resref), utd.appearance_id))

print(f"Found {len(door_utds)} doors:\n")
for door_name, appearance_id in door_utds:
    print(f"  {door_name:30s} - appearance_id: {appearance_id}")

# Check if "mydoor" model exists
print(f"\nChecking if 'mydoor' model exists...")
mydoor_result = inst.resource("mydoor", ResourceType.MDL)
if mydoor_result and mydoor_result.data:
    print("  ✓ mydoor.mdl exists")
else:
    print("  ✗ mydoor.mdl does NOT exist")

# Check if "MyDoor" model exists (with capital M)
print(f"\nChecking if 'MyDoor' model exists...")
mydoor_cap_result = inst.resource("MyDoor", ResourceType.MDL)
if mydoor_cap_result and mydoor_cap_result.data:
    print("  ✓ MyDoor.mdl exists")
else:
    print("  ✗ MyDoor.mdl does NOT exist")

