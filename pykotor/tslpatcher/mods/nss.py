from __future__ import annotations

import os
import re
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

from pykotor.common.misc import decode_bytes_with_fallbacks
from pykotor.common.stream import BinaryReader
from pykotor.helpers.path import Path, PurePath
from pykotor.resource.formats.ncs import bytes_ncs
from pykotor.resource.formats.ncs import compile_nss as compile_with_builtin
from pykotor.resource.formats.ncs.compilers import ExternalNCSCompiler
from pykotor.resource.type import SOURCE_TYPES
from pykotor.tslpatcher.mods.template import PatcherModifications

if TYPE_CHECKING:
    from pykotor.common.misc import Game
    from pykotor.tslpatcher.logger import PatchLogger
    from pykotor.tslpatcher.memory import PatcherMemory


class ModificationsNSS(PatcherModifications):
    def __init__(self, filename, replace=None, modifiers=None) -> None:
        super().__init__(filename, replace, modifiers)
        self.saveas = str(PurePath(filename).with_suffix(".ncs"))
        self.action: str = "Compile"
        self.nwnnsscomp_path: Path

    def apply(self, nss_source: SOURCE_TYPES, memory: PatcherMemory, logger: PatchLogger, game: Game) -> bytes:
        """Takes the source nss bytes and replaces instances of 2DAMEMORY# and StrRef# with the relevant data.

        Args:
        ----
            nss_source (SOURCE_TYPES): The source script to patch. (path or bytes object)
            memory (PatcherMemory): Memory references for patching.
            logger (PatchLogger): Logger for logging messages.
            game (Game IntEnum): The game being patched.

        Returns:
        -------
            bytes: The patched bytes.
        Processing Logic:
            1. Decodes bytes to a string
            2. Replaces #2DAMEMORY# tokens with values from PatcherMemory
            3. Replaces #StrRef# tokens with values from PatcherMemory
            4. Compiles the patched string and encodes to bytes.
        """
        nss_bytes: bytes
        if isinstance(nss_source, bytearray):
            nss_bytes = bytes(nss_source)
        elif isinstance(nss_source, bytes):
            nss_bytes = nss_source
        elif isinstance(nss_source, (os.PathLike, str)):
            nss_bytes = BinaryReader.load_file(nss_source)
        else:
            logger.add_error(f"Invalid nss source provided to ModificationsNSS.apply(), got {type(nss_source)}")
            return b""

        source: str = decode_bytes_with_fallbacks(nss_bytes)

        match = re.search(r"#2DAMEMORY\d+#", source)
        while match:
            token_id = int(source[match.start() + 10 : match.end() - 1])
            value_str: str = memory.memory_2da[token_id]
            source = source[: match.start()] + value_str + source[match.end() :]
            match = re.search(r"#2DAMEMORY\d+#", source)

        match = re.search(r"#StrRef\d+#", source)
        while match:
            token_id = int(source[match.start() + 7 : match.end() - 1])
            value = memory.memory_str[token_id]
            source = source[: match.start()] + str(value) + source[match.end() :]
            match = re.search(r"#StrRef\d+#", source)

        if os.name == "posix":
            # Compile using built-in script compiler.
            return bytes_ncs(compile_with_builtin(source, game))
        if os.name == "nt":
            # Compile using nwnnsscomp.exe on windows.
            #  1. Create a temporary directory
            #  2. Compile script with nwnnsscomp.exe's CLI to that directory.
            #  3. Load newly compiled script as bytes and return them.
            #  4. cleanup the temp dir
            with TemporaryDirectory() as tempdir:
                tempdir_path = Path(tempdir)
                source_script = self.nwnnsscomp_path.parent / self.sourcefile
                tempcompiled_filepath = tempdir_path / "temp_script.ncs"

                nwnnsscompiler = ExternalNCSCompiler(self.nwnnsscomp_path)
                nwnnsscompiler.compile_script(source_script, tempcompiled_filepath, game)
                compiled_bytes: bytes = BinaryReader.load_file(tempcompiled_filepath)
                return compiled_bytes

        logger.add_error("Operating system not supported - cannot compile script.")
        return b""

    def pop_tslpatcher_vars(self, file_section_dict, default_destination=PatcherModifications.DEFAULT_DESTINATION):
        super().pop_tslpatcher_vars(file_section_dict, default_destination)
        # TODO: Need to handle HACKList here and in apply.
