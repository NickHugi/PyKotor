from __future__ import annotations

from typing import TYPE_CHECKING, Iterable, Sequence

from qtpy.QtCore import QEvent, QObject
from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent

from pykotor.tools.encoding import decode_bytes_with_fallbacks

if TYPE_CHECKING:
    from qtpy.QtCore import QByteArray, QMimeData


def print_qt_object(  # noqa: C901
    obj: QObject,
    exclude_classes: Sequence[type] | None = None,
):  # noqa: C901
    def get_base_class_attributes(base_classes: Iterable[type[object]]) -> set[str]:
        attrs = set()
        for base_class in base_classes:
            attrs.update(dir(base_class))
        return attrs

    def print_filtered_attributes(
        obj: object,
        obj_name: str,
        exclude_attrs: Iterable[str],
    ):
        print(f"{obj_name} Attributes:")
        for attr in dir(obj):
            if (
                not attr.startswith(("_", "set"))
                and not callable(getattr(obj, attr))
                and attr not in exclude_attrs
            ):
                try:
                    print(f"  {attr}: {getattr(obj, attr)}")
                except Exception as ex:  # noqa: BLE001
                    print(f"  {attr}: Unable to retrieve value ({ex.__class__.__name__}: {ex})")

    def byte_array_to_hex(byte_array: QByteArray) -> str:
        return "".join(f"{b:02x}" for b in byte_array.data())

    exclude_classes_list: list[type] = [QObject, QEvent, object] if exclude_classes is None else list(exclude_classes)
    exclude_attrs: set[str] = get_base_class_attributes(exclude_classes_list)
    print_filtered_attributes(obj, "Event", exclude_attrs)

    if isinstance(obj, (QDropEvent, QDragMoveEvent, QDragEnterEvent)):
        mime_data: QMimeData | None = obj.mimeData()
        if mime_data is None:
            return
        print_filtered_attributes(mime_data, "Mime Data", exclude_attrs)
        formats: list[str] = list(mime_data.formats())
        print("Available MimeData Formats:")
        for format in formats:
            print(f" - {format}")
        for format in formats:
            data: QByteArray | None = mime_data.data(format)
            if data is None:
                continue
            hex_data: str = byte_array_to_hex(data)
            print(f"Data for format {format}: {hex_data[:100]}")
            try:
                decoded_data: str = decode_bytes_with_fallbacks(data.data()[:100])
            except UnicodeDecodeError as decode_error:
                print(f"UnicodeDecodeError: {decode_error}")
                decoded_data = "Error decoding data"
            print(f"Decoded data for format {format}: {decoded_data}")
