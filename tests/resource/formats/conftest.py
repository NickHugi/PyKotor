from __future__ import annotations

from pathlib import Path

import cProfile
import contextlib
import os
import pathlib
import shutil
import sys
from io import StringIO
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
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource
    from typing_extensions import Literal

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
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
    Game.K1: set(),  #{"nwscript.nss"},
    Game.K2: set(),  #{"nwscript.nss"},
}

def pytest_report_teststatus(report: pytest.TestReport, config: pytest.Config) -> tuple[Literal['failed'], Literal['F'], str] | None:
    if report.failed:
        if report.longrepr is None:
            msg = ""
        elif hasattr(report.longrepr, "reprcrash"):
            msg = report.longrepr.reprcrash.message
        else:
            msg = repr(report.longrepr)
        return "failed", "F", f"FAILED: {msg}"

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

def _setup_and_profile_installation() -> dict[Game, Installation]:
    global ALL_INSTALLATIONS  # noqa: PLW0603

    ALL_INSTALLATIONS = {}

    profiler = True  # type: ignore[reportAssignmentType]
    if profiler:
        profiler: cProfile.Profile = cProfile.Profile()
        profiler.enable()

    #if K1_PATH and Path(K1_PATH).joinpath("chitin.key").is_file():
        #ALL_INSTALLATIONS[Game.K1] = Installation(K1_PATH)
        #ALL_INSTALLATIONS[Game.K1].reload_all()
    #if K2_PATH and Path(K2_PATH).joinpath("chitin.key").is_file():
        #ALL_INSTALLATIONS[Game.K2] = Installation(K2_PATH)
        #ALL_INSTALLATIONS[Game.K2].reload_all()

    if profiler:
        save_profiler_output(profiler, "installation_class_profile.pstat")
    return ALL_INSTALLATIONS

def populate_all_scripts(restype: ResourceType = ResourceType.NSS, hack_extract=False) -> dict[Game, list[tuple[FileResource, Path, Path]]]:
    global ALL_SCRIPTS
    if ALL_SCRIPTS is not None:
        return ALL_SCRIPTS

    global ALL_INSTALLATIONS
    if ALL_INSTALLATIONS is None:
        ALL_INSTALLATIONS = _setup_and_profile_installation()

    ALL_SCRIPTS = {Game.K1: [], Game.K2: []}

    symlink_map: dict[Path, FileResource] = {}

    iterator = (
        (Game.K1, Installation(r"C:\GitHub\ipatool-2.1.3-windows-amd64.tar\ipatool-2.1.3-windows-amd64\bin\com.aspyr.kotor.ios_611436052_1.2.7\Payload\KOTOR.app")),
        #(Game.K2, Installation(K2_PATH)),
    ) if hack_extract else ALL_INSTALLATIONS.items()


    for i, (game, installation) in enumerate(iterator):
        for resource in installation: #.override_resources():
            if resource.restype() != restype:
                continue
            res_ident = resource.identifier()
            resdata = resource.data()
            filename = str(res_ident)

            if resource.inside_capsule:
                subfolder = Installation.replace_module_extensions(resource.filepath())
            elif resource.inside_bif:
                subfolder = resource.filepath().name
            else:
                subfolder = resource.filepath().parent.name

            if res_ident in CANNOT_COMPILE_EXT[game]:
                log_file(f"Skipping '{filename}', known incompatible...", filepath="fallback_out.txt")
                continue

            if not hack_extract:
                nss_dir = Path(TEMP_NSS_DIRS[game].name)
            else:
                nss_dir = Path(r"C:\GitHub\Vanilla_KOTOR_Script_Source\K1").joinpath("iOS") if i == 0 else Path(r"C:\GitHub\Vanilla_KOTOR_Script_Source\K2").joinpath("iOS")
            nss_path: Path = nss_dir.joinpath(subfolder, filename)
            nss_path.parent.mkdir(exist_ok=True, parents=True)

            if not hack_extract:
                ncs_dir = Path(TEMP_NCS_DIRS[game].name)
            else:
                ncs_dir = Path(r"C:\GitHub\Vanilla_KOTOR_Script_Source\K1").joinpath("iOS") if i == 0 else Path(r"C:\GitHub\Vanilla_KOTOR_Script_Source\K2").joinpath("iOS")
            ncs_path: Path = ncs_dir.joinpath(subfolder, filename).with_suffix(".ncs")
            ncs_path.parent.mkdir(exist_ok=True, parents=True)

            if not hack_extract and resource.inside_bif:
                assert nss_path not in symlink_map, f"'{nss_path.name}' is a bif script name that should not exist in symlink_map yet?"
                symlink_map[nss_path] = resource

            assert hack_extract or not nss_path.is_file()
            with nss_path.open("wb") as f:
                f.write(resdata)

            if hack_extract:
                continue

            ALL_SCRIPTS[game].append((resource, nss_path, ncs_path))

        seen_paths = set()
        for resource, nss_path, ncs_path in ALL_SCRIPTS[game]:
            if nss_path in symlink_map:
                continue
            if nss_path in seen_paths:
                continue
            if nss_path.name.lower() == "nwscript.nss" and nss_path.is_file():
                continue

            working_folder = nss_path.parent
            for bif_nss_path in symlink_map:
                target_symlink_path = working_folder.joinpath(bif_nss_path.name)
                assert not target_symlink_path.is_file(), f"'{nss_path.name}' is a bif script name that should not exist at this path yet?"
                target_symlink_path.symlink_to(bif_nss_path, target_is_directory=False)
            seen_paths.add(working_folder)



    return ALL_SCRIPTS



@pytest.fixture(params=[Game.K1, Game.K2])
def game(request: pytest.FixtureRequest) -> Game:
    return request.param

# when using `indirect=True`, we must have a fixture to accept these parameters.
@pytest.fixture
def script_data(request: pytest.FixtureRequest):
    return request.param

# TODO: function isn't called early enough.
def cleanup_before_tests():
    # List of paths for temporary directories and log files
    log_files = [
        f"{LOG_FILENAME}.txt",
        "FAILED_TESTS*.log",
        "*_incompatible.txt",
        "test_ncs_compilers_install.txt"
    ]

    # Delete log files
    for filename in log_files:
        for file in Path.cwd().glob(filename):
            with contextlib.suppress(OSError):
                file.unlink(missing_ok=True)

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
        f"{game}_{script[0].identifier()}"
        for game, scripts in scripts_fixture.items()
        for script in scripts
    ]
    metafunc.parametrize("script_data", test_data, ids=ids, indirect=True)