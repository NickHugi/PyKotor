from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.mdl.reference_only.constants import WalkmeshType
from pykotor.resource.formats.mdl.reference_only.dummy import DummyNode
from pykotor.resource.formats.mdl.reference_only.model import Model
from pykotor.resource.formats.mdl.reference_only.utils import is_dwk_root, is_pwk_root

if TYPE_CHECKING:
    import bpy

    from typing_extensions import Literal

    from pykotor.resource.formats.bwm.bwm_data import BWMNodeAABB
    from pykotor.resource.formats.mdl.reference_only.constants import ImportOptions

class Walkmesh(Model):
    def __init__(
        self,
        walkmesh_type: Literal["WOK", "PWK", "DWK"],
    ):
        super().__init__()
        self.walkmesh_type: WalkmeshType | Literal["WOK", "PWK", "DWK"] = walkmesh_type

    def add_to_collection(
        self,
        parent_obj: bpy.types.Object,
        collection: bpy.types.Collection,
        options: ImportOptions,
    ):
        if not isinstance(self.root_node, DummyNode) or self.root_node.parent:
            raise RuntimeError("Root node has to be a dummy without a parent")

        self.import_nodes_to_collection(self.root_node, parent_obj, collection, options)

    @classmethod
    def from_aabb_node(cls, aabb: BWMNodeAABB) -> Walkmesh | Literal["WOK", "PWK", "DWK"]:
        root_node = DummyNode("wok")
        root_node.children.append(aabb)

        walkmesh = Walkmesh(WalkmeshType.WOK)
        walkmesh.root_node = root_node

        return walkmesh

    @classmethod
    def from_root_object(
        cls,
        obj: bpy.types.Object,
        options: ImportOptions,
    ) -> Walkmesh | Literal["WOK", "PWK", "DWK"]:
        if is_pwk_root(obj):
            walkmesh_type = WalkmeshType.PWK
        elif is_dwk_root(obj):
            walkmesh_type = WalkmeshType.DWK
        else:
            raise ValueError(
                f"Cannot create walkmesh from root object '{obj.name}'"
            )

        walkmesh = Walkmesh(walkmesh_type)
        walkmesh.root_node = cls.model_node_from_object(obj, options, exclude_xwk=False)

        return walkmesh
