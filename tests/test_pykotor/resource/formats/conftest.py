from __future__ import annotations

import cProfile
import os
import pathlib
import shutil
import sys
from contextlib import suppress
from io import StringIO
from pathlib import Path  # noqa: E402
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Libraries", "Utility", "src")

def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        print(f"Adding {working_dir} to sys.path")
        sys.path.append(working_dir)
    else:
        print(f"{working_dir} already in sys.path!")


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.file import FileResource, ResourceIdentifier
from utility.error_handling import format_exception_with_variables

from pykotor.common.misc import Game  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.extract.file import FileResource

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")
LOG_FILENAME = "test_ncs_compilers_install"


def pytest_report_teststatus(
    report: pytest.TestReport,
    config: pytest.Config,
) -> tuple[Literal["failed"], Literal["F"], str] | None:
    if report.failed:
        if report.longrepr is None:
            return "failed", "F", "FAILED: <unknown error>"

        reprcrash = getattr(report.longrepr, "reprcrash", None)
        if reprcrash is not None:
            msg = reprcrash.message
        else:
            msg = repr(report.longrepr)
        return "failed", "F", f"FAILED: {msg}"
    return None


def save_profiler_output(
    profiler: cProfile.Profile,
    filepath: os.PathLike | str,
):
    profiler.disable()
    profiler_output_file: Path = Path(filepath)
    profiler_output_file_str: str = str(profiler_output_file)
    profiler.dump_stats(profiler_output_file_str)
    # Generate reports from the profile stats
    # stats = pstats.Stats(profiler_output_file_str).sort_stats('cumulative')
    # stats.print_stats()


def log_file(
    *args,
    filepath: os.PathLike | str | None = None,
    file: StringIO | None = None,
    **kwargs,
):
    buffer: StringIO = file or StringIO()
    print(*args, file=buffer, **kwargs)
    msg: str = buffer.getvalue()
    print(*args, **kwargs)  # noqa: T201

    filepath = Path.cwd().joinpath(f"{LOG_FILENAME}.txt") if filepath is None else Path(filepath)
    with filepath.open(mode="a", encoding="utf-8", errors="strict") as f:
        f.write(msg)


def _setup_and_profile_installation() -> dict[Game, Installation]:
    # Shared helper, but not used locally to trigger anything automatically.
    # It will be imported/copied to specific test files if needed,
    # or kept here and imported.
    all_installations = {}

    profiler: cProfile.Profile | bool = True
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    if K1_PATH and Path(K1_PATH).joinpath("chitin.key").is_file():
        all_installations[Game.K1] = Installation(K1_PATH)
    if K2_PATH and Path(K2_PATH).joinpath("chitin.key").is_file():
        all_installations[Game.K2] = Installation(K2_PATH)

    if profiler:
        save_profiler_output(profiler, "installation_class_profile.pstat")
    return all_installations


@pytest.fixture(params=[Game.K1, Game.K2])
def game(request: pytest.FixtureRequest) -> Game:
    return request.param

# Cleanup hooks can remain as they are general utilities, but ensure they don't trigger heavy operations.
def cleanup_before_tests():
    log_files: list[str] = [
        f"*{LOG_FILENAME}.txt",
        "*FAILED_TESTS*.log",
        "*_incompatible*.txt",
        "*fallback_level*",
        "*test_ncs_compilers_install.txt",
        "*.pstat",
        "*pytest_report.html",
        "*pytest_report.xml",
    ]
    for filename in log_files:
        for file in Path.cwd().glob(filename):
            try:
                file.unlink(missing_ok=True)
            except Exception:
                pass


def cleanup_temp_dirs():
    # These dir names might need to be shared or defined here if they are standard.
    # Since the temp dirs were defined in globals, we should probably keep the NAMES defined
    # but not create them here.
    # Actually, let's just clean specific known temp patterns.
    # For now, removing the explicit cleanup of specific globals since they are gone.
    pass


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
):
    cleanup_temp_dirs()


def pytest_runtest_makereport(
    item: pytest.Item,
    call: pytest.CallInfo,
) -> pytest.TestReport | None:
    if "setup" in call.when:
        return None
    if call.excinfo is not None and call.when == "call":
        longrepr: str = format_exception_with_variables(call.excinfo.value, call.excinfo.type, call.excinfo.tb)
        report = pytest.TestReport(
            nodeid=item.nodeid,
            location=item.location,
            keywords=item.keywords,
            outcome="failed",
            longrepr=longrepr,
            when=call.when,
            sections=[],
            duration=call.stop - call.start,
            user_properties=item.user_properties,
        )
        return report
    return None
