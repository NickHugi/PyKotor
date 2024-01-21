from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, ClassVar

from pykotor.common.misc import Game
from pykotor.common.stream import BinaryReader
from pykotor.resource.formats.ncs.ncs_auto import compile_nss, write_ncs
from pykotor.resource.formats.ncs.ncs_data import NCSCompiler
from pykotor.tools.path import CaseAwarePath
from utility.misc import generate_hash
from utility.path import Path

if TYPE_CHECKING:
    import os

    from pykotor.resource.formats.ncs.ncs_data import NCS


class InbuiltNCSCompiler(NCSCompiler):
    """A class representing an inbuilt NCS compiler.

    This class provides functionality to compile a NSS script into NCS using an inbuilt compiler.

    Methods:
    -------
        compile_script(source_path, output_path, game): Compiles a NSS script into NCS.

    Args:
    ----
        source_path (os.PathLike | str): The path to the source file to compile.
        output_path (os.PathLike | str): The path to the output file to generate.
        game (Game): The Game enum value.
    """

    def compile_script(self, source_path: os.PathLike | str, output_path: os.PathLike | str, game: Game) -> None:
        """Compiles a NSS script into NCS.

        Args:
        ----
            source_path: The path to the source file to compile.
            output_path: The path to the output file to generate.
            game: The Game enum value.
        """
        source_path_obj = CaseAwarePath(source_path)
        source = BinaryReader.load_file(source_path_obj).decode(errors="ignore")
        ncs: NCS = compile_nss(source, game, library_lookup=[source_path_obj.parent])
        write_ncs(ncs, output_path)


