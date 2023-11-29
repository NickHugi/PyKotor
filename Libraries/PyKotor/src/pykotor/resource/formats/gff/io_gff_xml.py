from __future__ import annotations

import base64
from typing import Any
from xml.etree import ElementTree

from defusedxml.ElementTree import fromstring
from pykotor.common.geometry import Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import ResRef
from pykotor.resource.formats.gff.gff_data import GFF, GFFFieldType, GFFList, GFFStruct
from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES, ResourceReader, ResourceWriter, autoclose
from pykotor.utility.misc import indent


class GFFXMLReader(ResourceReader):
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._gff: GFF | None = None

    @autoclose
    def load(
        self,
        auto_close: bool = True,
    ) -> GFF:
        self._gff = GFF()

        data = self._reader.read_bytes(self._reader.size()).decode()
        xml_root = fromstring(data).find("struct")
        self._load_struct(self._gff.root, xml_root)

        return self._gff

    def _load_struct(
        self,
        gff_struct: GFFStruct,
        xml_struct,
    ):
        gff_struct.struct_id = int(xml_struct.get("id"))

        for xml_field in xml_struct:
            self._load_field(gff_struct, xml_field)

    def _load_field(
        self,
        gff_struct: GFFStruct,
        xml_field,
    ):
        label = xml_field.get("label")

        if xml_field.tag == "byte":
            gff_struct.set_uint8(label, int(xml_field.text))
        elif xml_field.tag == "char":
            gff_struct.set_int8(label, int(xml_field.text))
        elif xml_field.tag == "uint16":
            gff_struct.set_uint16(label, int(xml_field.text))
        elif xml_field.tag == "sint16":
            gff_struct.set_int16(label, int(xml_field.text))
        elif xml_field.tag == "uint32":
            gff_struct.set_uint32(label, int(xml_field.text))
        elif xml_field.tag == "sint32":
            gff_struct.set_int32(label, int(xml_field.text))
        elif xml_field.tag == "uint64":
            gff_struct.set_uint64(label, int(xml_field.text))
        elif xml_field.tag == "sint65":
            gff_struct.set_int64(label, int(xml_field.text))
        elif xml_field.tag == "float":
            gff_struct.set_single(label, float(xml_field.text))
        elif xml_field.tag == "double":
            gff_struct.set_double(label, float(xml_field.text))
        elif xml_field.tag == "exostring":
            gff_struct.set_string(label, xml_field.text)
        elif xml_field.tag == "resref":
            gff_struct.set_resref(label, ResRef(xml_field.text))
        elif xml_field.tag == "locstring":
            locstring = LocalizedString(-1)
            locstring.stringref = -1 if xml_field.get("strref") == "4294967295" else int(xml_field.get("strref"))
            for substring in xml_field:
                language, gender = LocalizedString.substring_pair(
                    int(substring.get("language")),
                )
                locstring.set_data(language, gender, substring.text)
            gff_struct.set_locstring(label, locstring)
        elif xml_field.tag == "data":
            data = base64.b64decode(xml_field.text)
            gff_struct.set_binary(label, data)
        elif xml_field.tag == "orientation":
            coords = xml_field.findall("double")
            v4 = Vector4(
                float(coords[0].text),
                float(coords[1].text),
                float(coords[2].text),
                float(coords[3].text),
            )
            gff_struct.set_vector4(label, v4)
        elif xml_field.tag == "vector":
            coords = xml_field.findall("double")
            v3 = Vector3(
                float(coords[0].text),
                float(coords[1].text),
                float(coords[2].text),
            )
            gff_struct.set_vector3(label, v3)
        elif xml_field.tag == "struct":
            child_struct = GFFStruct()
            self._load_struct(child_struct, xml_field)
            gff_struct.set_struct(label, child_struct)
        elif xml_field.tag == "list":
            gff_list = GFFList()
            for xml_struct in xml_field:
                gff_list.add(0)
                child_struct = gff_list.at(len(gff_list) - 1)
                self._load_struct(child_struct, xml_struct)
            gff_struct.set_list(label, gff_list)


