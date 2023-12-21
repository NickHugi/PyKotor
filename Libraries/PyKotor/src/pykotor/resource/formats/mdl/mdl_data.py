from __future__ import annotations

from enum import IntEnum

from pykotor.common.geometry import SurfaceMaterial, Vector2, Vector3, Vector4
from pykotor.common.misc import Color
from pykotor.resource.type import ResourceType


class MDL:
    """Represents a MDL/MDX file.

    Attributes
    ----------
        root: The root node of the model.
        anims: The animations stored in the model.
        name: The model name.
        fog: If fog affects the model.
        supermodel: Name of another model resource to import extra data from.
    """

    BINARY_TYPE = ResourceType.MDL

    def __init__(
        self,
    ) -> None:
        self.root: MDLNode = MDLNode()
        self.anims: list[MDLAnimation] = []
        self.name: str = ""
        self.fog: bool = False
        self.supermodel: str = ""

    def get(
        self,
        node_name: str,
    ) -> MDLNode | None:
        """Gets a node by name from the tree.

        Args:
        ----
            node_name: The name of the node to retrieve.

        Returns:
        -------
            pick: The node with the matching name or None.

        Processing Logic:
        ----------------
            - Traverse the tree depth-first by recursively adding child nodes to a stack.
            - Check each node's name against the target name.
            - Return the matching node or None if not found.
        """
        pick: MDLNode | None = None

        nodes: list[MDLNode] = [self.root]
        while nodes:
            node: MDLNode = nodes.pop()
            if node.name == node_name:
                pick = node
            else:
                nodes.extend(node.children)

        return pick

    def all_nodes(
        self,
    ) -> list[MDLNode]:
        """Returns a list of all nodes in the tree including the root node and children recursively.

        Args:
        ----
            self: The tree object

        Returns:
        -------
            list[MDLNode]: A list of all nodes in the tree

        Processing Logic:
        ----------------
            - Initialize an empty list to store nodes
            - Initialize a scan list with the root node
            - Pop a node from scan and add it to nodes list
            - Extend scan with children of the popped node
            - Repeat until scan is empty
            - Return the nodes list with all nodes
        """
        nodes: list[MDLNode] = []
        scan: list[MDLNode] = [self.root]
        while scan:
            node: MDLNode = scan.pop()
            nodes.append(node)
            scan.extend(node.children)
        return nodes

    def find_parent(
        self,
        child: MDLNode,
    ) -> MDLNode | None:
        """Find the parent node of the given child node.

        Args:
        ----
            child: The child node to find the parent for

        Returns:
        -------
            parent: The parent node of the given child or None if not found

        Processing Logic:
        ----------------
            - Get all nodes in the scene
            - Iterate through all nodes
            - Check if the child is in the node's children
            - If found, set the parent variable to that node
            - Return the parent node or None if not found.
        """
        return next(
            (
                node
                for node in self.all_nodes()
                if child in node.children
            ),
            None,
        )

    def global_position(
        self,
        node: MDLNode,
    ) -> Vector3:
        """Returns the global position of a node by traversing up the parent chain.

        Args:
        ----
            node: The node to get the global position for.

        Returns:
        -------
            Vector3: The global position of the node

        Processing Logic:
        ----------------
            - Traverse up the parent chain of the node and add each parent's position to a running total
            - Start with the node's local position
            - Keep traversing up parents until the parent is None (root node reached)
            - Return the final global position
        """
        position: Vector3 = node.position
        parent: MDLNode | None = self.find_parent(node)
        while parent is not None:
            position += parent.position
            parent = self.find_parent(parent)
        return position

    def get_by_node_id(
        self,
        node_id,
    ) -> MDLNode:
        """Get node by node id.

        Args:
        ----
            node_id: The id of the node to retrieve

        Returns:
        -------
            MDLNode: The node with matching id

        Raises:
        ------
            StopIteration: node_id not found.

        Processing Logic:
        ----------------
            - Iterate through all nodes in the graph
            - Check if current node id matches argument node id
            - Return node if id matches
            - Raise error if no matching node found.
        """
        return next(node for node in self.all_nodes() if node.node_id == node_id)

    def all_textures(
        self,
    ) -> set[str]:
        """Returns all unique texture names used in the scene.

        Args:
        ----
            self: The scene object

        Returns:
        -------
            set[str]: A set containing all unique texture names used in meshes

        Processing Logic:
        ----------------
            - Iterate through all nodes in the scene
            - Check if the node has a mesh and the mesh has a valid texture name
            - Add the texture name to a set to eliminate duplicates
            - Return the final set of unique texture names.
        """
        return {
            node.mesh.texture_1
            for node in self.all_nodes()
            if (node.mesh and node.mesh.texture_1 != "NULL" and node.mesh.texture_1 != "")
        }

    def all_lightmaps(
        self,
    ) -> set[str]:
        """Returns a set of all lightmap textures used in the scene.

        Args:
        ----
            self: The scene object

        Returns:
        -------
            set[str]: A set of all lightmap texture names used in nodes

        Processing Logic:
        ----------------
            - Iterate through all nodes in the scene
            - Check if the node has a mesh and a lightmap texture
            - Add the lightmap texture to the return set if it is not empty.
        """
        return {
            node.mesh.texture_2
            for node in self.all_nodes()
            if (node.mesh and node.mesh.texture_2 != "NULL" and node.mesh.texture_2 != "")
        }


