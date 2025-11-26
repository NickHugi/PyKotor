from __future__ import annotations

import cProfile
import sys
import os
import pathlib
from typing import TYPE_CHECKING, Any
from pathlib import Path
from tempfile import TemporaryDirectory

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
    if __name__ == "__main__":
        os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").is_dir():
    add_sys_path(UTILITY_PATH)

from pykotor.common.misc import Game
from pykotor.resource.formats.gff.gff_auto import read_gff, write_gff
from pykotor.resource.generics.are import read_are, write_are
from pykotor.resource.generics.dlg import read_dlg, write_dlg
from pykotor.resource.generics.git import read_git, write_git
from pykotor.resource.generics.jrl import read_jrl, write_jrl
from pykotor.resource.generics.pth import read_pth, write_pth
from pykotor.resource.generics.utc import read_utc, write_utc
from pykotor.resource.generics.utd import read_utd, write_utd
from pykotor.resource.generics.ute import read_ute, write_ute
from pykotor.resource.generics.uti import read_uti, write_uti
from pykotor.resource.generics.utm import read_utm, write_utm
from pykotor.resource.generics.utp import read_utp, write_utp
from pykotor.resource.generics.uts import read_uts, write_uts
from pykotor.resource.generics.utt import read_utt, write_utt
from pykotor.resource.generics.utw import read_utw, write_utw
from pykotor.resource.type import ResourceType
from pykotor.extract.installation import Installation
from pykotor.extract.file import FileResource, ResourceIdentifier
from typing_extensions import Literal

if TYPE_CHECKING:
    from pykotor.extract.file import FileResource

K1_PATH: str | None = os.environ.get("K1_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\swkotor")
K2_PATH: str | None = os.environ.get("K2_PATH", "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Knights of the Old Republic II")

ALL_INSTALLATIONS: dict[Game, Installation] | None = None
ALL_GFFS: dict[Game, list[tuple[FileResource, Path]]] = {Game.K1: [], Game.K2: []}
TEMP_GFF_DIRS: dict[Game, TemporaryDirectory[str]] = {
    Game.K1: TemporaryDirectory(),
    Game.K2: TemporaryDirectory(),
}


def _setup_and_profile_installation() -> dict[Game, Installation]:
    all_installations = {}
    if K1_PATH and Path(K1_PATH).joinpath("chitin.key").is_file():
        all_installations[Game.K1] = Installation(K1_PATH)
    if K2_PATH and Path(K2_PATH).joinpath("chitin.key").is_file():
        all_installations[Game.K2] = Installation(K2_PATH)
    return all_installations

def collect_all_gffs(
    restype: ResourceType = ResourceType.NSS,
) -> dict[Game, list[tuple[FileResource, Path]]]:
    global ALL_INSTALLATIONS
    global ALL_GFFS
    if ALL_INSTALLATIONS is None:
        ALL_INSTALLATIONS = _setup_and_profile_installation()

    all_gffs: dict[Game, list[tuple[FileResource, Path]]] = {Game.K1: [], Game.K2: []}
    for game, installation in ALL_INSTALLATIONS.items():
        gff_convert_dir = Path(TEMP_GFF_DIRS[game].name)
        for resource in installation:
            if resource.restype().contents != "gff":
                continue
            res_ident: ResourceIdentifier = resource.identifier()
            filename: str = str(res_ident)
            filepath: Path = resource.filepath()

            if resource.inside_capsule:
                subfolder: str = Installation.get_module_root(filepath)
            elif resource.inside_bif:
                subfolder = filepath.name
            else:
                subfolder = filepath.parent.name

            subfolder_path: Path = gff_convert_dir / subfolder
            gff_convert_filepath: Path = subfolder_path / filename
            all_gffs[game].append((resource, gff_convert_filepath))

    ALL_GFFS = all_gffs
    return all_gffs


def extract_all_gffs():
    """Performs the actual disk extraction (directory creation) for GFFs."""
    global ALL_GFFS
    for game, gff_list in ALL_GFFS.items():
        for resource, gff_convert_filepath in gff_list:
            # Create directory
            gff_convert_filepath.parent.mkdir(parents=True, exist_ok=True)


