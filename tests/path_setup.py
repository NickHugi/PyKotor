import sys
from pathlib import Path
print()
print("TEST","PATH SETUP","TEST")
TESTS_FOLDER = Path(__file__).parent
UTILITY_PATH = TESTS_FOLDER.parents[2].joinpath("Utility").resolve()

utility_path_str = str(UTILITY_PATH)
if utility_path_str not in sys.path:
    sys.path.append(str(UTILITY_PATH))