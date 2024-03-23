from __future__ import annotations

import subprocess

from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs.compiler.classes import EntryPointError
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, write_ncs
from pykotor.resource.formats.ncs.ncs_data import NCSCompiler
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.misc import generate_hash
from utility.system.path import Path

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.ncs.ncs_data import NCS, NCSOptimizer


class InbuiltNCSCompiler(NCSCompiler):
    def compile_script(  # noqa: PLR0913
        self,
        source_path: os.PathLike | str,
        output_path: os.PathLike | str,
        game: Game,
        optimizers: list[NCSOptimizer] | None = None,
        *,
        debug: bool = False,
    ):
        source_filepath: Path = Path.pathify(source_path)
        nss_data: bytes = BinaryReader.load_file(source_filepath)
        nss_contents: str = decode_bytes_with_fallbacks(nss_data)  # .replace('#include "k_inc_debug"', "")
        ncs: NCS = compile_nss(nss_contents, game, optimizers, library_lookup=[source_filepath.parent], debug=debug)
        write_ncs(ncs, output_path)


class ExternalCompilerFeatures(NamedTuple):
    can_compile: bool
    can_decompile: bool


class ExternalCompilerConfig(NamedTuple):
    sha256: str
    name: str
    release_date: date
    author: str
    features: ExternalCompilerFeatures
    commandline: dict[str, list[str]]


class KnownExternalCompilers(Enum):
    TSLPATCHER = ExternalCompilerConfig(
        sha256="539EB689D2E0D3751AEED273385865278BEF6696C46BC0CAB116B40C3B2FE820",
        name="TSLPatcher",
        release_date=date(2009, 1, 1),
        author="todo",
        features=ExternalCompilerFeatures(can_compile=True, can_decompile=True),
        commandline={
            "compile": ["-c", "{source}", "-o", "{output}"],
            "decompile": ["-d", "{source}", "-o", "{output}"],
        },
    )
    KOTOR_TOOL = ExternalCompilerConfig(
        sha256="E36AA3172173B654AE20379888EDDC9CF45C62FBEB7AB05061C57B52961C824D",
        name="KOTOR Tool",
        release_date=date(2005, 1, 1),
        author="Fred Tetra",
        features=ExternalCompilerFeatures(can_compile=True, can_decompile=True),
        commandline={
            "compile": ["-c", "--outputdir", "{output_dir}", "-o", "{output_name}", "-g", "{game_value}", "{source}"],
            "decompile": ["-d", "--outputdir", "{output_dir}", "-o", "{output_name}", "-g", "{game_value}", "{source}"],
        },
    )
    V1 = ExternalCompilerConfig(
        sha256="EC3E657C18A32AD13D28DA0AA3A77911B32D9661EA83CF0D9BCE02E1C4D8499D",
        name="v1.3 first public release",
        release_date=date(2003, 12, 31),
        author="todo",
        features=ExternalCompilerFeatures(can_compile=True, can_decompile=True),
        commandline={
            "compile": ["-c", "{source}", "{output}"],
            "decompile": ["-d", "{source}", "{output}"],
        },
    )
    KOTOR_SCRIPTING_TOOL = ExternalCompilerConfig(
        sha256="B7344408A47BE8780816CF68F5A171A09640AB47AD1A905B7F87DE30A50A0A92",
        name="KOTOR Scripting Tool",
        release_date=date(2016, 5, 18),
        author="James Goad",  # TODO: double check
        features=ExternalCompilerFeatures(can_compile=True, can_decompile=True),
        commandline={
            "compile": ["-c", "--outputdir", "{output_dir}", "-o", "{output_name}", "-g", "{game_value}", "{source}"],
            "decompile": ["-d", "--outputdir", "{output_dir}", "-o", "{output_name}", "-g", "{game_value}", "{source}"],
        },
    )
    DENCS = ExternalCompilerConfig(
        sha256="539EB689D2E0D3751AEED273385865278BEF6696C46BC0CAB116B40C3B2FE820",
        name="DeNCS",
        release_date=date(2006, 5, 30),
        author="todo",
        features=ExternalCompilerFeatures(can_compile=True, can_decompile=True),
        commandline={},
    )
    XOREOS = ExternalCompilerConfig(
        sha256="todo",
        name="Xoreos Tools",
        release_date=date(1, 1, 1),
        author="todo",
        features=ExternalCompilerFeatures(can_compile=False, can_decompile=True),
        commandline={},
    )
    KNSSCOMP = ExternalCompilerConfig(  # TODO: add hash and look for this in tslpatcher.reader.ConfigReader.load_compile_list()
        sha256="todo",
        name="knsscomp",
        release_date=date(1, 1, 1),  # 2022?
        author="Nick Hugi",
        features=ExternalCompilerFeatures(can_compile=True, can_decompile=False),
        commandline={},
    )

    @classmethod
    def from_sha256(cls: type[KnownExternalCompilers], sha256: str) -> KnownExternalCompilers:
        uppercase_sha256: str = sha256.upper()
        for known_ext_compiler in cls:
            if known_ext_compiler.value.sha256 == uppercase_sha256:
                return known_ext_compiler

        msg = f"No compilers found with sha256 hash '{uppercase_sha256}'"
        raise ValueError(msg)


