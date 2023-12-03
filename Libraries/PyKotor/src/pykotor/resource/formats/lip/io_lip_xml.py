from __future__ import annotations

from contextlib import suppress

# Try to import defusedxml, fallback to ElementTree if not available
from xml.etree import ElementTree

with suppress(ImportError):
    from defusedxml.ElementTree import fromstring as _fromstring
    ElementTree.fromstring = _fromstring

from pykotor.resource.formats.lip.lip_data import LIP, LIPShape
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter, autoclose
from utility.misc import indent


class LIPXMLReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._lip: LIP | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> LIP:
        self._lip = LIP()

        data = self._reader.read_bytes(self._reader.size()).decode()
        xml_root = ElementTree.fromstring(data)  # noqa: S314

        if xml_root.tag != "lip":
            msg = "The XML file that was loaded was not a valid LIP."
            raise ValueError(msg)

        self._lip.length = float(xml_root.get("duration"))

        for subelement in xml_root:
            time = float(subelement.get("time"))
            shape = LIPShape(int(subelement.get("shape")))
            self._lip.add(time, shape)

        return self._lip


class LIPXMLWriter(ResourceWriter):
    def __init__(
        self,
        lip: LIP,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._lip = lip
        self._xml_root: ElementTree.Element = ElementTree.Element("lip")

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        self._xml_root.set("duration", str(self._lip.length))

        for keyframe in self._lip:
            ElementTree.SubElement(
                self._xml_root,
                "keyframe",
                time=str(keyframe.time),
                shape=str(keyframe.shape.value),
            )

        indent(self._xml_root)
        self._writer.write_bytes(ElementTree.tostring(self._xml_root))
