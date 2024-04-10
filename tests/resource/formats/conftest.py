from __future__ import annotations

import cProfile
import os
import pathlib
import shutil
import sys

from contextlib import suppress
from io import StringIO
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

from utility.error_handling import format_exception_with_variables

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[3].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.misc import Game  # noqa: E402
from pykotor.extract.installation import Installation  # noqa: E402
from pykotor.resource.type import ResourceType  # noqa: E402
from utility.system.path import Path  # noqa: E402

if TYPE_CHECKING:
    from typing_extensions import Literal

    from pykotor.extract.file import FileResource

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
LOG_FILENAME = "test_ncs_compilers_install"

ALL_INSTALLATIONS: dict[Game, Installation] | None = None
ALL_SCRIPTS: dict[Game, list[tuple[FileResource, Path, Path]]] = {Game.K1: [], Game.K2: []}
ALL_GFFS: dict[Game, list[tuple[FileResource, Path]]] = {Game.K1: [], Game.K2: []}
TEMP_NSS_DIRS: dict[Game, TemporaryDirectory[str]] = {Game.K1: TemporaryDirectory(), Game.K2: TemporaryDirectory()}
TEMP_NCS_DIRS: dict[Game, TemporaryDirectory[str]] = {Game.K1: TemporaryDirectory(), Game.K2: TemporaryDirectory()}

TEMP_GFF_DIRS: dict[Game, TemporaryDirectory[str]] = {
    Game.K1: TemporaryDirectory(),
    Game.K2: TemporaryDirectory(),
}

CANNOT_COMPILE_EXT: dict[Game, set[str]] = {
    Game.K1: set(),  # {"nwscript.nss"},
    Game.K2: set(),  # {"nwscript.nss"},
}


def pytest_report_teststatus(report: pytest.TestReport, config: pytest.Config) -> tuple[Literal["failed"], Literal["F"], str] | None:
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


def save_profiler_output(profiler: cProfile.Profile, filepath: os.PathLike | str):
    profiler.disable()
    profiler_output_file = Path.pathify(filepath)
    profiler_output_file_str = str(profiler_output_file)
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

    filepath = Path.cwd().joinpath(f"{LOG_FILENAME}.txt") if filepath is None else Path.pathify(filepath)
    with filepath.open(mode="a", encoding="utf-8", errors="strict") as f:
        f.write(msg)


def _setup_and_profile_installation() -> dict[Game, Installation]:
    global ALL_INSTALLATIONS  # noqa: PLW0603

    ALL_INSTALLATIONS = {}

    profiler: cProfile.Profile = True  # type: ignore[reportAssignmentType, assignment]
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    if K1_PATH and Path(K1_PATH).joinpath("chitin.key").safe_isfile():
        ALL_INSTALLATIONS[Game.K1] = Installation(K1_PATH)
    if K2_PATH and Path(K2_PATH).joinpath("chitin.key").safe_isfile():
        ALL_INSTALLATIONS[Game.K2] = Installation(K2_PATH)

    if profiler:
        save_profiler_output(profiler, "installation_class_profile.pstat")
    return ALL_INSTALLATIONS


def populate_all_gffs(
    restype: ResourceType = ResourceType.NSS,
) -> dict[Game, list[tuple[FileResource, Path]]]:
    global ALL_INSTALLATIONS
    if ALL_INSTALLATIONS is None:
        ALL_INSTALLATIONS = _setup_and_profile_installation()

    all_gffs: dict[Game, list[tuple[FileResource, Path]]] = {Game.K1: [], Game.K2: []}
    for game, installation in ALL_INSTALLATIONS.items():
        gff_convert_dir = Path(TEMP_GFF_DIRS[game].name)
        for resource in installation:
            if resource.restype().contents != "gff":
                continue
            res_ident = resource.identifier()
            filename = str(res_ident)
            filepath = resource.filepath()

            if resource.inside_capsule:
                subfolder = Installation.replace_module_extensions(filepath)
            elif resource.inside_bif:
                subfolder = filepath.name
            else:
                subfolder = filepath.parent.name

            subfolder_path = gff_convert_dir / subfolder
            subfolder_path.mkdir(parents=True, exist_ok=True)
            gff_convert_filepath = subfolder_path / filename
            all_gffs[game].append((resource, gff_convert_filepath))

    return all_gffs


