from __future__ import annotations

import os
import pathlib
import sys
import unittest
from io import StringIO
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING, ClassVar

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[3].resolve()
UTILITY_PATH = THIS_SCRIPT_PATH.parents[5].joinpath("Utility", "src").resolve()
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.misc import Game
from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS
from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation
from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import CompileError, EntryPointError
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, InbuiltNCSCompiler
from pykotor.resource.formats.ncs.ncs_auto import compile_nss
from pykotor.resource.type import ResourceType
from pykotor.tools.encoding import decode_bytes_with_fallbacks
from utility.error_handling import format_exception_with_variables
from utility.system.path import Path

if TYPE_CHECKING:
    from ply import yacc
    from pykotor.extract.file import FileResource

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
NWNNSSCOMP_PATH: str | None = r"C:/Program Files (x86)/KotOR Scripting Tool/nwnnsscomp.exe"
NWNNSSCOMP_PATH2: str | None = r"C:\Program Files (x86)\Kotor Tool\nwnnsscomp.exe"
NWNNSSCOMP_PATH3: str | None = r"C:\Users\boden\Documents\k1 mods\KillCzerkaJerk\tslpatchdata\nwnnsscomp.exe"
LOG_FILENAME = "test_ncs_compilers_install"
ORIG_LOGSTEM = "test_ncs_compilers_install"

CANNOT_COMPILE_EXT: dict[Game, set[ResourceIdentifier]] = {
    Game.K1: {
        ResourceIdentifier("nwscript", ResourceType.NSS),
    },
    Game.K2: {
        ResourceIdentifier("nwscript", ResourceType.NSS),
    },
}
CANNOT_COMPILE_BUILTIN: dict[Game, set[ResourceIdentifier]] = {
    Game.K1: {
        ResourceIdentifier("a_102attattack", ResourceType.NSS),
        ResourceIdentifier("k_act_atkonend", ResourceType.NSS),
        ResourceIdentifier("k_act_bandatt", ResourceType.NSS),
        ResourceIdentifier("e3_scripts", ResourceType.NSS),
        ResourceIdentifier("nwscript", ResourceType.NSS),
    },
    Game.K2: {
        ResourceIdentifier("nwscript", ResourceType.NSS),
    },
}



def bizarre_compiler(
    script: str,
    game: Game,
    library: dict[str, bytes] | None = None,
    library_lookup: list[str | Path] | list[str] | list[Path] | str | Path | None = None,
) -> NCS:
    if not library:
        library = KOTOR_LIBRARY if game == Game.K1 else TSL_LIBRARY
    _nssLexer = NssLexer()
    nssParser = NssParser(
        library=library,
        constants=KOTOR_CONSTANTS,
        functions=KOTOR_FUNCTIONS,
        library_lookup=library_lookup
    )

    parser: yacc.LRParser = nssParser.parser
    t = parser.parse(script, tracking=True)

    ncs = NCS()
    t.compile(ncs)
    return ncs

