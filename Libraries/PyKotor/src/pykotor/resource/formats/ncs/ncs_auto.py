from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.common.scriptdefs import KOTOR_CONSTANTS, KOTOR_FUNCTIONS, TSL_CONSTANTS, TSL_FUNCTIONS
from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.io_ncs import NCSBinaryReader, NCSBinaryWriter
from pykotor.resource.formats.ncs.ncs_data import NCS
from pykotor.resource.formats.ncs.optimizers import RemoveNopOptimizer
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from ply import yacc

    from pykotor.common.misc import Game
    from pykotor.resource.formats.ncs.ncs_data import NCSOptimizer
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES
    from utility.system.path import Path


def read_ncs(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> NCS:
    """Returns an NCS instance from the source.

    Args:
    ----
        source: The source of the data.
        offset: The byte offset of the file inside the data.
        size: Number of bytes to allowed to read from the stream. If not specified, uses the whole stream.

    Raises:
    ------
        ValueError: If the file was corrupted or in an unsupported format.

    Returns:
    -------
        An NCS instance.
    """
    return NCSBinaryReader(source, offset, size or 0).load()


def write_ncs(
    ncs: NCS,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.NCS,
):
    """Writes the NCS data to the target location with the specified format (NCS only).

    Args:
    ----
        ncs: The NCS file being written.
        target: The location to write the data to.
        file_format: The file format.

    Raises:
    ------
        ValueError: If an unsupported file format was given.
    """
    if file_format is ResourceType.NCS:
        NCSBinaryWriter(ncs, target).write()
    else:
        msg = "Unsupported format specified; use NCS."
        raise ValueError(msg)


def bytes_ncs(
    ncs: NCS,
    file_format: ResourceType = ResourceType.NCS,
) -> bytearray:
    """Returns the NCS data in the specified format (NCS only) as a bytes object.

    This is a convenience method that wraps the write_ncs() method.

    Args:
    ----
        ncs: The target NCS object.
        file_format: The file format.

    Raises:
    ------
        ValueError: If an unsupported file format was given.

    Returns:
    -------
        The NCS data.
    """
    data = bytearray()
    write_ncs(ncs, data, file_format)
    return data


def compile_nss(
    source: str,
    game: Game,
    optimizers: list[NCSOptimizer] | None = None,
    library_lookup: list[str | Path] | list[Path] | list[str] | str | Path | None = None,
    *,
    errorlog: yacc.NullLogger | None = None,
    debug: bool = False,
) -> NCS:
    """Returns NCS object compiled from input source string.

    Attributes:
    ----------
        source: The source code.
        game: Target game for the NCS object.
        optimizers: What post-compilation optimizers to apply to the NCS object.
    """
    NssLexer()
    nss_parser = NssParser(
        functions=KOTOR_FUNCTIONS if game.is_k1() else TSL_FUNCTIONS,
        constants=KOTOR_CONSTANTS if game.is_k1() else TSL_CONSTANTS,
        library=KOTOR_LIBRARY if game.is_k1() else TSL_LIBRARY,
        library_lookup=library_lookup,
        errorlog=errorlog,
        debug=debug,
    )

    ncs = NCS()

    block = nss_parser.parser.parse(source, tracking=True, debug=debug)
    block.compile(ncs)

    if not optimizers or not any(isinstance(optimizer, RemoveNopOptimizer) for optimizer in optimizers):
        optimizers = [RemoveNopOptimizer()] + (optimizers or [])

    for optimizer in optimizers:
        optimizer.reset()
    ncs.optimize(optimizers)
    return ncs
