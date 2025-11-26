"""Check if genericdoors.2da exists in installation."""
import os
import sys
from pathlib import Path

# Add paths for imports
REPO_ROOT = Path(__file__).parent.parent
PYKOTOR_PATH = REPO_ROOT / "Libraries" / "PyKotor" / "src"
if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))

from pykotor.extract.file import ResourceIdentifier  # noqa: E402
from pykotor.extract.installation import Installation, SearchLocation  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402

K1_PATH = os.getenv("K1_PATH")
if not K1_PATH:
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("K1_PATH="):
                K1_PATH = line.split("=", 1)[1].strip().strip('"').strip("'")
                break

# Clean up K1_PATH (remove quotes if present)
if K1_PATH:
    K1_PATH = K1_PATH.strip('"').strip("'")

if not K1_PATH or not Path(K1_PATH).exists():
    print(f"ERROR: K1_PATH not set or invalid! (value: {K1_PATH})")
    exit(1)

print(f"Checking installation: {K1_PATH}")
inst = Installation(K1_PATH)

# Try resource() method
result = inst.resource("genericdoors", ResourceType.TwoDA)
print(f"\nUsing installation.resource(): {'Found' if result else 'Not found'}")

# Try locations() method
location_results = inst.locations(
    [ResourceIdentifier(resname="genericdoors", restype=ResourceType.TwoDA)],
    order=[SearchLocation.CHITIN, SearchLocation.OVERRIDE],
)
print(f"\nUsing installation.locations(): {len(location_results)} results")
for res_ident, loc_list in location_results.items():
    print(f"  Resource: {res_ident}")
    for loc in loc_list:
        print(f"    - {loc.filepath}")

