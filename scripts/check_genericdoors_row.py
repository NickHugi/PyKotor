"""Check what's in genericdoors.2da for a specific appearance_id."""
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
from pykotor.resource.formats.twoda import read_2da
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
    print(f"ERROR: K1_PATH not set or invalid! (value: {K1_PATH})")
    sys.exit(1)

inst = Installation(K1_PATH)

# Load genericdoors.2da
print("Loading genericdoors.2da...")
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
                print(f"Loaded from: {loc.filepath}")
                break
except Exception as e:
    print(f"ERROR: {e}")

if genericdoors_2da is None:
    print("Trying resource() fallback...")
    try:
        result = inst.resource("genericdoors", ResourceType.TwoDA)
        if result and result.data:
            genericdoors_2da = read_2da(result.data)
            print("Loaded via resource()")
    except Exception as e:
        print(f"ERROR: {e}")

if genericdoors_2da is None:
    print("ERROR: Could not load genericdoors.2da!")
    sys.exit(1)

# Check row 11 (appearance_id 11)
print(f"\nChecking row 11 (appearance_id 11):")
try:
    row = genericdoors_2da.get_row(11)
    print(f"  Row exists: {row is not None}")
    if row:
        modelname = row.get_string("modelname")
        print(f"  Model name: {modelname}")
        print(f"  All columns in row:")
        for col in genericdoors_2da.get_headers():
            val = row.get_string(col)
            if val:
                print(f"    {col}: {val}")
except Exception as e:
    print(f"  ERROR accessing row 11: {e}")

# Check a few other rows to see the pattern
print(f"\nChecking first 5 rows:")
for i in range(5):
    try:
        row = genericdoors_2da.get_row(i)
        if row:
            modelname = row.get_string("modelname")
            print(f"  Row {i}: {modelname}")
    except Exception as e:
        print(f"  Row {i}: ERROR - {e}")

# Check if there's a row with a valid model
print(f"\nSearching for rows with valid model names (not 'mydoor.mdl'):")
valid_models = []
for i in range(100):  # Check first 100 rows
    try:
        row = genericdoors_2da.get_row(i)
        if row:
            modelname = row.get_string("modelname")
            if modelname and modelname.lower() != "mydoor.mdl" and modelname:
                valid_models.append((i, modelname))
                if len(valid_models) <= 10:
                    print(f"  Row {i}: {modelname}")
    except Exception:
        break

print(f"\nFound {len(valid_models)} rows with valid model names")