# region Animation Data
class MDLAnimation:
    def __init__(
        self,
    ) -> None:
        self.name: str = ""
        self.root_model: str = ""
        self.anim_length: float = 0.0
        self.transition_length: float = 0.0
        self.events: list[MDLEvent] = []
        self.root: MDLNode = MDLNode()

    def all_nodes(
        self,
    ) -> list[MDLNode]:
        """Returns all nodes in the MDL tree including children recursively.

        Args:
        ----
            self: The MDL tree object

        Returns:
        -------
            list[MDLNode]: A list containing all nodes in the tree

        Processing Logic:
        ----------------
            - Initialize an empty list to store nodes and a scan list containing just the root node
            - Pop a node from scan and append it to nodes list
            - Extend scan with children of the popped node
            - Repeat until scan is empty
            - Return the nodes list containing all nodes.
        """
        nodes: list[MDLNode] = []
        scan: list[MDLNode] = [self.root]
        while scan:
            node: MDLNode = scan.pop()
            nodes.append(node)
            scan.extend(node.children)
        return nodes


class MDLEvent:
    def __init__(
        self,
    ) -> None:
        self.activation_time: float = 0.0
        self.name: str = ""


# endregion


# region Node Headers
class MDLNodeFlags(IntEnum):
    HEADER = 0x00000001
    LIGHT = 0x00000002
    EMITTER = 0x00000004
    CAMERA = 0x00000008
    REFERENCE = 0x00000010
    MESH = 0x00000020
    SKIN = 0x00000040
    DANGLY = 0x00000100
    AABB = 0x00000200
    SABER = 0x00000800


