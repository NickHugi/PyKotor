from pykotor.common.misc import Game
from pykotor.common.scriptdefs import (
    KOTOR_CONSTANTS,
    KOTOR_FUNCTIONS,
    TSL_CONSTANTS,
    TSL_FUNCTIONS,
)
from pykotor.common.scriptlib import KOTOR_LIBRARY, TSL_LIBRARY
from pykotor.resource.formats.ncs import NCS, NCSBinaryReader, NCSBinaryWriter
from pykotor.resource.formats.ncs.compiler.lexer import NssLexer
from pykotor.resource.formats.ncs.compiler.parser import NssParser
from pykotor.resource.formats.ncs.ncs_data import NCSOptimizer
from pykotor.resource.formats.ncs.optimizers import (
    RemoveNopOptimizer,
)
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceType


def read_ncs(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int = None,
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
    return NCSBinaryReader(source, offset, size).load()


def write_ncs(
    ncs: NCS,
    target: TARGET_TYPES,
    file_format: ResourceType = ResourceType.NCS,
) -> None:
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
    if file_format == ResourceType.NCS:
        NCSBinaryWriter(ncs, target).write()
    else:
        msg = "Unsupported format specified; use NCS."
        raise ValueError(msg)


def bytes_ncs(
    ncs: NCS,
    file_format: ResourceType = ResourceType.NCS,
) -> bytes:
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
    library_lookup: list[str] | None = None,
) -> NCS:
    """Returns NCS object compiled from input source string.

    Attributes
    ----------
        source: The source code.
        game: Target game for the NCS object.
        optimizers: What post-compilation optimizers to apply to the NCS object.
    """
    NssLexer()
    nss_parser = NssParser(
        library=KOTOR_LIBRARY if game == Game.K1 else TSL_LIBRARY,
        functions=KOTOR_FUNCTIONS if game == Game.K1 else TSL_FUNCTIONS,
        constants=KOTOR_CONSTANTS if game == Game.K1 else TSL_CONSTANTS,
        library_lookup=library_lookup,
    )

    ncs = NCS()

    block = nss_parser.parser.parse(source, tracking=True)
    block.compile(ncs)

    optimizers = (
        [RemoveNopOptimizer()]
        if optimizers is None
        else [RemoveNopOptimizer(), *optimizers]
    )
    for optimizer in optimizers:
        optimizer.reset()
    ncs.optimize(optimizers)
    return ncs
