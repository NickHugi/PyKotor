from __future__ import annotations

import cProfile
import os
import pathlib
import sys

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.installation import Installation
from utility.system.path import Path

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")

if __name__ == "__main__":
    profiler = True  # Set to False or None to disable profiler
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    if K1_PATH is not None:
        k1_path = Path(K1_PATH)
        if k1_path.exists():
            Installation(k1_path)
    if K2_PATH is not None:
        k2_path = Path(K2_PATH)
        if k2_path.exists():
            Installation(k2_path)

    if profiler:
        profiler.disable()
        profiler.create_stats()

        profiler.dump_stats(str(Path("profiler_output_post.pstat")))
        try:
            from pstats import Stats

            with Path("profiler_output_post.prof").open("w") as f:
                stats = Stats(profiler, stream=f)
                stats.sort_stats("cumulative")
                stats.print_stats()
                stats.print_callers()
                stats.print_callees()
                stats.print_callers()
                stats.print_callees()

        except ModuleNotFoundError:
            print("Install `pstats` to profile call stacks.")
            print("Once it's installed, you can run the profiler again.")
