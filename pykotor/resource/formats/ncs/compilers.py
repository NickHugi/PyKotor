import subprocess

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, write_ncs
from pykotor.resource.formats.ncs.ncs_data import NCSCompiler


class InbuiltNCSCompiler(NCSCompiler):
    def compile(self, source_path: str, output_path: str, game: Game) -> None:
        source = BinaryReader.load_file(source_path).decode(errors="ignore")
        ncs = compile_nss(source, game)
        write_ncs(ncs, output_path)


class ExternalNCSCompiler(NCSCompiler):
    def __init__(self, nwnnsscomp_path: str):
        self.nwnnsscomp_path: str = nwnnsscomp_path

    def compile(self, source_filepath: str, output_filepath: str, game: Game) -> None:
        subprocess.call(
            [
                self.nwnnsscomp_path,
                "-c",
                source_filepath,
                "-o",
                output_filepath,
                "-g",
                str(game.value),
            ],
            stdin=None,
            stdout=None,
            stderr=None,
            shell=False,
        )
