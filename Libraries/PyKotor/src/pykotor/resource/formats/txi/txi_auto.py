from __future__ import annotations

import os
from typing import TYPE_CHECKING

from utility.system.path import Path

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES


def read_txi(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
):
    #if isinstance(source, (os.PathLike, str)):
    #    txi = TXI()
    #    with Path.pathify(source).open("r") as f:
    #        for line in f.readlines():
    #            key, value = line.split(" ", maxsplit=1)
    #            setattr(txi, key, value)
    pass
