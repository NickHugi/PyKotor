from __future__ import annotations

from typing import TYPE_CHECKING

# Try to import defusedxml, fallback to ET if not available
from xml.etree import ElementTree as ET

try:  # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
    from defusedxml.ElementTree import fromstring
except (ImportError, ModuleNotFoundError):
    from xml.etree import ElementTree as ET

    fromstring = ET.fromstring

from pykotor.resource.formats.lip.lip_data import LIP, LIPShape
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose
from utility.misc import indent

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class LIPXMLReader(ResourceReader):
    """Reads LIP files from XML format.
    
    XML is a human-readable format for easier editing of lip-sync animation data.
    
    References:
    ----------
        vendor/xoreos-tools/src/xml/lipdumper.cpp (LIP to XML conversion)
        vendor/xoreos-tools/src/xml/lipcreator.cpp (XML to LIP conversion)
        Note: XML format structure may vary between tools
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._lip: LIP | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> LIP:  # noqa: FBT001, FBT002, ARG002
        self._lip = LIP()

        data: str = self._reader.read_bytes(self._reader.size()).decode()
        xml_root: ET.Element = fromstring(data)  # noqa: S314

        if xml_root.tag != "lip":
            msg = "The XML file that was loaded was not a valid LIP."
            raise ValueError(msg)

        duration: str | None = xml_root.get("duration")
        if duration is None:
            msg = "Missing duration of the LIP."
            raise ValueError(msg)
        self._lip.length = float(duration)

        for subelement in xml_root:
            time: str | None = subelement.get("time")
            if time is None:
                msg = "Missing time for a keyframe."
                raise ValueError(msg)

            shape: str | None = subelement.get("shape")
            if shape is None:
                msg = "Missing shape for a keyframe."
                raise ValueError(msg)
            self._lip.add(float(time), LIPShape(int(shape)))

        return self._lip


class LIPXMLWriter(ResourceWriter):
    def __init__(
        self,
        lip: LIP,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._lip: LIP = lip
        self._xml_root: ET.Element = ET.Element("lip")

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        self._xml_root.set("duration", str(self._lip.length))

        for keyframe in self._lip:
            ET.SubElement(
                self._xml_root,
                "keyframe",
                time=str(keyframe.time),
                shape=str(keyframe.shape.value),
            )

        indent(self._xml_root)
        self._writer.write_bytes(ET.tostring(self._xml_root))