class MDLNode:
    """A node in the MDL tree that can store additional nodes or some extra data related to the model such as geometry or lighting.

    Attributes
    ----------
        children: List of children linked to the node.
        controllers: List of controllers linked to the node.
        name: Name of the node.
        position: The position of the node.
        orientation: The orientation of the node.
        light: Light data associated with the node.
        emitter: Emitter data associated with the node.
        mesh: Trimesh data associated with the node.
        skin: Skin data associated with the node.
        dangly: Danglymesh data associated with the node.
        aabb: Walkmesh data associated with the node
        saber: Sabermesh data associated with the node.
    """

    def __init__(
        self,
    ) -> None:
        """Initializes a MDLNode object.

        Args:
        ----
            self: The MDLNode object being initialized

        Processing Logic:
        ----------------
            - Sets the children list to an empty list
            - Sets the controllers list to an empty list
            - Sets the name to an empty string
            - Sets the node ID to -1
            - Sets the position to the null vector
            - Sets the orientation to identity
            - Sets all component references to None.
        """
        self.children: list[MDLNode] = []
        self.controllers: list[MDLController] = []
        self.name: str = ""
        self.node_id: int = -1
        self.position: Vector3 = Vector3.from_null()
        self.orientation: Vector4 = Vector4(0, 0, 0, 1)

        self.light: MDLLight | None = None
        self.emitter: MDLEmitter | None = None
        self.reference: MDLReference | None = None
        self.mesh: MDLMesh | None = None
        self.skin: MDLSkin | None = None
        self.dangly: MDLDangly | None = None
        self.aabb: MDLWalkmesh | None = None
        self.saber: MDLSaber | None = None

    def descendants(
        self,
    ) -> list[MDLNode]:
        """Returns all descendants of a node including itself.

        Args:
        ----
            self: The node to find descendants for

        Returns:
        -------
            list[MDLNode]: A list containing the node and all its descendants

        Processing Logic:
        ----------------
            - Initialize an empty list to store ancestors
            - Loop through each child node of the current node
            - Append the child to the ancestors list
            - Recursively call descendants on the child to get its descendants and extend the ancestors list
            - Return the final ancestors list containing the node and all its descendants.
        """
        ancestors = []
        for child in self.children:
            ancestors.append(child)
            ancestors.extend(child.descendants())
        return ancestors

    def child(
        self,
        name,
    ) -> MDLNode:
        """Find child node by name.

        Args:
        ----
            name: Name of child node to find

        Returns:
        -------
            MDLNode: Child node with matching name

        Processing Logic:
        ----------------
            - Iterate through list of children nodes
            - Check if child name matches name argument
            - If match found, return child node
            - If no match, raise KeyError.
        """
        for child in self.children:
            if child.name == name:
                return child
        raise KeyError


class MDLLight:
    """Light data that can be attached to a node.

    Attributes
    ----------
        flare_radius:
        light_priority:
        ambient_only:
        dynamic_type:
        shadow:
        flare:
        fading_light:
    """

    def __init__(
        self,
    ) -> None:
        # TODO: Make enums, check if bools, docs, merge flare data into class
        self.flare_radius: float = 0.0
        self.light_priority: int = 0
        self.ambient_only: int = 0
        self.dynamic_type: int = 0
        self.shadow: int = 0
        self.flare: int = 0
        self.fading_light: int = 0
        self.flare_sizes: list = []
        self.flare_positions: list = []
        self.flare_color_shifts: list = []
        self.flare_textures: list = []


class MDLEmitter:
    """Emitter data that can be attached to a node.

    Attributes
    ----------
        dead_space:
        blast_radius:
        blast_length:
        branch_count:
        control_point_smoothing:
        x_grid:
        y_grid:
        spawn_type:
        update:
        render:
        blend:
        texture:
        chunk_name:
        two_sided_texture:
        loop:
        render_order:
        frame_blender:
        depth_texture:
    """

    def __init__(
        self,
    ) -> None:
        # TODO: Make enums, check if bools, docs, seperate flags into booleans
        self.dead_space: float = 0.0
        self.blast_radius: float = 0.0
        self.blast_length: float = 0.0
        self.branch_count: int = 0
        self.control_point_smoothing: float = 0.0
        self.x_grid: int = 0
        self.y_grid: int = 0
        self.spawn_type: int = 0
        self.update: str = ""
        self.render: str = ""
        self.blend: str = ""
        self.texture: str = ""
        self.chunk_name: str = ""
        self.two_sided_texture: int = 0
        self.loop: int = 0
        self.render_order: int = 0
        self.frame_blender: int = 0
        self.depth_texture: str = ""
        self.flags: int = 0


class MDLReference:
    """Reference data that can be attached to a node.

    Attributes
    ----------
        model:
        reattachable:
    """

    def __init__(
        self,
    ) -> None:
        # TODO: docs
        self.model: str = ""
        self.reattachable: bool = False


