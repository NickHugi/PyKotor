"""Check if missing resources are actually referenced by danm13 models."""

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

from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.common.module import Module  # noqa: E402
from pykotor.tools.model import iterate_lightmaps, iterate_textures  # noqa: E402

k1_path = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
inst = Installation(k1_path)
module = Module("danm13", inst, use_dot_mod=False)

all_lightmaps = set()
all_textures = set()

print("Scanning all models in danm13...")
for mdl in module.models():
    try:
        mdl_data = mdl.data()
        if mdl_data is None:
            print(f"  Error getting data for {mdl.identifier()}")
            continue
        for lm in iterate_lightmaps(mdl_data):
            all_lightmaps.add(lm.lower())
        mdl_data2 = mdl.data()
        if mdl_data2 is None:
            print(f"  Error getting data for {mdl.identifier()}")
            continue
        for tex in iterate_textures(mdl_data2):
            all_textures.add(tex.lower())
    except Exception as e:
        print(f"  Error processing {mdl.identifier()}: {e}")

print(f"\nTotal lightmaps referenced: {len(all_lightmaps)}")
print(f"Total textures referenced: {len(all_textures)}")

missing_lms = [
    "m03af_01a_lm13", "m03af_03a_lm13",
    "m03mg_01a_lm13",
    "m10aa_01a_lm13", "m10ac_28a_lm13",
    "m14ab_02a_lm13",
    "m15aa_01a_lm13",
    "m22aa_03a_lm13", "m22ab_12a_lm13",
    "m28ab_19a_lm13",
    "m33ab_01_lm13",
    "m36aa_01_lm13",
    "m44ab_27a_lm13",
]

missing_textures = [
    "h_f_lo01headtest", "i_datapad", "lda_bark04", "lda_flr07", "lda_flr08",
    "lda_flr11", "lda_grass07", "lda_grate01", "lda_ivy01", "lda_leaf02",
    "lda_lite01", "lda_rock06", "lda_sky0001", "lda_sky0002", "lda_sky0003",
    "lda_sky0004", "lda_sky0005", "lda_trim02", "lda_trim03", "lda_trim04",
    "lda_unwal07",
]

print("\nChecking if missing lightmaps are referenced:")
for lm in missing_lms:
    if lm.lower() in all_lightmaps:
        print(f"  {lm}: YES")
    else:
        print(f"  {lm}: NO")

print("\nChecking if missing textures are referenced:")
for tex in missing_textures:
    if tex.lower() in all_textures:
        print(f"  {tex}: YES")
    else:
        print(f"  {tex}: NO")