def populate_all_scripts(
    restype: ResourceType = ResourceType.NSS,
) -> dict[Game, list[tuple[FileResource, Path, Path]]]:
    global ALL_INSTALLATIONS
    if ALL_INSTALLATIONS is None:
        ALL_INSTALLATIONS = _setup_and_profile_installation()

    all_scripts: dict[Game, list[tuple[FileResource, Path, Path]]] = {Game.K1: [], Game.K2: []}
    symlink_map: dict[Path, FileResource] = {}

    for game, installation in ALL_INSTALLATIONS.items():
        game_name = "K1" if game.is_k1() else "TSL"
        print(f"Populating all {game_name} scripts...")
        for resource in installation:
            res_ident = resource.identifier()
            if res_ident.restype != restype:
                continue
            res_ident = resource.identifier()
            filename = str(res_ident)
            filepath = resource.filepath()

            if resource.inside_capsule:
                subfolder = Installation.replace_module_extensions(filepath)
            elif resource.inside_bif:
                subfolder = filepath.name
            else:
                subfolder = filepath.parent.name

            if res_ident in CANNOT_COMPILE_EXT[game]:
                log_file(f"Skipping '{filename}', known incompatible...", filepath="fallback_out.txt")
                continue

            nss_dir = Path(TEMP_NSS_DIRS[game].name)
            nss_path: Path = nss_dir.joinpath(subfolder, filename)
            nss_path.parent.mkdir(exist_ok=True, parents=True)

            ncs_dir = Path(TEMP_NCS_DIRS[game].name)
            ncs_path: Path = ncs_dir.joinpath(subfolder, filename).with_suffix(".ncs")
            ncs_path.parent.mkdir(exist_ok=True, parents=True)

            if resource.inside_bif and "_inc_" in filename.lower():
                assert nss_path not in symlink_map, f"'{nss_path.name}' is a bif script name that should not exist in symlink_map yet?"
                symlink_map[nss_path] = resource

            entry = (resource, nss_path, ncs_path)
            if nss_path.is_file():
                if entry not in all_scripts[game]:
                    continue
                all_scripts[game].append(entry)
                continue  # No idea why this happens

            resdata = resource.data()
            with nss_path.open("wb") as f:
                f.write(resdata)

            all_scripts[game].append(entry)

        print(f"Populated {len(all_scripts[game])} {game_name} scripts.")
        print(f"Symlinking {len(symlink_map)} scripts.bif scripts into subfolders... this may take a while...")
        seen_paths = set()
        for resource, nss_path, ncs_path in all_scripts[game]:
            if nss_path in symlink_map:
                continue
            working_folder = nss_path.parent
            if working_folder in seen_paths:
                continue
            if working_folder.name == "scripts.bif":
                continue
            print(f"Symlinking {len(symlink_map)} bif scripts into {working_folder}...")

            for bif_nss_path in symlink_map:
                link_path = working_folder.joinpath(bif_nss_path.name)
                if link_path.exists():
                    print(f"'{link_path}' is a bif script that should not exist at this path yet? Symlink test: {link_path.is_symlink()}")
                    continue
                # already_exists_msg = f"'{link_path}' is a bif script that should not exist at this path yet? Symlink test: {link_path.is_symlink()}"
                # assert not link_path.is_file(), already_exists_msg
                link_path.symlink_to(bif_nss_path, target_is_directory=False)
            seen_paths.add(working_folder)

    print("Finished symlinking.")
    return all_scripts


@pytest.fixture(params=[Game.K1, Game.K2])
def game(request: pytest.FixtureRequest) -> Game:
    return request.param


# when using `indirect=True`, we must have a fixture to accept these parameters.
@pytest.fixture
def script_data(request: pytest.FixtureRequest):
    return request.param


@pytest.fixture
def gff_data(request: pytest.FixtureRequest):
    return request.param


