"""Script wrapper for kit generation from RIM files.

This script provides a command-line interface for the kit generation functionality
that has been moved to pykotor.tools.kit.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add paths for imports
REPO_ROOT = Path(__file__).parent.parent
LIBS_PATH = REPO_ROOT / "Libraries"
PYKOTOR_PATH = LIBS_PATH / "PyKotor" / "src"
UTILITY_PATH = LIBS_PATH / "Utility" / "src"

if str(PYKOTOR_PATH) not in sys.path:
    sys.path.insert(0, str(PYKOTOR_PATH))
if str(UTILITY_PATH) not in sys.path:
    sys.path.insert(0, str(UTILITY_PATH))

from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.tools.kit import extract_kit_from_rim  # noqa: E402

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a kit from RIM files")
    parser.add_argument("k1_path", type=str, help="Path to K1 installation")
    parser.add_argument("module_name", type=str, help="Module name (e.g., danm13)")
    parser.add_argument("output_path", type=str, help="Output path for the kit")
    parser.add_argument("--kit-id", type=str, default=None, help="Kit ID (defaults to module_name.lower())")
    args = parser.parse_args()

    installation = Installation(args.k1_path)
    extract_kit_from_rim(installation, args.module_name, Path(args.output_path), kit_id=args.kit_id)
    print(f"Kit generated successfully at {args.output_path}")