class NwnnsscompConfig:
    """Unifies the arguments passed to each different version of nwnnsscomp, since no versions offer backwards-compatibility with each other."""

    def __init__(
        self,
        sha256_hash: str,
        sourcefile: Path,
        outputfile: Path,
        game: Game,
    ):
        self.sha256_hash: str = sha256_hash
        self.source_file: Path = sourcefile
        self.output_file: Path = outputfile
        self.output_dir: Path = outputfile.parent
        self.output_name: str = outputfile.name
        self.game: Game = game

        self.chosen_compiler: KnownExternalCompilers = KnownExternalCompilers.from_sha256(self.sha256_hash)

    def get_compile_args(self, executable: str) -> list[str]:
        return self._format_args(self.chosen_compiler.value.commandline["compile"], executable)

    def get_decompile_args(self, executable: str) -> list[str]:
        return self._format_args(self.chosen_compiler.value.commandline["decompile"], executable)

    def _format_args(self, args_list: list[str], executable: str) -> list[str]:
        formatted_args: list[str] = [
            arg.format(
                source=self.source_file,
                output=self.output_file,
                output_dir=self.output_dir,
                output_name=self.output_name,
                game_value="1" if self.game.is_k1() else "2",
            )
            for arg in args_list
        ]
        formatted_args.insert(0, executable)
        return formatted_args


