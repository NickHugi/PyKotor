from __future__ import annotations

import cProfile

from typing import TYPE_CHECKING, Any

import pytest

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
from utility.system.path import Path

if TYPE_CHECKING:
    import os
    from pykotor.extract.file import FileResource


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
    profiler_output_file = Path.pathify(filepath)
    profiler_output_file_str = str(profiler_output_file)
    profiler.dump_stats(profiler_output_file_str)


if __name__ == "__main__":
    profiler: cProfile.Profile = True  # type: ignore[reportAssignmentType, assignment]
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
