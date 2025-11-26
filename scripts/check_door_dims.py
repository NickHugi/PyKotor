"""Check door dimensions in generated JSON."""
import json
from pathlib import Path

gen = Path("tests/test_toolset/test_files/generated_kit/jedienclave.json")
if not gen.exists():
    print("Generated JSON not found!")
    exit(1)

data = json.loads(gen.read_text(encoding="utf-8"))
doors = data.get("doors", [])
print(f"Total doors: {len(doors)}")

non_default = [d for d in doors if d.get("width", 0) != 2.0 or d.get("height", 0) != 3.0]
print(f"Non-default dimensions: {len(non_default)}")
for d in non_default[:10]:
    print(f"  {d.get('utd_k1')}: {d.get('width')}x{d.get('height')}")

default_count = len(doors) - len(non_default)
print(f"\nDefault dimensions (2.0x3.0): {default_count}")

