from __future__ import annotations

import io
import pytest
from pykotor.resource.formats.txi import TXI, read_txi, write_txi, bytes_txi

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import LiteralString


@pytest.fixture
def sample_txi_data() -> LiteralString:
    return """
    mipmap 0
    filter 0
    numchars 256
    fontheight 0.500000
    baselineheight 0.400000
    texturewidth 1.000000
    fontwidth 1.000000
    spacingR 0.002600
    spacingB 0.100000
    caretindent -0.010000
    isdoublebyte 0
    upperleftcoords 256
    0.000000 0.000000 0
    0.062500 0.000000 0
    0.125000 0.000000 0
    lowerrightcoords 256
    0.062500 0.125000 0
    0.125000 0.125000 0
    0.187500 0.125000 0
    """


@pytest.fixture
def sample_txi(sample_txi_data: LiteralString) -> TXI:
    return read_txi(io.BytesIO(sample_txi_data.encode()))


def test_read_txi(sample_txi_data: LiteralString, sample_txi: TXI):
    assert isinstance(sample_txi, TXI)
    assert sample_txi.features.mipmap == False
    assert sample_txi.features.filter == False
    assert sample_txi.features.numchars == 256
    assert sample_txi.features.fontheight == 0.5
    assert len(sample_txi.features.upperleftcoords) == 256
    assert len(sample_txi.features.lowerrightcoords) == 256


def test_write_txi(sample_txi: TXI):
    output = bytearray()
    write_txi(sample_txi, output)
    output.seek(0)
    written_txi = read_txi(output)

    assert written_txi.features.mipmap == sample_txi.features.mipmap
    assert written_txi.features.filter == sample_txi.features.filter
    assert written_txi.features.numchars == sample_txi.features.numchars
    assert written_txi.features.fontheight == sample_txi.features.fontheight
    assert len(written_txi.features.upperleftcoords) == len(sample_txi.features.upperleftcoords)
    assert len(written_txi.features.lowerrightcoords) == len(sample_txi.features.lowerrightcoords)


def test_bytes_txi(sample_txi: TXI):
    txi_bytes = bytes_txi(sample_txi)
    assert isinstance(txi_bytes, bytes)

    read_back_txi = read_txi(io.BytesIO(txi_bytes))
    assert read_back_txi.features.mipmap == sample_txi.features.mipmap
    assert read_back_txi.features.filter == sample_txi.features.filter
    assert read_back_txi.features.numchars == sample_txi.features.numchars
    assert read_back_txi.features.fontheight == sample_txi.features.fontheight


if __name__ == "__main__":
    pytest.main()