class ExternalNCSCompiler(NCSCompiler):
    def __init__(self, nwnnsscomp_path: os.PathLike | str):
        self.nwnnsscomp_path: Path
        self.filehash: str
        self.change_nwnnsscomp_path(nwnnsscomp_path)

    def get_info(self) -> ExternalCompilerConfig:
        return KnownExternalCompilers.from_sha256(self.filehash).value

    def change_nwnnsscomp_path(self, nwnnsscomp_path: os.PathLike | str):
        self.nwnnsscomp_path: Path = Path.pathify(nwnnsscomp_path)
        self.filehash: str = generate_hash(self.nwnnsscomp_path, hash_algo="sha256").upper()

    def config(
        self,
        source_file: os.PathLike | str,
        output_file: os.PathLike | str,
        game: Game | int,
        *,
        debug: bool = False,
    ) -> NwnnsscompConfig:
        """Configures a Nwnnsscomp run.

        Args:
        ----
            source_file: Path to the source file to compile
            output_file: Path to output file to generate
            game: Game enum or integer to configure in one line
            debug - bool (kwarg): Whether to debug Ply and verbosely output more information. Defaults to False.

        Returns:
        -------
            NwnnsscompConfig: Config object for Nwnnsscomp run

        Processing Logic:
        ----------------
            - Resolves source and output file paths
            - Converts game arg to Game enum if integer
            - Returns NwnnsscompConfig object configured with args useable with the compile_script and decompile_script functions.
        """
        source_filepath, output_filepath = map(Path.pathify, (source_file, output_file))
        if not isinstance(game, Game):
            game = Game(game)
        return NwnnsscompConfig(self.filehash, source_filepath, output_filepath, game)

    def compile_script(
        self,
        source_file: os.PathLike | str,
        output_file: os.PathLike | str,
        game: Game | int,
        timeout: int = 5,
        *,
        debug: bool = False,
    ) -> tuple[str, str]:
        """Compiles a NSS script into NCS using the external compiler.

        Function is compatible with any nwnnsscomp.exe version.

        Args:
        ----
            source_file: The path or name of the script source file to compile.
            output_file: The path or name of the compiled module file to output.
            game: The Game object or game ID to configure the compiler for.
            timeout: The timeout in seconds to wait for compilation to finish before aborting.
            debug - bool (kwarg): (does nothing for external compilers)

        Returns:
        -------
            A tuple of (stdout, stderr) strings from the compilation process.

        Processing Logic:
        ----------------
            - Configures the compiler based on the nwnnsscomp.exe used.
            - Runs the compiler process, capturing stdout and stderr.
            - Returns a tuple of the stdout and stderr strings on completion.

        Raises:
        ------
            - EntryPointError: File has no entry point and is an include file, so it could not be compiled.
        """
        config: NwnnsscompConfig = self.config(source_file, output_file, game)

        result: subprocess.CompletedProcess[str] = subprocess.run(
            args=config.get_compile_args(str(self.nwnnsscomp_path)),
            capture_output=True,  # Capture stdout and stderr
            text=True,
            timeout=timeout,
            check=False,
        )

        stdout, stderr = self._get_output(result)
        if "File is an include file, ignored" in stdout:
            msg = "This file has no entry point and cannot be compiled (Most likely an include file)."
            raise EntryPointError(msg)

        return stdout, stderr

    def decompile_script(
        self,
        source_file: os.PathLike | str,
        output_file: os.PathLike | str,
        game: Game | int,
        timeout: int = 5,
    ) -> tuple[str, str]:
        """Decompiles a script file into C# source code.

        Args:
        ----
            source_file: (os.PathLike | str) - Path to the script file to decompile.
            output_file: (os.PathLike | str) - Path to output the decompiled C# source code.
            game: (Game) - The Game object containing configuration.
            timeout: (int) - How long to wait for decompiling to finish before aborting. Defaults to 5 seconds.

        Processing Logic:
        ----------------
            - Checks if configuration exists and configures if not
            - Calls nwnnsscomp subprocess to decompile script file using configuration
            - Waits up to the provided timeout seconds for decompilation process to complete.
        """
        config: NwnnsscompConfig = self.config(source_file, output_file, game)

        result: subprocess.CompletedProcess[str] = subprocess.run(
            args=config.get_decompile_args(str(self.nwnnsscomp_path)),
            capture_output=True,  # Capture stdout and stderr
            text=True,
            timeout=timeout,
            check=False,
        )

        return self._get_output(result)

    def _get_output(self, result: subprocess.CompletedProcess[str]) -> tuple[str, str]:
        stdout: str = result.stdout
        stderr: str = (
            f"no error provided but return code is nonzero: ({result.returncode})"
            if result.returncode != 0 and (not result.stderr or not result.stderr.strip())
            else result.stderr
        )

        if "Error:" in stdout:
            stdout_lines: list[str] = stdout.split("\n")
            error_line: str = ""
            # Find and remove the line with 'Error:'
            filtered_stdout_lines: list[str] = []
            for line in stdout_lines:
                if "Error:" in line:
                    error_line += "\n" + line
                else:
                    filtered_stdout_lines.append(line)

            # Reconstruct stdout without the error line
            stdout = "\n".join(filtered_stdout_lines)

            # Append the error line to stderr if it was found
            if error_line:
                if stderr:  # If there's already content in stderr, add a newline before appending
                    stderr += "\n" + error_line
                else:
                    stderr = error_line
        return stdout, stderr
