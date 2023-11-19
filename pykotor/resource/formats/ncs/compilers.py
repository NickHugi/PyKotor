from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, ClassVar

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, write_ncs
from pykotor.resource.formats.ncs.ncs_data import NCSCompiler
from pykotor.utility.misc import generate_filehash_sha256
from pykotor.utility.path import Path

if TYPE_CHECKING:
    import os


class InbuiltNCSCompiler(NCSCompiler):
    def compile_script(self, source_path: str, output_path: str, game: Game) -> None:
        source = BinaryReader.load_file(source_path).decode(errors="ignore")
        ncs = compile_nss(source, game)
        write_ncs(ncs, output_path)


class ExternalNCSCompiler(NCSCompiler):
    NWNNSSCOMP_SHA256_HASHES: ClassVar[dict[str, str]] = {
        "TSLPatcher": "539EB689D2E0D3751AEED273385865278BEF6696C46BC0CAB116B40C3B2FE820",  # TSLPatcher (2009)
        "Kotor Tool": "E36AA3172173B654AE20379888EDDC9CF45C62FBEB7AB05061C57B52961C824D",  # KotorTool (2005)
        "v1": "EC3E657C18A32AD13D28DA0AA3A77911B32D9661EA83CF0D9BCE02E1C4D8499D",          # v1 (2004)
    }

    class NwnnsscompConfig:
        """Unifies the arguments passed to each different version of nwnnsscomp. No versions offer backwards-compatibility with each other."""

        def __init__(self, sha256_hash: str, source: Path, output: Path, game_value: Game) -> None:
            self.sha256_hash: str = sha256_hash
            self.source: Path = source
            self.output: Path = output
            self.output_dir: Path = output.parent
            self.output_name: str = output.name
            self.game_value: Game = game_value
            self.compile_args: list[str] = []
            self.decompile_args: list[str] = []
            self._configure_based_on_hash()

        def get_compile_args(self, executable: str) -> list[str]:
            return self._format_args(self.compile_args, executable)

        def get_decompile_args(self, executable: str) -> list[str]:
            return self._format_args(self.decompile_args, executable)

        def _configure_based_on_hash(self) -> None:
            arg_configurations: dict[str, dict[str, list[str]]] = {
                ExternalNCSCompiler.NWNNSSCOMP_SHA256_HASHES["TSLPatcher"]: {
                    "compile": ["-c", "{source}", "-o", "{output}"],
                    "decompile": ["-d", "{source}", "-o", "{output}"],
                },
                ExternalNCSCompiler.NWNNSSCOMP_SHA256_HASHES["Kotor Tool"]: {
                    "compile": ["-c", "--outputdir", "{output_dir}", "-o", "{output_name}", "-g", "{game_value}", "--optimize", "{source}"],
                    "decompile": ["-d", "--outputdir", "{output_dir}", "-o", "{output_name}", "-g", "{game_value}", "{source}"],
                },
                ExternalNCSCompiler.NWNNSSCOMP_SHA256_HASHES["v1"]: {
                    "compile": ["-c", "-o", "{source}", "{output}"],
                    "decompile": ["-d", "{source}", "{output}"],
                },
            }

            config = arg_configurations.get(self.sha256_hash)
            if config:
                self.compile_args = config["compile"]
                self.decompile_args = config["decompile"]
            else:
                msg = "Unknown NWNNSSCOMP hash"
                raise ValueError(msg)

        def _format_args(self, args_list: list[str], executable: str) -> list[str]:
            formatted_args: list[str] = [arg.format(
                source=self.source,
                output=self.output,
                output_dir=self.output_dir,
                output_name=self.output_name,
                game_value=self.game_value,
            ) for arg in args_list]
            formatted_args.insert(0, executable)
            return formatted_args

    def __init__(self, nwnnsscomp_path: os.PathLike | str) -> None:
        self.nwnnsscomp_path: Path = nwnnsscomp_path if isinstance(nwnnsscomp_path, Path) else Path(nwnnsscomp_path)
        self.filehash: str = generate_filehash_sha256(self.nwnnsscomp_path).upper()
        self.config: ExternalNCSCompiler.NwnnsscompConfig | None = None

    def configure(self, source_file: os.PathLike | str, output_file: os.PathLike | str, game: Game | int) -> NwnnsscompConfig:
        """Configures a Nwnnsscomp run
        Args:
            source_file: Path to the source file to compile
            output_file: Path to output file to generate
            game: Game enum or integer to configure in one line
        Returns:
            NwnnsscompConfig: Config object for Nwnnsscomp run
        Processes Logic:
            - Resolves source and output file paths
            - Converts game arg to Game enum if integer
            - Returns NwnnsscompConfig object configured with args useable with the compile_script and decompile_script functions.
        """
        source_filepath, output_filepath = (p.resolve() for p in map(Path, (source_file, output_file)))
        if not isinstance(game, Game):
            game = Game(game)
        return self.NwnnsscompConfig(self.filehash, source_filepath, output_filepath, game)

    def compile_script(
        self,
        source_file: os.PathLike | str,
        output_file: os.PathLike | str,
        game: Game | int,
        timeout: int=5,
    ) -> None:
        """Compiles a NSS script into NCS using the external compiler.
        Function is compatible with any nwnnsscomp.exe versions.

        Args:
        ----
            source_file: Path or name of the source file to compile
            output_file: Path or name of the output file
            game: Game object or ID of the game module
            timeout - Optional[int]: How long to wait for compiling to finish. Defaults to 5 seconds.

        Returns:
        -------
            None

        Processing Logic:
        - Checks if configuration exists and configures if not
        - Calls nwnnsscomp to compile the source file using the configuration
        - Waits up to the provided timeout seconds for compilation process to complete.
        """
        if not self.config:
            self.config = self.configure(source_file, output_file, game)

        subprocess.call(
            args = self.config.get_compile_args(str(self.nwnnsscomp_path)),
            timeout=timeout,
        )


    def decompile_script(
        self,
        source_file: os.PathLike | str,
        output_file: os.PathLike | str,
        game: Game | int,
        timeout: int=5,
    ) -> None:
        """Decompiles a script file into C# source code.

        Args:
        ----
            source_file: Path to the script file to decompile.
            output_file: Path to output the decompiled C# source code.
            game: The Game object containing configuration.
            timeout - Optional[int]: How long to wait for decompiling to finish. Defaults to 5 seconds.

        Returns:
        -------
            None

        Processing Logic:
        - Checks if configuration exists and configures if not
        - Calls nwnnsscomp subprocess to decompile script file using configuration
        - Waits up to the provided timeout seconds for decompilation process to complete.
        """
        if not self.config:
            self.config = self.configure(source_file, output_file, game)

        subprocess.call(
            args = self.config.get_decompile_args(str(self.nwnnsscomp_path)),
            timeout=timeout,
        )