class GFFXMLWriter(ResourceWriter):
    def __init__(
        self,
        gff: GFF,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self.xml_root = ElementTree.Element("xml")
        self.gff: GFF = gff

    @autoclose
    def write(
        self,
        auto_close: bool = True,
    ) -> None:
        self.xml_root.tag = "gff3"

        xml_struct = ElementTree.Element("struct")
        self.xml_root.append(xml_struct)
        self._build_struct(self.gff.root, xml_struct)

        indent(self.xml_root)
        self._writer.write_bytes(ElementTree.tostring(self.xml_root))

    def _build_struct(
        self,
        gff_struct: GFFStruct,
        xml_struct: ElementTree.Element,
    ):
        xml_struct.set("id", str(gff_struct.struct_id))

        for label, field_type, value in gff_struct:
            self._build_field(label, value, field_type, xml_struct)

    def _build_field(
        self,
        label: str,
        value: Any,
        field_type: GFFFieldType,
        xml_struct: ElementTree.Element,
    ):
        xml_field = ElementTree.Element("")
        xml_field.set("label", label)
        xml_struct.append(xml_field)

        if field_type == GFFFieldType.UInt8:
            xml_field.tag = "byte"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.Int8:
            xml_field.tag = "char"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.UInt16:
            xml_field.tag = "uint16"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.Int16:
            xml_field.tag = "sint16"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.UInt32:
            xml_field.tag = "uint32"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.Int32:
            xml_field.tag = "sint32"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.UInt64:
            xml_field.tag = "uint64"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.Int64:
            xml_field.tag = "sint64"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.Single:
            xml_field.tag = "float"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.Double:
            xml_field.tag = "double"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.String:
            xml_field.tag = "exostring"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.ResRef:
            xml_field.tag = "resref"
            xml_field.text = str(value)
        elif field_type == GFFFieldType.LocalizedString:
            xml_field.tag = "locstring"
            locstring: LocalizedString = value
            xml_field.set("strref", str(locstring.stringref))
            for language, gender, string in locstring:
                subelement = ElementTree.Element("string")
                subelement.set(
                    "language",
                    str(LocalizedString.substring_id(language, gender)),
                )
                subelement.text = string
                xml_field.append(subelement)
        elif field_type == GFFFieldType.Binary:
            xml_field.tag = "data"
            xml_field.text = base64.b64encode(value).decode()
        elif field_type == GFFFieldType.Vector3:
            self._build_vector3(xml_field, value)
        elif field_type == GFFFieldType.Vector4:
            self._build_vector4(xml_field, value)
        elif field_type == GFFFieldType.Struct:
            xml_field.tag = "struct"
            self._build_struct(value, xml_field)
        elif field_type == GFFFieldType.List:
            xml_field.tag = "list"
            for gff_struct in value:
                subelement = ElementTree.Element("struct")
                xml_field.append(subelement)
                self._build_struct(gff_struct, subelement)

    def _build_vector3(self, xml_field: ElementTree.Element, value):
        xml_field.tag = "vector"
        x_element = ElementTree.Element("double")
        x_element.text = str(value.x)
        y_element = ElementTree.Element("double")
        y_element.text = str(value.y)
        z_element = ElementTree.Element("double")
        z_element.text = str(value.z)
        xml_field.extend([x_element, y_element, z_element])

    def _build_vector4(self, xml_field: ElementTree.Element, value):
        xml_field.tag = "orientation"
        x_element = ElementTree.Element("double")
        x_element.text = str(value.x)
        y_element = ElementTree.Element("double")
        y_element.text = str(value.y)
        z_element = ElementTree.Element("double")
        z_element.text = str(value.z)
        w_element = ElementTree.Element("double")
        w_element.text = str(value.w)
        xml_field.extend([x_element, y_element, z_element, w_element])
