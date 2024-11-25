"""Dialog link class for connecting nodes."""

from __future__ import annotations

import uuid

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Generic, TypeVar, cast

from pykotor.common.misc import Color, ResRef
from pykotor.resource.generics.dlg.nodes import DLGNode

if TYPE_CHECKING:
    from collections.abc import Generator

    from typing_extensions import Literal  # pyright: ignore[reportMissingModuleSource]

# Make T covariant to allow DLGLink[DLGEntry] to be used where DLGLink[DLGNode] is expected
T_co = TypeVar("T_co", bound=DLGNode, covariant=True)


class DLGLink(Generic[T_co]):
    """Represents a directed edge from a source node to a target node (DLGNode).

    Links are stored either in other nodes or in the starting list of the DLG. By design, all
    DLGLink objects must be unique.

    Attributes:
    ----------
        active1: "Active" field.
        comment: "LinkComment" field. Only used in links stored in nodes.
        is_child: "IsChild" field. Only used in links stored in nodes.
        active2: "Active2" field. KotOR 2 Only.
        logic: "Logic" field. KotOR 2 Only.
        active1_not: "Not" field. KotOR 2 Only.
        active2_not: "Not2" field. KotOR 2 Only.
        active1_param1: "Param1" field. KotOR 2 Only.
        active1_param2: "Param2" field. KotOR 2 Only.
        active1_param3: "Param3" field. KotOR 2 Only.
        active1_param4: "Param4" field. KotOR 2 Only.
        active1_param5: "Param5" field. KotOR 2 Only.
        active1_param6: "ParamStrA" field. KotOR 2 Only.
        active2_param1: "Param1b" field. KotOR 2 Only.
        active2_param2: "Param2b" field. KotOR 2 Only.
        active2_param3: "Param3b" field. KotOR 2 Only.
        active2_param4: "Param4b" field. KotOR 2 Only.
        active2_param5: "Param5b" field. KotOR 2 Only.
        active2_param6: "ParamStrB" field. KotOR 2 Only.
    """

    def __init__(
        self,
        node: T_co,
        list_index: int = -1,
    ):
        self._hash_cache: int = hash(uuid.uuid4().hex)
        self.active1: ResRef = ResRef.from_blank()
        self.node: T_co = node
        self.list_index: int = list_index

        # not in StartingList
        self.is_child: bool = False
        self.comment: str = ""

        # KotOR 2 Only:
        self.active2: ResRef = ResRef.from_blank()
        self.active1_not: bool = False
        self.active2_not: bool = False
        self.logic: bool = False

        self.active1_param1: int = 0
        self.active1_param2: int = 0
        self.active1_param3: int = 0
        self.active1_param4: int = 0
        self.active1_param5: int = 0
        self.active1_param6: str = ""

        self.active2_param1: int = 0
        self.active2_param2: int = 0
        self.active2_param3: int = 0
        self.active2_param4: int = 0
        self.active2_param5: int = 0
        self.active2_param6: str = ""

    def __iter__(self) -> Generator[DLGLink[T_co], Any, None]:
        """Iterate over nested links without recursion."""
        stack: list[DLGLink[T_co]] = [self]
        while stack:
            current: DLGLink[T_co] = stack.pop()
            yield current
            if not current.node:
                continue
            # Cast node.links to correct type since we know they're compatible
            stack.extend(cast(Sequence[DLGLink[T_co]], current.node.links))

    def __repr__(self) -> str:
        comment_str = str(self.comment)
        max_display = 30
        comment_display: str = (
            comment_str[:max_display]  # noqa: PLR2004
            if len(comment_str) > max_display
            else comment_str
        )
        return f"{self.__class__.__name__}(link_list_index={self.list_index}, comment={comment_display})"

    def __eq__(self, other):
        if self.__class__ is not other.__class__:
            return NotImplemented
        return self.__hash__() == other.__hash__()

    def __hash__(self) -> int:
        return self._hash_cache

    def partial_path(self, *, is_starter: bool) -> str:
        if is_starter:
            p1 = "StartingList"
        else:
            p1: Literal["EntriesList", "RepliesList", "StartingList"] = (
                "EntriesList"
                if self.node.__class__.__name__ == "DLGEntry"
                else "RepliesList"
            )
        return f"{p1}\\{self.list_index}"

    def to_dict(  # noqa: C901, PLR0912
        self,
        node_map: dict[str | int, Any] | None = None,
    ) -> dict[str | int, Any]:
        if node_map is None:
            node_map = {}

        link_key: int = hash(self)
        if link_key in node_map:
            return {"type": self.__class__.__name__, "ref": link_key}

        link_dict: dict[str | int, Any] = {
            "type": self.__class__.__name__,
            "key": link_key,
            "node": self.node.to_dict(node_map) if self.node else None,
            "link_list_index": self.list_index,
            "data": {},
        }

        for key, value in self.__dict__.items():
            if key.startswith("__"):
                continue
            if key in ("node", "list_index", "_hash_cache"):
                continue
            if isinstance(value, bool):
                link_dict["data"][key] = {"value": int(value), "py_type": "bool"}
            elif isinstance(value, int):
                link_dict["data"][key] = {"value": value, "py_type": "int"}
            elif isinstance(value, float):
                link_dict["data"][key] = {"value": value, "py_type": "float"}
            elif isinstance(value, str):
                link_dict["data"][key] = {"value": value, "py_type": "str"}
            elif isinstance(value, ResRef):
                link_dict["data"][key] = {"value": str(value), "py_type": "ResRef"}
            elif isinstance(value, Color):
                link_dict["data"][key] = {"value": value.bgr_integer(), "py_type": "Color"}
            elif isinstance(value, list):
                link_dict["data"][key] = {"value": value, "py_type": "list"}
            elif value is None:
                link_dict["data"][key] = {"value": None, "py_type": "None"}
            else:
                raise ValueError(f"Unsupported type: {value.__class__.__name__} for key: {key}")
        node_map[link_key] = link_dict

        return link_dict

    @classmethod
    def from_dict(  # noqa: C901, PLR0912
        cls,
        link_dict: dict[str | int, Any],
        node_map: dict[str | int, Any] | None = None,
    ) -> DLGLink[T_co]:
        if node_map is None:
            node_map = {}

        if "ref" in link_dict:
            return node_map[link_dict["ref"]]

        link_key: int = link_dict["key"]
        if link_key in node_map:
            return node_map[link_key]

        link: DLGLink[T_co] = object.__new__(cls)
        link._hash_cache = int(link_key)  # noqa: SLF001
        link.list_index = link_dict.get("link_list_index", -1)
        for key, value in link_dict["data"].items():
            if value is None:
                continue
            py_type: str | None = value.get("py_type")
            actual_value: Any = value.get("value")

            if py_type == "str":
                setattr(link, key, actual_value)
            elif py_type == "int":
                setattr(link, key, int(actual_value))
            elif py_type == "float":
                setattr(link, key, float(actual_value))
            elif py_type == "bool":
                setattr(link, key, bool(actual_value))
            elif py_type == "ResRef":
                setattr(link, key, ResRef(actual_value))
            elif py_type == "Color":
                setattr(link, key, Color.from_bgr_integer(actual_value))
            elif py_type == "list":
                setattr(link, key, actual_value)
            elif py_type == "None" or actual_value == "None":
                setattr(link, key, None)
            else:
                raise ValueError(f"Unsupported type: {py_type} for key: {key}")
        node_map[link_key] = link

        if link_dict["node"]:
            from pykotor.resource.generics.dlg.nodes import DLGNode

            link.node = DLGNode.from_dict(link_dict["node"], node_map)  # pyright: ignore[reportAttributeAccessIssue]

        return link
