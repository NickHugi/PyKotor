from __future__ import annotations

import json

from typing import TYPE_CHECKING, Any

from pykotor.resource.formats.lip.lip_data import LIP, LIPShape
from pykotor.resource.type import ResourceReader, ResourceWriter, autoclose
from pykotor.tools.encoding import decode_bytes_with_fallbacks

if TYPE_CHECKING:
    from typing_extensions import TypedDict  # pyright: ignore[reportMissingModuleSource]

    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES

    class LIPKeyframeDict(TypedDict):
        time: str
        shape: str

    class LIPJSONDict(TypedDict):
        duration: str
        keyframes: list[LIPKeyframeDict]


class LIPJSONReader(ResourceReader):
    """Reads LIP files from JSON format.
    
    JSON is a PyKotor-specific convenience format for easier editing of lip-sync data.
    
    References:
    ----------
        Note: JSON format is PyKotor-specific, not a standard game format
    """
    def __init__(
        self,
        source: SOURCE_TYPES,
        offset: int = 0,
        size: int = 0,
    ):
        super().__init__(source, offset, size)
        self._json: dict[str, Any] = {}
        self._lip: LIP | None = None

    @autoclose
    def load(self, *, auto_close: bool = True) -> LIP:  # noqa: FBT001, FBT002, ARG002
        self._lip = LIP()
        self._json = json.loads(decode_bytes_with_fallbacks(self._reader.read_bytes(self._reader.size())))

        if "lip" not in self._json:
            msg = "The JSON file that was loaded was not a valid LIP."
            raise ValueError(msg)

        self._lip.length = float(self._json["lip"]["duration"])

        for subelement in self._json["lip"]["elements"]:
            time = float(subelement["time"])
            shape = LIPShape(int(subelement["shape"]))
            self._lip.add(time, shape)

        return self._lip



class LIPJSONWriter(ResourceWriter):
    def __init__(
        self,
        lip: LIP,
        target: TARGET_TYPES,
    ):
        super().__init__(target)
        self._lip: LIP = lip
        self._json: LIPJSONDict = {
            "duration": str(self._lip.length),
            "keyframes": [],
        }

    @autoclose
    def write(self, *, auto_close: bool = True):  # noqa: FBT001, FBT002, ARG002  # pyright: ignore[reportUnusedParameters]
        # Populate the dictionary with keyframe data
        for keyframe in self._lip:
            self._json["keyframes"].append(
                LIPKeyframeDict(
                    time=str(keyframe.time),
                    shape=str(keyframe.shape.value),
                )
            )

        json_string: str = json.dumps(self._json, indent=4)
        self._writer.write_bytes(json_string.encode())