class ExternalNCSCompiler(NCSCompiler):
    """A class representing an external NCS compiler.

    This class provides functionality to configure and use an external NCS compiler for compiling and decompiling NSS scripts.

    Args:
    ----
        nwnnsscomp_path: The path to the nwnnsscomp executable.

    Attributes:
    ----------
        nwnnsscomp_path (Path): The path to the nwnnsscomp executable.
        filehash (str): The SHA256 hash of the nwnnsscomp executable.
        config (NwnnsscompConfig | None): The configuration object for the NCS compiler.

    Methods:
    -------
        configure(source_file, output_file, game): Configures a Nwnnsscomp run.
        compile_script(source_file, output_file, game, timeout=5): Compiles a NSS script into NCS using the external compiler.
        decompile_script(source_file, output_file, game, timeout=5): Decompiles a script file into C# source code.
    """

    NWNNSSCOMP_SHA256_HASHES: ClassVar[dict[str, str]] = {
        "TSLPatcher": "539EB689D2E0D3751AEED273385865278BEF6696C46BC0CAB116B40C3B2FE820",  # TSLPatcher (2009)
        "Kotor Tool": "E36AA3172173B654AE20379888EDDC9CF45C62FBEB7AB05061C57B52961C824D",  # KotorTool (2005)
        "v1": "EC3E657C18A32AD13D28DA0AA3A77911B32D9661EA83CF0D9BCE02E1C4D8499D",          # v1 (2004)
        "DeNCS": "DD1ECD396AAB6F4C731DED70A7BA91299F0F2159ECBDF10F2E54A15C5D0888BC",       # DeNCS.jar Beta 2 (May 30 2006)
    }

    class NwnnsscompConfig:
        """Unifies the arguments passed to each different version of nwnnsscomp. No versions offer backwards-compatibility with each other.

        Args:
        ----
            sha256_hash (str): The SHA256 hash of the nwnnsscomp executable.
            source (Path): The path to the source file to compile.
            output (Path): The path to the output file to generate.
            game_value (Game): The Game enum value.

        Attributes:
        ----------
            sha256_hash (str): The SHA256 hash of the nwnnsscomp executable.
            source (Path): The path to the source file to compile.
            output (Path): The path to the output file to generate.
            output_dir (Path): The parent directory of the output file.
            output_name (str): The name of the output file.
            game_value (Game): The Game enum value.
            compile_args (list[str]): The arguments for compilation.
            decompile_args (list[str]): The arguments for decompilation.

        Methods:
        -------
            get_compile_args(executable): Returns the formatted compilation arguments.
            get_decompile_args(executable): Returns the formatted decompilation arguments.
        """

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

            config: dict[str, list[str]] | None = arg_configurations.get(self.sha256_hash)
            if config is None:
                msg = "Unknown NWNNSSCOMP hash"
                raise ValueError(msg)
            self.compile_args = config["compile"]
            self.decompile_args = config["decompile"]

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
        self.nwnnsscomp_path: Path = Path.pathify(nwnnsscomp_path)  # type: ignore[reportGeneralTypeIssues, assignment]
        self.filehash: str = generate_hash(self.nwnnsscomp_path, hash_algo="sha256").upper()
        self.config: ExternalNCSCompiler.NwnnsscompConfig | None = None

    def configure(self, source_file: os.PathLike | str, output_file: os.PathLike | str, game: Game | int) -> NwnnsscompConfig:
        """Configures a Nwnnsscomp run.

        Args:
        ----
            source_file: Path to the source file to compile
            output_file: Path to output file to generate
            game: Game enum or integer to configure in one line

        Returns:
        -------
            NwnnsscompConfig: Config object for Nwnnsscomp run

        Processing Logic:
        ----------------
            - Resolves source and output file paths
            - Converts game arg to Game enum if integer
            - Returns NwnnsscompConfig object configured with args useable with the compile_script and decompile_script functions.
        """
        source_filepath, output_filepath = (p if p.exists() else p.resolve() for p in map(Path, (source_file, output_file)))
        if not isinstance(game, Game):
            game = Game(game)
        return self.NwnnsscompConfig(self.filehash, source_filepath, output_filepath, game)

    def compile_script(
        self,
        source_file: os.PathLike | str,
        output_file: os.PathLike | str,
        game: Game | int,
        timeout: int=5,
    ) -> tuple[str, str]:
        """Compiles a NSS script into NCS using the external compiler.

        Function is compatible with any nwnnsscomp.exe version.

        Args:
        ----
            source_file: The path or name of the script source file to compile.
            output_file: The path or name of the compiled module file to output.
            game: The Game object or game ID to configure the compiler for.
            timeout: The timeout in seconds for the compilation process.

        Returns:
        -------
            A tuple of (stdout, stderr) strings from the compilation process.

        Processing Logic:
        ----------------
            - Configures the compiler based on the nwnnsscomp.exe used.
            - Runs the compiler process, capturing stdout and stderr.
            - Returns a tuple of the stdout and stderr strings on completion.
        """
        if not self.config:
            self.config = self.configure(source_file, output_file, game)

        result = subprocess.run(
            args=self.config.get_compile_args(str(self.nwnnsscomp_path)),
            capture_output=True,  # Capture stdout and stderr
            text=True,
            timeout=timeout,
            check=False,
        )

        stderr_message = result.stderr or f"no error provided but return code is nonzero: {result.returncode}"
        return result.stdout, stderr_message if result.returncode != 0 else result.stderr


    def decompile_script(
        self,
        source_file: os.PathLike | str,
        output_file: os.PathLike | str,
        game: Game | int,
        timeout: int=5,
    ) -> tuple[str, str]:
        """Decompiles a script file into C# source code.

        Args:
        ----
            source_file: Path to the script file to decompile.
            output_file: Path to output the decompiled C# source code.
            game: The Game object containing configuration.
            timeout - int | None: How long to wait for decompiling to finish. Defaults to 5 seconds.

        Processing Logic:
        ----------------
            - Checks if configuration exists and configures if not
            - Calls nwnnsscomp subprocess to decompile script file using configuration
            - Waits up to the provided timeout seconds for decompilation process to complete.
        """
        if not self.config:
            self.config = self.configure(source_file, output_file, game)

        result = subprocess.run(
            args=self.config.get_decompile_args(str(self.nwnnsscomp_path)),
            capture_output=True,  # Capture stdout and stderr
            text=True,
            timeout=timeout,
            check=False,
        )

        stderr_message = result.stderr or f"no error provided but return code is nonzero: {result.returncode}"
        return result.stdout, stderr_message if result.returncode != 0 else result.stderr