@unittest.skipIf(
    (
        not NWNNSSCOMP_PATH
        or not Path(NWNNSSCOMP_PATH).exists()
        or (
            not K1_PATH
            or not Path(K1_PATH).joinpath("chitin.key").exists()
        )
        and (
            not K2_PATH
            or not Path(K2_PATH).joinpath("chitin.key").exists()
        )
    ),
    "K1_PATH/K2_PATH/NWNNSSCOMP_PATH environment variable is not set or not found on disk.",
)
class TestCompileInstallation(unittest.TestCase):

    # define these here otherwise mypy complains
    ext_compiler1: ExternalNCSCompiler | None = ExternalNCSCompiler(NWNNSSCOMP_PATH) if NWNNSSCOMP_PATH and Path(NWNNSSCOMP_PATH).exists() else None
    ext_compiler2: ExternalNCSCompiler | None = ExternalNCSCompiler(NWNNSSCOMP_PATH2) if NWNNSSCOMP_PATH2 and Path(NWNNSSCOMP_PATH2).exists() else None
    ext_compiler3: ExternalNCSCompiler | None = ExternalNCSCompiler(NWNNSSCOMP_PATH3) if NWNNSSCOMP_PATH3 and Path(NWNNSSCOMP_PATH3).exists() else None
    inbuilt_compiler = InbuiltNCSCompiler()
    all_scripts: ClassVar[dict[Game, list[tuple[FileResource, Path, Path]]]] = {
        Game.K1: [],
        Game.K2: [],
    }
    all_nss_paths: ClassVar[dict[Game, Path]] = {
        Game.K1: Path(TemporaryDirectory().name),
        Game.K2: Path(TemporaryDirectory().name)
    }
    installations: dict[Game, Installation] = {}

    @classmethod
    def setUpClass(cls):
        try:
            # Remove old files
            Path.cwd().joinpath("pykotor_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath("inbuilt_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath("nwnnsscomp_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath("nwnnsscomp2_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath("nwnnsscomp3_incompatible.txt").unlink(missing_ok=True)
            Path.cwd().joinpath(f"{ORIG_LOGSTEM}_k1.txt").unlink(missing_ok=True)
            Path.cwd().joinpath(f"{ORIG_LOGSTEM}_k2.txt").unlink(missing_ok=True)

            for path in cls.all_nss_paths.values():
                path.mkdir(parents=True)

            # Load installations
            if K1_PATH is not None and Path(K1_PATH).joinpath("chitin.key").exists():
                cls.installations[Game.K1] = Installation(K1_PATH)
                cls.setup_extracted_scripts(Game.K1)
            if K2_PATH is not None and Path(K2_PATH).joinpath("chitin.key").exists():
                cls.installations[Game.K2] = Installation(K2_PATH)
                cls.setup_extracted_scripts(Game.K2)
        except Exception:
            cls.tearDownClass()
            raise # to still mark the test as failed.

    @classmethod
    def tearDownClass(cls):
        import shutil
        shutil.rmtree(cls.all_nss_paths[Game.K1], ignore_errors=True)
        shutil.rmtree(cls.all_nss_paths[Game.K2], ignore_errors=True)

    @classmethod
    def setup_extracted_scripts(
        cls,
        game: Game,
    ):
        for resource in cls.installations[game]:
            if resource.identifier() in CANNOT_COMPILE_EXT[game]:
                cls.log_file(f"Skipping {resource.identifier()}, known incompatible...")
                continue
            if resource.restype() != ResourceType.NSS:
                continue

            temp_nss_path: Path = cls.all_nss_paths[game].joinpath(str(resource.identifier()))
            temp_ncs_path: Path = temp_nss_path.with_suffix(".ncs")
            with temp_nss_path.open("w") as f:
                str_script: str = decode_bytes_with_fallbacks(resource.data())
                lines: list[str] = str_script.replace("\r", "").split("\n")
                f.writelines(lines)

            cls.all_scripts[game].append((resource, temp_nss_path, temp_ncs_path))

    @staticmethod
    def log_file(
        *args,
        filepath: os.PathLike | str | None = None,
        file: StringIO | None = None,
        **kwargs,
    ):
        # Create an in-memory text stream
        buffer: StringIO = file or StringIO()
        # Print to the in-memory stream
        print(*args, file=buffer, **kwargs)

        # Retrieve the printed content
        msg: str = buffer.getvalue()

        # Print the captured output to console
        print(*args, **kwargs)  # noqa: T201

        filepath = (
            Path.cwd().joinpath(f"{LOG_FILENAME}.txt")
            if filepath is None
            else Path.pathify(filepath)
        )
        with filepath.open(mode="a", encoding="utf-8", errors="strict") as f:
            f.write(msg)

    def compile_with_abstract_compatible(
        self,
        compiler: ExternalNCSCompiler | InbuiltNCSCompiler | None,
        nss_path: Path,
        ncs_path: Path,
        game: Game,
    ) -> Path | None:
        if compiler is None:
            return None
        if isinstance(compiler, ExternalNCSCompiler):
            stdout, stderr = compiler.compile_script(nss_path, ncs_path, game)
            self.log_file(game, compiler.nwnnsscomp_path, "path:", nss_path, "stdout:", stdout, f"stderr:\t{stderr}" if stderr else "")
        else:
            compiler.compile_script(nss_path, ncs_path, game)
        return ncs_path

    def _test_nwnnsscomp_compiles(self, game):
        for script_info in self.all_scripts[game]:
            file_res, nss_path, ncs_path = script_info
            compiled_paths: list[Path | None] = [
                self.compile_with_abstract_compatible(self.ext_compiler1, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_ext1"), game),
                self.compile_with_abstract_compatible(self.ext_compiler2, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_ext2"), game),
                self.compile_with_abstract_compatible(self.ext_compiler3, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_ext3"), game)
            ]

            # Filter out None paths (from compilers that weren't defined)
            compiled_paths = [path for path in compiled_paths if path is not None]

            # Check if all existing paths have the same existence status
            if not compiled_paths:
                return

            existence_status: list[bool] = [path.exists() for path in compiled_paths]
            assert all(status == existence_status[0] for status in existence_status), \
                f"Mismatch in compilation results: {[path for path, exists in zip(compiled_paths, existence_status) if not exists]}"

    def _test_inbuilt_compiler(self, game: Game):
        for script_info in self.all_scripts[game]:
            file_res, nss_path, ncs_path = script_info
            if file_res.identifier() in CANNOT_COMPILE_BUILTIN[game]:
                self.log_file(f"Skipping {file_res.identifier()}, known incompatible with inbuilt...")
                continue

            try:
                compiled_path: Path | None =  self.compile_with_abstract_compatible(self.inbuilt_compiler, nss_path, ncs_path.with_stem(f"{ncs_path.stem}_inbuilt"), game)
            except EntryPointError as e:
                ...
            except CompileError as e:
                #self.log_file(nss_path.name, filepath="inbuilt_incompatible.txt")
                self.fail(f"Could not compile {nss_path.name} with inbuilt!{os.linesep*2} {format_exception_with_variables(e)}")
            else:
                #if not compiled_path.exists():
                #    self.log_file(nss_path.name, filepath="inbuilt_incompatible.txt")
                assert compiled_path.exists(), f"{compiled_path} could not be found on disk, inbuilt compiler failed."

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_nwnnsscomp_compiles(self):
        self._test_nwnnsscomp_compiles(Game.K1)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_nwnnsscomp_compiles(self):
        self._test_nwnnsscomp_compiles(Game.K2)

    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_inbuilt_compiler(self):
        self._test_inbuilt_compiler(Game.K1)

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_inbuilt_compiler(self):
        self._test_inbuilt_compiler(Game.K2)


if __name__ == "__main__":
    unittest.main()
