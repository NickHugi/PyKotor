from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from pykotor.common.stream import BinaryReader
from pykotor.utility.misc import generate_filehash_sha256
from pykotor.utility.path import Path
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, write_ncs
from pykotor.resource.formats.ncs.ncs_data import NCSCompiler

if TYPE_CHECKING:
    import os

    from pykotor.common.misc import Game


class InbuiltNCSCompiler(NCSCompiler):
    def compile_script(self, source_path: str, output_path: str, game: Game) -> None:
        source = BinaryReader.load_file(source_path).decode(errors="ignore")
        ncs = compile_nss(source, game)
        write_ncs(ncs, output_path)


class ExternalNCSCompiler(NCSCompiler):
    def __init__(self, nwnnsscomp_path: os.PathLike | str):
        self.nwnnsscomp_path: Path = nwnnsscomp_path if isinstance(nwnnsscomp_path, Path) else Path(nwnnsscomp_path)
        self.filehash: str | None = None

    def calculate_filehash(self):
        self.filehash = generate_filehash_sha256(self.nwnnsscomp_path)

    def compile_script(self, source_file: os.PathLike | str, output_file: os.PathLike | str, game: Game) -> None:
        source_filepath, output_filepath = (p.resolve() for p in map(Path, (source_file, output_file)))

        if not self.filehash:
            self.calculate_filehash()
        if not self.filehash:
            msg = "NWNNSSCOMP Filehash could not be calculated"
            raise ValueError(msg)

        executable = str(self.nwnnsscomp_path)
        if self.filehash.upper() == "E36AA3172173B654AE20379888EDDC9CF45C62FBEB7AB05061C57B52961C824D":  # KTool (2005)
            subprocess.call(
                args = [
                    executable,
                    "-c",
                    "--outputdir",
                    f"{output_filepath.parent!s}",
                    "-o",
                    f"{output_filepath.name}",
                    "-g",
                    str(game.value),
                    "--optimize",
                    f"{source_filepath!s}",
                ],
                timeout=15,
            )
        elif self.filehash.upper() == "EC3E657C18A32AD13D28DA0AA3A77911B32D9661EA83CF0D9BCE02E1C4D8499D":  # v1 (2004)
            subprocess.call(
                args=[
                    executable,
                    "-c",
                    "-o",
                    f"{source_filepath!s}",
                    f"{output_filepath!s}",
                ],
                timeout=15,
            )
        elif self.filehash.upper() == "539EB689D2E0D3751AEED273385865278BEF6696C46BC0CAB116B40C3B2FE820":  # TSLPatcher (2009)
            subprocess.call(
                args=[
                    executable,
                    "-c",
                    f"{source_filepath}",
                    "-o",
                    f"{output_filepath}",
                ],
                cwd=str(self.nwnnsscomp_path.parent),
                timeout=15,
            )


    def decompile_script(self, source_file: os.PathLike | str, output_file: os.PathLike | str, game: Game) -> bool:
        source_filepath = source_file if isinstance(source_file, Path) else Path(source_file)
        output_filepath = output_file if isinstance(output_file, Path) else Path(output_file)

        if not self.filehash:
            self.calculate_filehash()
        if not self.filehash:
            msg = "NWNNSSCOMP Filehash could not be calculated"
            raise ValueError(msg)

        executable = str(self.nwnnsscomp_path)
        if self.filehash.upper() == "E36AA3172173B654AE20379888EDDC9CF45C62FBEB7AB05061C57B52961C824D":  # KTool (2005)
            subprocess.call(
                args=[
                    executable,
                    "-d",
                    "--outputdir",
                    f"{output_filepath.parent!s}",
                    "-o",
                    f"{output_filepath.name!s}",
                    "-g",
                    str(game.value),
                    f'"{source_filepath}"',
                ],
                timeout=15,
            )
        elif self.filehash.upper() == "EC3E657C18A32AD13D28DA0AA3A77911B32D9661EA83CF0D9BCE02E1C4D8499D":  # v1 (2004)
            subprocess.call(
                args=[
                    executable,
                    "-d",
                    f"{source_filepath!s}",
                    f"{output_filepath!s}",
                ],
                timeout=15,
            )
        elif self.filehash.upper() == "539EB689D2E0D3751AEED273385865278BEF6696C46BC0CAB116B40C3B2FE820":  # TSLPatcher (2009)
            subprocess.call(
                args=[
                    executable,
                    "-d",
                    f"{source_filepath!s}",
                    "-o",
                    f"{output_filepath!s}",
                ],
                cwd=str(self.nwnnsscomp_path.parent),
                timeout=15,
            )
        else:  # TODO: dencs? what is this?
            gameIndex = "--kotor2" if game == Game.K2 else "--kotor"
            command = [str(self.nwnnsscomp_path), gameIndex, str(source_filepath)]

            # Execute the command and redirect the output directly to a file
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            if process.returncode:
                raise ValueError(error.decode())
            with output_filepath.open("w") as file:
                file.write(output.decode(errors="ignore"))

        return True