class MDLMesh:
    """Mesh data that can be attached to a node."""

    def __init__(
        self,
    ) -> None:
        # TODO: look at mesh inverted counter array, rename boolean flags
        self.faces: list[MDLFace] = []
        self.diffuse: Color = Color.WHITE
        self.ambient: Color = Color.WHITE
        self.transparency_hint: int = 0
        self.texture_1: str = ""
        self.texture_2: str = ""
        self.saber_unknowns: tuple[int, int, int, int, int, int, int, int] = (3, 0, 0, 0, 0, 0, 0, 0)
        self.animate_uv: bool = False

        self.radius: float = 0.0
        self.bb_min: Vector3 = Vector3.from_null()
        self.bb_max: Vector3 = Vector3.from_null()
        self.average: Vector3 = Vector3.from_null()
        self.area: float = 0.0

        self.uv_direction_x: float = 0.0
        self.uv_direction_y: float = 0.0
        self.uv_jitter: float = 0.0
        self.uv_jitter_speed: float = 0.0

        self.has_lightmap: bool = False
        self.rotate_texture: bool = False
        self.background_geometry: bool = False
        self.shadow: bool = False
        self.beaming: bool = False
        self.render: bool = True

        # Trimesh
        self.vertex_positions: list[Vector3] = []
        self.vertex_normals: list[Vector3] | None = None
        self.vertex_uv1: list[Vector2] | None = None
        self.vertex_uv2: list[Vector2] | None = None

        # KotOR 2 Only
        self.dirt_enabled: bool = False
        self.dirt_texture: int = 0
        self.dirt_coordinate_space: int = 0
        self.hide_in_hologram: bool = False

    def gen_normals(
        self,
    ):
        ...


class MDLSkin:
    """Skin data that can be attached to a node."""

    def __init__(
        self,
    ) -> None:
        self.bone_indices: tuple[int, int, int, int, int, int, int, int, int, int, int, int, int, int, int, int] = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        self.qbones: list[Vector4] = []
        self.tbones: list[Vector3] = []
        self.bonemap: list[int] = []

        self.vertex_bones: list[MDLBoneVertex] = []


class MDLDangly:
    """Dangly data that can be attached to a node."""


class MDLWalkmesh:
    """AABB data that can be attached to a node."""


class MDLSaber:
    """Saber data that can be attached to a node."""


# endregion


# region Geometry Data
class MDLBoneVertex:
    def __init__(
        self,
    ) -> None:
        self.vertex_weights: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
        self.vertex_indices: tuple[float, float, float, float] = (-1.0, -1.0, -1.0, -1.0)


class MDLFace:
    def __init__(
        self,
    ) -> None:
        self.v1: int = 0
        self.v2: int = 0
        self.v3: int = 0
        self.material: SurfaceMaterial = SurfaceMaterial.GRASS
        self.a1: int = 0
        self.a2: int = 0
        self.a3: int = 0
        self.coefficient: int = 0
        self.normal: Vector3 = Vector3.from_null()


# endregion


# region Controller Data
class MDLControllerType(IntEnum):
    INVALID = -1

    POSITION = 8
    ORIENTATION = 20
    SCALE = 36
    ILLUM_COLOR = 100
    ALPHA = 132

    P2P_BEZIER_2 = 132


class MDLController:
    """A controller is an object that gets attached to the node and influences some sort of change that is either static or animated."""

    def __init__(
        self,
    ) -> None:
        self.controller_type: MDLControllerType = MDLControllerType.INVALID
        self.rows: list[MDLControllerRow] = []


class MDLControllerRow:
    def __init__(
        self,
        time,
        data,
    ) -> None:
        self.time: float = time
        self.data: list[float] = data

    def __repr__(
        self,
    ):
        return f"MDLControllerRow({self.time}, {self.data})"

    def __str__(
        self,
    ):
        return f"{self.time} {self.data}".replace(",", "").replace("[", "").replace("]", "")


# endregion
