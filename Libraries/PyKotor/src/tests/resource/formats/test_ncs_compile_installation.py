from __future__ import annotations

import os
import pathlib
import sys
import unittest
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from pykotor.tools.encoding import decode_bytes_with_fallbacks

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
        #    cls.k1_installation = cls.load_installation('K1_PATH', 'k1_installation.pkl')  # type: ignore[attr-defined]
        #if K2_PATH is not None:
        #    cls.k2_installation = cls.load_installation('K2_PATH', 'k2_installation.pkl')  # type: ignore[attr-defined]


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
        ext_compiler = ExternalNCSCompiler(NWNNSSCOMP_PATH)
        nwnnsscomp_result: tuple[str, str] = ext_compiler.compile_script(temp_nss_path, temp_ncs_path, game)
        stdout, stderr = nwnnsscomp_result
        print("nwnnsscomp.exe", "path:", temp_nss_path, "stdout:", stdout, f"stderr:\t{stderr}" if stderr else "")
        if stderr.strip() or not temp_ncs_path.is_file():
            return False

        inbuilt_compiler = InbuiltNCSCompiler()
        inbuilt_compiler.compile_script(temp_nss_path, temp_ncs_path, game)
        try:
            assert temp_ncs_path.is_file(), f"{temp_ncs_path} not found on disk!"
        except AssertionError as e:
            print("#2 (InbuiltNCSCompiler's `Path.is_file()` failed)", e)
            return False
        else:
            return True

    def compile_and_compare(
        self,
        resource: FileResource,
        game: Game,
        script_folderpath: Path,
    ):
        nss_source_str: str = decode_bytes_with_fallbacks(resource.data())
        pykotor_compiled_result: NCS | None = None
        try:
            pykotor_compiled_result = compile_nss(nss_source_str, game, library_lookup=script_folderpath)
        except CompileError as e:
            print(f"#3 (compile_nss): Add '{resource.identifier()}' to incompatible")
            with Path("pykotor_incompatible.txt").open("a") as f:
                f.write(f"\n{resource.identifier()}")
        test2_result: NCS | None = None
        try:
            test2_result = self.compile(nss_source_str, KOTOR_LIBRARY, script_folderpath)
        except CompileError as e:
            print("#5 (self.compile): Add '{resource.identifier()}' to incompatible")
            return
        error_msg: str = (
            f"Script '{resource.identifier()}' failed to compile consistently (from {resource.filepath()}):{os.linesep*2}"
            #f"{pykotor_compiled_result.print()} != {test2_result.print()}"
        )
        try:
            assert pykotor_compiled_result == test2_result, error_msg
        except AssertionError as e:
            print(e)
            print(f"#1 (eq check failed between compiled scripts): Add '{resource.identifier()}' to incompatible")
            #with Path("pykotor_incompatible.txt").open("a") as f:
            #    f.write(f"\n{resource.identifier()}")

    def compile_entire_install(
        self,
        game: Game,
        installation: Installation,
    ):
        assert NWNNSSCOMP_PATH is not None
        extracted_scripts: list[tuple[Path, Path]] = []
        with TemporaryDirectory() as tempdir:
            temp_dirpath = Path(tempdir)
            for resource in installation:
                if resource.identifier() in KNOWN_PROBLEM_NSS[game]:
                    print(f"Skipping {resource.identifier()}, known incompatible...")
                    continue
                if resource.restype() != ResourceType.NSS:
                    continue

                temp_nss_path: Path = temp_dirpath.joinpath(str(resource.identifier()))
                temp_ncs_path: Path = temp_nss_path.with_suffix(".ncs")
                with temp_nss_path.open("w") as f:
                    str_script: str = decode_bytes_with_fallbacks(resource.data())
                    lines: list[str] = str_script.replace("\r", "").split("\n")
                    f.writelines(lines)

                extracted_scripts.append((temp_nss_path, temp_ncs_path))

            for this_script in extracted_scripts:
                this_script_nss, this_script_ncs = this_script
                if not self.compile_script_and_assert_existence(this_script_nss, this_script_ncs, game):
                    print("#4 (nwnnsscomp.exe)", f"{resource.identifier()} is incompatible.")
                    with Path("nwnnsscomp_incompatible.txt").open("a") as f:
                        f.write(f"\n{resource.identifier()}")
                    continue

                self.compile_and_compare(resource, game, temp_dirpath)


    @unittest.skipIf(
        not K1_PATH or not pathlib.Path(K1_PATH).joinpath("chitin.key").is_file(),
        "K1_PATH environment variable is not set or not found on disk.",
    )
    def test_k1_compile_entire_install(self):
        assert K1_PATH is not None
        self.compile_entire_install(Game.K1, Installation(K1_PATH))  # type: ignore[attr-defined]

    @unittest.skipIf(
        not K2_PATH or not pathlib.Path(K2_PATH).joinpath("chitin.key").is_file(),
        "K2_PATH environment variable is not set or not found on disk.",
    )
    def test_k2_compile_entire_install(self):
        assert K2_PATH is not None
        self.compile_entire_install(Game.K2, Installation(K2_PATH))  # type: ignore[attr-defined]

if __name__ == "__main__":
    unittest.main()