# TODO: function isn't called early enough.
def cleanup_before_tests():
    # List of paths for temporary directories and log files
    log_files = [
        f"*{LOG_FILENAME}.txt",
        "*FAILED_TESTS*.log",
        "*_incompatible*.txt",
        "*fallback_level*",
        "*test_ncs_compilers_install.txt",
        "*.pstat",
        "*pytest_report.html",
        "*pytest_report.xml",
    ]

    # Delete log files
    for filename in log_files:
        for file in Path.cwd().glob(filename):
            try:
                file.unlink(missing_ok=True)
                print(f"Cleaned '{file}' in preparation for new test...")
            except Exception as e:
                exc_str = str(e)
                file_path_str = str(file)
                if file_path_str.lower() in exc_str.lower():
                    print(f"Cleanup failed: {exc_str}")
                else:
                    print(f"Could not cleanup '{file}': {e}")


def cleanup_temp_dirs():
    temp_dirs = [
        TEMP_NSS_DIRS[Game.K1].name,
        TEMP_NCS_DIRS[Game.K1].name,
        TEMP_NSS_DIRS[Game.K2].name,
        TEMP_NCS_DIRS[Game.K2].name,
        TEMP_GFF_DIRS[Game.K1].name,
        TEMP_GFF_DIRS[Game.K2].name,
    ]
    for temp_dir in temp_dirs:
        temp_dirpath = Path(temp_dir)
        # temp_dirpath.gain_access(recurse=True)
        for temp_file in temp_dirpath.safe_rglob("*"):
            with suppress(Exception):
                temp_file.unlink(missing_ok=True)
        with suppress(Exception):
            shutil.rmtree(temp_dir, ignore_errors=True)


def pytest_configure():
    cleanup_before_tests()
    print("Prepare all scripts...")
    global ALL_SCRIPTS
    ALL_SCRIPTS = populate_all_scripts()
    print("Prepare all GFFs...")
    global ALL_GFFS
    ALL_GFFS = populate_all_gffs()


def pytest_sessionfinish(
    session: pytest.Session,
    exitstatus: int,
):
    cleanup_temp_dirs()


# pytest hook to check test outcomes
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> pytest.TestReport | None:
    if "setup" in call.when:
        # Skip setup phase
        return None
    if call.excinfo is not None and call.when == "call":
        # This means the test has failed
        # Construct and return a TestReport object

        # longrepr = call.excinfo.getrepr()
        longrepr = format_exception_with_variables(call.excinfo.value, call.excinfo.type, call.excinfo.tb)
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


def pytest_generate_tests(metafunc: pytest.Metafunc):
    if "script_data" in metafunc.fixturenames:
        print("Generating NSS compile tests...")
        # Load the data prepared in the session start
        test_script_data = [
            (game, script)
            for game, scripts in ALL_SCRIPTS.items()
            for script in scripts
            if not script[1].is_symlink()  # and not print(f"Skipping test collection for '{script[1]}', already symlinked to '{script[1].resolve()}'")
        ]
        print(f"Test data collected. Total tests: {len(test_script_data)}")
        ids = sorted([f"{game}_{script[0].identifier()}" for game, script in test_script_data])
        print(f"Test IDs collected. Total IDs: {len(ids)}")
        metafunc.parametrize("script_data", test_script_data, ids=ids, indirect=True)
        print("Tests have finished parametrizing!")

    if "gff_data" in metafunc.fixturenames:
        print("Generating GFF conversion tests...")
        # Step 1: Generate IDs along with their corresponding data
        combined_data = [
            (f"{game}_{resource._path_ident_obj}", (game, resource, conversion_path)) for game, gff_info in ALL_GFFS.items() for resource, conversion_path in gff_info
        ]

        # Step 2 and 3: Sort combined data alphabetically by the ID
        sorted_combined_data = sorted(combined_data, key=lambda x: x[0])

        # Step 4: Separate the sorted IDs and their corresponding data back into their respective lists
        sorted_ids = [item[0] for item in sorted_combined_data]
        sorted_test_gff_data = [item[1] for item in sorted_combined_data]
        metafunc.parametrize("gff_data", sorted_test_gff_data, ids=sorted_ids, indirect=True)
        print("Tests have finished parametrizing!")
