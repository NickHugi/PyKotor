from __future__ import annotations

import os
import pathlib
import sys
import unittest
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

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
from pykotor.common.scriptlib import KOTOR_LIBRARY
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation
from pykotor.resource.formats.ncs import NCS
from pykotor.resource.formats.ncs.compiler.classes import CompileError
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler, InbuiltNCSCompiler
from pykotor.resource.formats.ncs.ncs_auto import compile_nss
from pykotor.resource.type import ResourceType
from utility.system.path import Path

if TYPE_CHECKING:
    from ply import yacc
    from pykotor.extract.file import FileResource

K1_PATH: str | None = os.environ.get("K1_PATH")
K2_PATH: str | None = os.environ.get("K2_PATH")
NWNNSSCOMP_PATH: str | None = os.environ.get("NWNNSSCOMP_PATH")

KNOWN_PROBLEM_NSS: dict[Game, set[ResourceIdentifier]] = {
    Game.K1: {
        ResourceIdentifier("a_102attattack", ResourceType.NSS),
    },
    Game.K2: set(),
}

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
    @classmethod
    def setUpClass(cls):
        ...
        #if K1_PATH is not None:
        #    cls.k1_installation = Installation(K1_PATH)  # type: ignore[attr-defined]
        #if K2_PATH is not None:
        #    cls.k2_installation = Installation(K2_PATH)  # type: ignore[attr-defined]

    def compile(
        self,
        script: str,
        library: dict[str, bytes] | None = None,
        library_lookup: list[str | Path] | list[str] | list[Path] | str | Path | None = None,
    ) -> NCS:
        if library is None:
            library = {}
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

    def compile_script_and_assert_existence(
        self,
        temp_nss_path: Path,
        temp_ncs_path: Path,
        game: Game,
    ):
        assert NWNNSSCOMP_PATH is not None
        nwnnsscomp_result: tuple[str, str] = ExternalNCSCompiler(NWNNSSCOMP_PATH).compile_script(temp_nss_path, temp_ncs_path, game)
        stdout, stderr = nwnnsscomp_result
        print("nwnnsscomp.exe", "path:", temp_nss_path, "stdout:", stdout, f"stderr:\t{stderr}" if stderr else "")
        if stderr.strip() or not temp_ncs_path.is_file():
            return False

        InbuiltNCSCompiler().compile_script(temp_nss_path, temp_ncs_path, game)
        assert temp_ncs_path.is_file(), f"{temp_ncs_path} not found on disk!"
        return True

    def compile_and_compare(
        self,
        resource: FileResource,
        game: Game,
    ):
        nss_source_str: str = resource.data().decode("windows-1252", errors="strict")
        pykotor_compiled_result: NCS = compile_nss(nss_source_str, game)
        test2_result: NCS = self.compile(nss_source_str, KOTOR_LIBRARY)
        error_msg: str = (
            f"Script '{resource.identifier()}' failed to compile consistently (from {resource.filepath()}):{os.linesep*2}"
            #f"{pykotor_compiled_result.print()} != {test2_result.print()}"
        )
        try:
            assert pykotor_compiled_result == test2_result, error_msg
        except AssertionError as e:
            print(e)
            print(f"Add '{resource.identifier()}' to incompatible")
            with Path("incompatible.txt").open("a") as f:
                f.write(f"\n{resource.identifier()}")

    def compile_entire_install(
        self,
        game: Game,
        installation: Installation,
    ):
        assert NWNNSSCOMP_PATH is not None
        for resource in installation:
            if resource.identifier() in KNOWN_PROBLEM_NSS[game]:
                print(f"Skipping {resource.identifier()}, known incompatible...")
                continue
            if resource.restype() == ResourceType.NSS:
                with TemporaryDirectory() as tempdir:
                    temp_dirpath = Path(tempdir)
                    temp_nss_path: Path = temp_dirpath.joinpath("temp_script.nss")
                    temp_ncs_path: Path = temp_nss_path.with_suffix(".ncs")
                    with temp_nss_path.open("wb") as f:
                        f.write(resource.data())

                    if not self.compile_script_and_assert_existence(temp_nss_path, temp_ncs_path, game):
                        with Path("nwnnsscomp_incompatible.txt").open("a") as f:
                            f.write(f"\n{resource.identifier()}")
                        continue

                    self.compile_and_compare(resource, game)


    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_compile_entire_install(self):
        assert K1_PATH is not None
        self.compile_entire_install(Game.K1, Installation(K1_PATH))

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_compile_entire_install(self):
        assert K2_PATH is not None
        self.compile_entire_install(Game.K2, Installation(K2_PATH))

if __name__ == "__main__":
    unittest.main()
