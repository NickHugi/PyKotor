from __future__ import annotations
from pykotor.resource.formats.gff.gff_data import (
    GFF,
    GFFList,
    GFFStruct,
    GFFFieldType,
    GFFContent,
    GFFComparisonResult,
)
from pykotor.resource.formats.gff.io_gff import (
    GFFBinaryReader,
    GFFBinaryWriter,
)
from pykotor.resource.formats.gff.io_gff_xml import (
    GFFXMLReader,
    GFFXMLWriter,
)
from pykotor.resource.formats.gff.gff_auto import write_gff, read_gff, detect_gff, bytes_gff

__all__ = [
    "GFF",
    "GFFComparisonResult",
    "GFFBinaryReader",
    "GFFBinaryWriter",
    "GFFContent",
    "GFFFieldType",
    "GFFList",
    "GFFStruct",
    "GFFXMLReader",
    "GFFXMLWriter",
    "bytes_gff",
    "detect_gff",
    "read_gff",
    "write_gff",
]