def pytest_generate_tests(metafunc: pytest.Metafunc):
    if "gff_data" in metafunc.fixturenames:
        print("Generating GFF conversion tests...")
        
        if not ALL_GFFS[Game.K1] and not ALL_GFFS[Game.K2]:
            collect_all_gffs()

        combined_data: list[tuple[str, tuple[Game, FileResource, Path]]] = [(f"{game}_{resource._path_ident_obj}", (game, resource, conversion_path)) for game, gff_info in ALL_GFFS.items() for resource, conversion_path in gff_info]

        sorted_combined_data: list[tuple[str, tuple[Game, FileResource, Path]]] = sorted(combined_data, key=lambda x: x[0])

        sorted_ids: list[str] = [item[0] for item in sorted_combined_data]
        sorted_test_gff_data: list[tuple[Game, FileResource, Path]] = [item[1] for item in sorted_combined_data]
        metafunc.parametrize("gff_data", sorted_test_gff_data, ids=sorted_ids, indirect=True)


@pytest.fixture(scope="session")
def ensure_gffs_ready():
    if not ALL_GFFS[Game.K1] and not ALL_GFFS[Game.K2]:
        collect_all_gffs()
    extract_all_gffs()

@pytest.fixture
def gff_data(request: pytest.FixtureRequest, ensure_gffs_ready):
    return request.param


def test_gff_conversions(
    gff_data: tuple[Game, FileResource, Path],
):
    game, resource, converted_filepath = gff_data
    converted_game = Game.K2 if game.is_k1() else Game.K1
    generic: Any

    if resource.restype() is ResourceType.ARE:
        generic = read_are(resource.data(), offset=0, size=resource.size())
        write_are(generic, converted_filepath, converted_game)

    elif resource.restype() is ResourceType.DLG:
        generic = read_dlg(resource.data(), offset=0, size=resource.size())
        write_dlg(generic, converted_filepath, converted_game)

    elif resource.restype() is ResourceType.GIT:
        generic = read_git(resource.data(), offset=0, size=resource.size())
        write_git(generic, converted_filepath, converted_game)

    elif resource.restype() is ResourceType.JRL:
        generic = read_jrl(resource.data(), offset=0, size=resource.size())
        write_jrl(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.PTH:
        generic = read_pth(resource.data(), offset=0, size=resource.size())
        write_pth(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTC:
        generic = read_utc(resource.data(), offset=0, size=resource.size())
        write_utc(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTD:
        generic = read_utd(resource.data(), offset=0, size=resource.size())
        write_utd(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTE:
        generic = read_ute(resource.data(), offset=0, size=resource.size())
        write_ute(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTI:
        generic = read_uti(resource.data(), offset=0, size=resource.size())
        write_uti(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTM:
        generic = read_utm(resource.data(), offset=0, size=resource.size())
        write_utm(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTP:
        generic = read_utp(resource.data(), offset=0, size=resource.size())
        write_utp(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTS:
        generic = read_uts(resource.data(), offset=0, size=resource.size())
        write_uts(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTT:
        generic = read_utt(resource.data(), offset=0, size=resource.size())
        write_utt(generic, converted_filepath, game=converted_game)

    elif resource.restype() is ResourceType.UTW:
        generic = read_utw(resource.data(), offset=0, size=resource.size())
        write_utw(generic, converted_filepath, game=converted_game)

    elif resource.restype() in {
        ResourceType.RES,
        ResourceType.FAC,
        ResourceType.GUI,
        ResourceType.IFO,
        ResourceType.BIC,
    }:
        unknown_generic = read_gff(resource.data())
        write_gff(unknown_generic, converted_filepath)


def save_profiler_output(
    profiler: cProfile.Profile,
    filepath: os.PathLike | str,
):
    profiler.disable()
    profiler_output_file = Path(filepath)
    profiler_output_file_str = str(profiler_output_file)
    profiler.dump_stats(profiler_output_file_str)


if __name__ == "__main__":
    profiler: cProfile.Profile = True  # pyright: ignore[reportAssignmentType, assignment]
    if profiler:
        profiler = cProfile.Profile()
        profiler.enable()

    result: int | pytest.ExitCode = pytest.main(
        [
            __file__,
            "-v",
            # "--full-trace",
            "-ra",
            "--log-file=test_gff_conversions.txt",
            "-o",
            "log_cli=true",
            "--capture=no",
            "--junitxml=pytest_report.xml",
            "--html=pytest_report.html",
            "--self-contained-html",
            # "-n",
            # "auto"
        ],
    )

    if profiler:
        save_profiler_output(profiler, "profiler_output.pstat")
