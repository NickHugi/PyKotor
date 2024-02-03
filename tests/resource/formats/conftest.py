from __future__ import annotations

import cProfile
import contextlib
import logging
import os
import pathlib
import shutil
import sys
from io import StringIO
from logging.handlers import RotatingFileHandler
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").is_dir():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").is_dir():
    add_sys_path(UTILITY_PATH)

from pykotor.common.misc import Game  # noqa: E402
from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS  # noqa: E402
from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.resource.formats.ncs.compiler.classes import CompileError, EntryPointError  # noqa: E402
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer  # noqa: E402
from pykotor.resource.formats.ncs.compiler.parser import NssParser  # noqa: E402
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, InbuiltNCSCompiler  # noqa: E402
from pykotor.resource.formats.ncs.ncs_auto import compile_nss  # noqa: E402
from pykotor.resource.formats.ncs.ncs_data import NCS, NCSCompiler  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402
from utility.error_handling import format_exception_with_variables, universal_simplify_exception  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from _pytest.reports import TestReport
    from ply import yacc
    from pykotor.extract.file import FileResource

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
NWNNSSCOMP_PATH: str | None = r"C:/Program Files (x86)/KotOR Scripting Tool/nwnnsscomp.exe"
NWNNSSCOMP_PATH2: str | None = r"C:\Program Files (x86)\Kotor Tool\nwnnsscomp.exe"
NWNNSSCOMP_PATH3: str | None = r"C:\Users\boden\Documents\k1 mods\KillCzerkaJerk\tslpatchdata\nwnnsscomp.exe"
LOG_FILENAME = "test_ncs_compilers_install"

ALL_INSTALLATIONS: dict[Game, Installation] | None = None
ALL_SCRIPTS: dict[Game, list[tuple[FileResource, Path, Path]]] | None = None
TEMP_NSS_DIRS: dict[Game, TemporaryDirectory[str]] = {
    Game.K1: TemporaryDirectory(),
    Game.K2: TemporaryDirectory()
}
TEMP_NCS_DIRS: dict[Game, TemporaryDirectory[str]] = {
    Game.K1: TemporaryDirectory(),
    Game.K2: TemporaryDirectory()
}

CANNOT_COMPILE_EXT: dict[Game, set[str]] = {
    Game.K1: {
        "nwscript.nss"
    },
    Game.K2: {
        "nwscript.nss"
        "a_262imprison_ext3.ncs"  # tslpatcher's nwnnsscomp.exe fails
    },
}

#def pytest_report_teststatus(report, config):
#    if report.when == 'call' and report.failed:
#        return report.outcome, 'F', 'FAILED'
#    if report.when == 'call':
#        return report.outcome, '', ''
#    return None

def save_profiler_output(profiler: cProfile.Profile, filepath: os.PathLike | str):
    profiler.disable()
    profiler_output_file = Path.pathify(filepath)
    profiler_output_file_str = str(profiler_output_file)
    profiler.dump_stats(profiler_output_file_str)
    # Generate reports from the profile stats
    #stats = pstats.Stats(profiler_output_file_str).sort_stats('cumulative')
    #stats.print_stats()

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

    filepath = (
        Path.cwd().joinpath(f"{LOG_FILENAME}.txt")
        if filepath is None
        else Path.pathify(filepath)
    )
    with filepath.open(mode="a", encoding="utf-8", errors="strict") as f:
        f.write(msg)

def _setup_and_profile_installation():
    global ALL_INSTALLATIONS  # noqa: PLW0603

    ALL_INSTALLATIONS = {}

    profiler = True  # type: ignore[reportAssignmentType]
    if profiler:
        profiler: cProfile.Profile = cProfile.Profile()
        profiler.enable()

    if K1_PATH and Path(K1_PATH).joinpath("chitin.key").is_file():
        ALL_INSTALLATIONS[Game.K1] = Installation(K1_PATH)
    if K2_PATH and Path(K2_PATH).joinpath("chitin.key").is_file():
        ALL_INSTALLATIONS[Game.K2] = Installation(K2_PATH)

    if profiler:
        save_profiler_output(profiler, "installation_class_profile.pstat")
    return ALL_INSTALLATIONS

def populate_all_scripts() -> dict[Game, list[tuple[FileResource, Path, Path]]]:
    global ALL_SCRIPTS
    if ALL_SCRIPTS is not None:
        return ALL_SCRIPTS

    global ALL_INSTALLATIONS
    if ALL_INSTALLATIONS is None:
        ALL_INSTALLATIONS = _setup_and_profile_installation()

    ALL_SCRIPTS = {Game.K1: [], Game.K2: []}
    for game, installation in ALL_INSTALLATIONS.items():
        for resource in installation:
            res_ident = resource.identifier()
            if res_ident in CANNOT_COMPILE_EXT[game]:
                if res_ident != "nwscript.nss":
                    log_file(f"Skipping {resource.identifier()}, known incompatible...", filepath="fallback_out.txt")
                continue
            if resource.restype() != ResourceType.NSS:
                continue
            nss_path: Path = Path(TEMP_NSS_DIRS[game].name).joinpath(str(resource.identifier()))
            ncs_path: Path = Path(TEMP_NCS_DIRS[game].name).joinpath(resource.resname()).with_suffix(".ncs")
            with nss_path.open("wb") as f:
                f.write(resource.data())
            ALL_SCRIPTS[game].append((resource, nss_path, ncs_path))

    return ALL_SCRIPTS


@pytest.fixture(params=[Game.K1, Game.K2])
def game(request: pytest.FixtureRequest) -> Game:
    return request.param

# when using `indirect=True`, we must have a fixture to accept these parameters.
@pytest.fixture
def script_data(request: pytest.FixtureRequest):
    return request.param

def cleanup_before_tests():
    # List of paths for temporary directories and log files
    log_files = [
        f"{LOG_FILENAME}.txt",
        "FAILED_TESTS.log",
        "FAILED_TESTS_1.log",
        "FAILED_TESTS_2.log",
        "FAILED_TESTS_3.log",
        "FAILED_TESTS_4.log",
        "fallback_level_info.txt",
        "fallback_level_debug.txt",
    ]

    # Delete log files
    for log_file in log_files:
        with contextlib.suppress(OSError):
            Path.cwd().joinpath(log_file).unlink()

    # Glob and delete remaining files ending in "_incompatible.txt"
    for incompatible_file in Path.cwd().glob("*_incompatible.txt"):
        with contextlib.suppress(FileNotFoundError):
            incompatible_file.unlink()

def cleanup_temp_dirs():
    temp_dirs = [
        TEMP_NSS_DIRS[Game.K1].name,
        TEMP_NCS_DIRS[Game.K1].name,
        TEMP_NSS_DIRS[Game.K2].name,
        TEMP_NCS_DIRS[Game.K2].name,
    ]
    for temp_dir in temp_dirs:
        shutil.rmtree(temp_dir, ignore_errors=True)

def pytest_sessionstart(session: pytest.Session):
    cleanup_before_tests()

def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
):
    cleanup_temp_dirs()

def pytest_generate_tests(metafunc: pytest.Metafunc):
    if "script_data" not in metafunc.fixturenames:
        return
    scripts_fixture = populate_all_scripts()
    test_data = [
        (game, script)
        for game, scripts in scripts_fixture.items()
        for script in scripts
    ]
    ids=[
        f"{game}_{script[0].identifier()}_compile_nss"
        for game, scripts in scripts_fixture.items()
        for script in scripts
    ]
    metafunc.parametrize("script_data", test_data, ids=ids, indirect=True)