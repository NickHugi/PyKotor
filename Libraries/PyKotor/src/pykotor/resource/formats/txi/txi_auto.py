from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES


def read_txi(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
):
    # if isinstance(source, (os.PathLike, str)):
    #    txi = TXI()
    #    with Path(source).open("r", encoding="utf-8") as f:
    #        for line in f.readlines():
    #            key, value = line.split(" ", maxsplit=1)
    #            setattr(txi, key, value)
    pass
