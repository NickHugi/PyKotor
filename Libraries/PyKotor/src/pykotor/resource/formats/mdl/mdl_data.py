from __future__ import annotations

from enum import IntFlag
from typing import TYPE_CHECKING

from pykotor.common.misc import Color
from pykotor.resource.formats._base import ComparableMixin
from pykotor.resource.type import ResourceType
from utility.common.geometry import Vector3, Vector4

if TYPE_CHECKING:
    from pykotor.resource.formats.mdl.mdl_types import MDLControllerType
    from utility.common.geometry import Vector2


class MDL(ComparableMixin):
    """Represents a MDL/MDX file.

    Attributes:
    ----------
        root: The root node of the model.
        anims: The animations stored in the model.
        name: The model name.
        fog: If fog affects the model.
        supermodel: Name of another model resource to import extra data from.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/model.cpp - Model structure and rendering
        vendor/reone/include/reone/graphics/model.h - Model header definitions
        vendor/mdlops - MDL/MDX manipulation tool
        vendor/kotorblender/io_scene_kotor/format/mdl/ - Blender MDL loader/exporter
        vendor/KotOR.js/src/odyssey/OdysseyModel.ts - TypeScript model structure
        vendor/kotor/kotor/model/nodes.py - Python model node parsing
        vendor/xoreos-tools/src/resource/mdlmdx.cpp - MDL/MDX format parser
        Note: MDL/MDX are binary formats with separate geometry (.mdx) and structure (.mdl) files
    """

    BINARY_TYPE = ResourceType.MDL
    COMPARABLE_FIELDS = ("name", "fog", "supermodel")
    COMPARABLE_SEQUENCE_FIELDS = ("anims",)

    def __init__(
        self,
    ):
        self.root: MDLNode = MDLNode()
        self.anims: list[MDLAnimation] = []
        self.name: str = ""
        self.fog: bool = False
        self.supermodel: str = ""

    def __eq__(self, other):
        if not isinstance(other, MDL):
            return NotImplemented
        return (
            self.root == other.root
            and self.anims == other.anims
            and self.name == other.name
            and self.fog == other.fog
            and self.supermodel == other.supermodel
        )

    def __hash__(self):
        return hash((
            self.root,
            tuple(self.anims),
            self.name,
            self.fog,
            self.supermodel
        ))

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
        """
        pick: MDLNode | None = None

        nodes: list[MDLNode] = [self.root]
        while nodes:
            node = nodes.pop()
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
        """
        all_nodes: list[MDLNode] = self.all_nodes()
        parent: MDLNode | None = None
        for node in all_nodes:
            if child in node.children:
                parent = node
        return parent

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
        """
        position: Vector3 = node.position
        parent: MDLNode | None = self.find_parent(node)
        while parent is not None:
            position += parent.position
            parent = self.find_parent(parent)
        return position

    def get_by_node_id(
        self,
        node_id: int,
    ) -> MDLNode:
        """Get node by node id.

        Args:
        ----
            node_id: The id of the node to retrieve

        Returns:
        -------
            MDLNode: The node with matching id
        """
        for node in self.all_nodes():
            if node.node_id == node_id:
                return node
        raise ValueError

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
        """
        return {
            node.mesh.texture_1
            for node in self.all_nodes()
            if (node.mesh and node.mesh.texture_1 != "NULL" and node.mesh.texture_1)
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
        """
        return {
            node.mesh.texture_2
            for node in self.all_nodes()
            if (node.mesh and node.mesh.texture_2 != "NULL" and node.mesh.texture_2)
        }
    
    def prepare_skin_meshes(self) -> None:
        """Prepare bone lookup tables for all skinned meshes in the model.
        
        This method should be called after loading the model and before rendering or
        manipulating skinned meshes. It creates bone serial and node number lookup
        tables for efficient bone matrix computation during skeletal animation.
        
        References:
        ----------
            vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723 - prepareSkinMeshes()
            Called after model loading to initialize skin mesh bone mappings
        
        Notes:
        -----
            This is essential for multi-part character models where body parts
            reference bones in the full skeleton hierarchy (reone:704-722).
        """
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:704-722
        nodes = self.all_nodes()
        for node in nodes:
            # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:705-707
            # Only process skin mesh nodes
            if node.mesh and node.mesh.skin:
                # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:708-721
                # Prepare bone lookups for this skin mesh
                node.mesh.skin.prepare_bone_lookups(nodes)

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, supermodel={self.supermodel!r})"


# region Animation Data
class MDLAnimation(ComparableMixin):
    """Animation data for model animations.
    
    Animations in KotOR contain a full node hierarchy with controller keyframe data.
    Each animation can override positions, rotations, and other properties of nodes
    over time to create character movement, attacks, expressions, etc.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:736-779 (animation reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:653-699 (animation loading)
        vendor/mdlops/MDLOpsM.pm:4052-4090 (animation reading from ASCII)
    
    Attributes:
    ----------
        name: Animation name (e.g. "c_imp_walk01", "g_dance01")
            Reference: reone:742, kotorblender:660
        root_model: Name of model this animation applies to
            Reference: reone:752, mdlops:4069
            Empty string means animation applies to same model
        anim_length: Duration of animation in seconds
            Reference: reone:751, kotorblender:662, mdlops:4065
        transition_length: Blend time when transitioning to this animation
            Reference: reone:752, kotorblender:663, mdlops:4069
        events: Animation events that trigger at specific times
            Reference: reone:760-769, kotorblender:684-698, mdlops:4078-4081
            Used for footstep sounds, attack hit timing, etc.
        root: Root node of animation node hierarchy
            Reference: reone:757, kotorblender:700-767
            Contains controller keyframe data for all animated nodes
    """
    COMPARABLE_FIELDS = ("name", "root_model", "anim_length", "transition_length")
    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:742
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:660
        self.name: str = ""
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:752
        # vendor/mdlops/MDLOpsM.pm:4069 - animroot
        self.root_model: str = ""
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:751
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:662
        self.anim_length: float = 0.0
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:752
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:663
        self.transition_length: float = 0.0
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:760-769
        # vendor/mdlops/MDLOpsM.pm:4078-4081
        # Animation events (footsteps, attack hits, sounds, etc.)
        self.events: list[MDLEvent] = []
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:757
        # Animation node hierarchy with controller keyframes
        self.root: MDLNode = MDLNode()

    def __eq__(self, other):
        if not isinstance(other, MDLAnimation):
            return NotImplemented
        return (
            self.name == other.name
            and self.root_model == other.root_model
            and self.anim_length == other.anim_length
            and self.transition_length == other.transition_length
            and self.events == other.events
            and self.root == other.root
        )

    def __hash__(self):
        return hash((
            self.name,
            self.root_model,
            self.anim_length,
            self.transition_length,
            tuple(self.events),
            self.root
        ))

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
        """
        nodes: list[MDLNode] = []
        scan: list[MDLNode] = [self.root]
        while scan:
            node = scan.pop()
            nodes.append(node)
            scan.extend(node.children)
        return nodes

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, root_model={self.root_model!r}, anim_length={self.anim_length!r}, transition_length={self.transition_length!r})"


class MDLEvent(ComparableMixin):
    """Animation event that triggers at a specific time during animation playback.
    
    Events are used to synchronize sound effects, particle effects, or gameplay logic
    with animation timing. Common uses include footstep sounds, weapon swing sounds,
    attack damage timing, and special effect triggers.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:764-768 (event reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:686-698 (event loading)
        vendor/mdlops/MDLOpsM.pm:4078-4081 (event parsing from ASCII)
    
    Attributes:
    ----------
        activation_time: Time in seconds when event triggers (0.0 to anim_length)
            Reference: reone:765, kotorblender:694
        name: Event name/identifier (e.g. "snd_footstep", "snd_hit", "detonate")
            Reference: reone:766, kotorblender:695
            Game code uses event names to trigger appropriate actions
    
    Examples:
    --------
        footstep event at 0.5s: triggers footstep sound effect
        hit event at 1.2s: deals damage when attack animation reaches strike
        detonate event: triggers explosion for grenades/mines
    """
    COMPARABLE_FIELDS = ("activation_time", "name")

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:765
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:694
        # Time in seconds when event fires (0.0 to animation length)
        self.activation_time: float = 0.0
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:766
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:695
        # Event name used by game code to trigger actions
        self.name: str = ""

    def __eq__(self, other):
        if not isinstance(other, MDLEvent):
            return NotImplemented
        return (
            self.activation_time == other.activation_time
            and self.name == other.name
        )

    def __hash__(self):
        return hash((self.activation_time, self.name))


# endregion


# region Node Headers
class MDLNodeFlags(IntFlag):
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


class MDLNode(ComparableMixin):
    """A node in the MDL tree that can store additional nodes or some extra data related to the model such as geometry or lighting.
    
    Model nodes form a hierarchical tree structure where each node can contain geometric data
    (mesh, skin, dangly, saber, walkmesh), light sources, particle emitters, or serve as
    positioning dummies. Controller keyframes can animate node properties over time.
    
    References:
    ----------
        vendor/reone/include/reone/graphics/modelnode.h:31-287 - ModelNode class definition
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:182-290 - Node loading from MDL
        vendor/xoreos/src/graphics/aurora/modelnode.h:67-252 - ModelNode class
        vendor/xoreos/src/graphics/aurora/model_kotor.cpp:277-533 - KotOR node parsing
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:406-582 - Node reading
        vendor/kotorblender/io_scene_kotor/scene/model.py:103-297 - Node hierarchy building
        vendor/KotOR.js/src/odyssey/OdysseyModelNode.ts:31-464 - TypeScript node implementation
        vendor/mdlops (ASCII MDL node format specifications)
        vendor/kotor/kotor/model/nodes.py:7-51 - Python node parsing

    Attributes:
    ----------
        children: List of child nodes in hierarchy
            Reference: reone:modelnode.h:219, xoreos:modelnode.h:241, KotOR.js:37
            Child nodes inherit parent transforms and can be enumerated for rendering
            
        controllers: Animation controller keyframe data
            Reference: reone:modelnode.h:34, xoreos:modelnode.h:178-196, kotorblender:reader.py:498-526
            Controllers animate position, orientation, scale, color, alpha, and other properties
            See MDLControllerType enum for complete list of controllable properties
            
        name: Node name (ASCII string, max 32 chars)
            Reference: reone:mdlmdxreader.cpp:212, xoreos:model_kotor.cpp:311, kotorblender:reader.py:416
            Used to reference nodes by name for attachment points, bone lookups, and parenting
            
        node_id: Unique node number within model for quick lookups
            Reference: reone:mdlmdxreader.cpp:202-203, xoreos:model_kotor.cpp:305, kotorblender:reader.py:413
            Stored as uint16 in binary format, used for parent/child relationships and bone references
            
        position: Local position relative to parent (x, y, z)
            Reference: reone:modelnode.h:243, xoreos:modelnode.h:89, KotOR.js:42, kotorblender:reader.py:427
            Combined with parent transforms to compute world-space position
            Can be animated via position controller (type 8)
            
        orientation: Local rotation as quaternion (x, y, z, w)
            Reference: reone:modelnode.h:244, xoreos:modelnode.h:92-93, KotOR.js:43, kotorblender:reader.py:428
            Quaternion format ensures smooth interpolation for animation
            Can be animated via orientation controller (type 20)
            Compressed in animation keyframes using 32-bit packed format (KotOR.js:14-20)

        light: Light source data (color, radius, flare properties)
            Reference: reone:modelnode.h:116-127, xoreos:modelnode.h:204-211, kotorblender/light.py:33-124
            Present when node type includes LIGHT flag (0x02)
            See MDLLight class for detailed light properties
            
        emitter: Particle emitter data (spawn rate, velocity, textures)
            Reference: reone:modelnode.h:129-153, xoreos:modelnode.h:213-221, kotorblender/emitter.py:39-286
            Present when node type includes EMITTER flag (0x04)
            See MDLEmitter class for particle system properties
            
        reference: Reference node (links to external model)
            Reference: reone:modelnode.h:155-158, xoreos:modelnode.h:223-224
            Present when node type includes REFERENCE flag (0x10)
            Used for equippable items, attached weapons, etc.
            
        mesh: Triangle mesh geometry data (vertices, faces, materials)
            Reference: reone:modelnode.h:70-91, xoreos:modelnode.h:197-202, kotorblender/trimesh.py:44-242
            Present when node type includes MESH flag (0x20)
            Contains vertex data in companion MDX file
            See MDLMesh class for geometry details
            
        skin: Skinned mesh with bone weighting for character animation
            Reference: reone:modelnode.h:36-41, xoreos:modelnode.h:226-232, kotorblender/skinmesh.py:33-189
            Present when node type includes SKIN flag (0x40)
            Vertices deform based on bone transforms using weight maps
            See MDLSkin class for bone binding details
            
        dangly: Cloth/hair physics mesh with constraint simulation
            Reference: reone:modelnode.h:47-53, xoreos:modelnode.h:234-237, kotorblender:reader.py:451-466
            Present when node type includes DANGLY flag (0x100)
            Vertices constrained by displacement, tightness, period values
            See MDLDangly class for physics properties
            
        aabb: Axis-aligned bounding box tree for walkmesh collision
            Reference: reone:modelnode.h:55-68, xoreos:modelnode.h:239-240, kotorblender/reader.py:469-487
            Present when node type includes AABB flag (0x200)
            Used for pathfinding and collision detection
            See MDLWalkmesh class for collision geometry
            
        saber: Lightsaber blade mesh with special rendering
            Reference: reone:modelnode.h:99, xoreos:modelnode.h:202, kotorblender:reader.py:446-448
            Present when node type includes SABER flag (0x800)
            Single plane geometry rendered with additive blending
            See MDLSaber class for blade properties
    """

    COMPARABLE_FIELDS = ("name", "position", "orientation", "light", "emitter", "mesh", "skin", "dangly", "aabb", "saber")
    COMPARABLE_SEQUENCE_FIELDS = ("children", "controllers")

    def __init__(
        self,
    ):
        """Initializes a MDLNode object.

        Args:
        ----
            self: The MDLNode object being initialized
        """
        # vendor/reone/include/reone/graphics/modelnode.h:219
        # vendor/xoreos/src/graphics/aurora/modelnode.h:241
        # vendor/KotOR.js/src/odyssey/OdysseyModelNode.ts:37
        # Child nodes inherit transforms and participate in rendering hierarchy
        self.children: list[MDLNode] = []
        
        # vendor/reone/include/reone/graphics/modelnode.h:34
        # vendor/xoreos/src/graphics/aurora/modelnode.h:178-196
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:498-526
        # Animation keyframe data for position, orientation, scale, color, etc.
        self.controllers: list[MDLController] = []
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:212
        # vendor/xoreos/src/graphics/aurora/model_kotor.cpp:311
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:416
        # ASCII string identifier (max 32 chars in binary format)
        self.name: str = ""
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:202-203
        # vendor/xoreos/src/graphics/aurora/model_kotor.cpp:305
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:413
        # Unique node number (uint16) for quick lookups and bone references
        self.node_id: int = -1
        
        # vendor/reone/include/reone/graphics/modelnode.h:243
        # vendor/xoreos/src/graphics/aurora/modelnode.h:89
        # vendor/KotOR.js/src/odyssey/OdysseyModelNode.ts:42
        # Local position (x,y,z) relative to parent node
        self.position: Vector3 = Vector3.from_null()
        
        # vendor/reone/include/reone/graphics/modelnode.h:244
        # vendor/xoreos/src/graphics/aurora/modelnode.h:92-93
        # vendor/KotOR.js/src/odyssey/OdysseyModelNode.ts:43
        # Local rotation as quaternion (x,y,z,w) for smooth animation interpolation
        self.orientation: Vector4 = Vector4(0, 0, 0, 1)

        # vendor/reone/include/reone/graphics/modelnode.h:116-127
        # Light source with flares, shadows, dynamic properties (node type & 0x02)
        self.light: MDLLight | None = None
        
        # vendor/reone/include/reone/graphics/modelnode.h:129-153
        # Particle emitter for effects like smoke, sparks, fire (node type & 0x04)
        self.emitter: MDLEmitter | None = None
        
        # vendor/reone/include/reone/graphics/modelnode.h:155-158
        # Reference to external model for equipment/attachments (node type & 0x10)
        self.reference: MDLReference | None = None
        
        # vendor/reone/include/reone/graphics/modelnode.h:70-91
        # Triangle mesh geometry with materials (node type & 0x20)
        self.mesh: MDLMesh | None = None
        
        # vendor/reone/include/reone/graphics/modelnode.h:36-41
        # Skinned mesh with bone weights for character animation (node type & 0x40)
        self.skin: MDLSkin | None = None
        
        # vendor/reone/include/reone/graphics/modelnode.h:47-53
        # Cloth/hair physics mesh with constraints (node type & 0x100)
        self.dangly: MDLDangly | None = None
        
        # vendor/reone/include/reone/graphics/modelnode.h:55-68
        # Walkmesh AABB tree for collision/pathfinding (node type & 0x200)
        self.aabb: MDLWalkmesh | None = None
        
        # vendor/reone/include/reone/graphics/modelnode.h:99
        # Lightsaber blade mesh with special rendering (node type & 0x800)
        self.saber: MDLSaber | None = None

    def __eq__(self, other):
        if not isinstance(other, MDLNode):
            return NotImplemented
        return (
            self.children == other.children
            and self.controllers == other.controllers
            and self.name == other.name
            and self.node_id == other.node_id
            and self.position == other.position
            and self.orientation == other.orientation
            and self.light == other.light
            and self.emitter == other.emitter
            and self.reference == other.reference
            and self.mesh == other.mesh
            and self.skin == other.skin
            and self.dangly == other.dangly
            and self.aabb == other.aabb
            and self.saber == other.saber
        )

    def __hash__(self):
        return hash((
            tuple(self.children),
            tuple(self.controllers),
            self.name,
            self.node_id,
            self.position,
            self.orientation,
            self.light,
            self.emitter,
            self.reference,
            self.mesh,
            self.skin,
            self.dangly,
            self.aabb,
            self.saber
        ))

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
        ancestors: list[MDLNode] = []
        for child in self.children:
            ancestors.append(child)
            ancestors.extend(child.descendants())
        return ancestors

    def child(
        self,
        name: str,
    ) -> MDLNode:
        """Find child node by name.

        Args:
        ----
            name: Name of child node to find

        Returns:
        -------
            MDLNode: Child node with matching name
        """
        for child in self.children:
            if child.name == name:
                return child
        raise KeyError

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, node_id={self.node_id!r})"


class MDLLight(ComparableMixin):
    """Light data that can be attached to a node.
    
    Lights in KotOR can have lens flares, shadows, dynamic properties, and various
    rendering modes. They use controller keyframes for animated properties like color,
    radius, and multiplier (intensity).
    
    References:
    ----------
        vendor/reone/src/libs/scene/node/light.cpp:43-86 (light scene node implementation)
        vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:33-124 (light properties)
    
    Attributes:
    ----------
        flare_radius: Radius around light source where lens flares are visible
            Reference: kotorblender:48,80,107
            Default 1.0, typically 0.0 to disable
        light_priority: Priority level for dynamic light rendering (0-5)
            Reference: kotorblender:41,76,103
            Higher priority lights are rendered when dynamic light limit is reached
        ambient_only: 1 = only affects ambient lighting, 0 = affects both diffuse & ambient
            Reference: kotorblender:43,74,101
            Used for fill lights and area mood lighting
        dynamic_type: Type of dynamic behavior
            Reference: kotorblender:44,78,105
            0 = static (baked), 1 = dynamic (real-time), 2 = animated
        shadow: 1 = casts shadows, 0 = no shadows
            Reference: kotorblender:38,63-66,75,102
            Shadows use contact shadow technique with radius as distance
        flare: 1 = has lens flares enabled, 0 = no lens flares
            Reference: kotorblender:47,83-84,110
            Requires flare_radius > 0 or flare_list populated
        fading_light: 1 = light fades in/out when toggled, 0 = instant on/off
            Reference: kotorblender:46,77,104, reone:52-66
            Fade speed is 2.0 units per second (reone:40)
        flare_sizes: List of flare element sizes (0.0-1.0 scale)
            Reference: kotorblender:28,90
        flare_positions: List of flare element positions along view ray (-1.0 to 1.0)
            Reference: kotorblender:29,91
            0.0 = at light source, negative = between camera and light, positive = beyond
        flare_color_shifts: List of color shift values for each flare element
            Reference: kotorblender:30,89
        flare_textures: List of texture names for each flare element
            Reference: kotorblender:27,88
            Common: "flaretex01" through "flaretex16"
    
    Controller Properties (animated via keyframes):
    -----------------------------------------------
        color: RGB color (Vector3) - controller type 76
            Reference: reone:44
        radius: Light falloff radius in meters - controller type 88
            Reference: reone:45, kotorblender:39,73,100
            For directional lights, radius >= 100.0 (reone:41,83-85)
            Energy = multiplier * radius^2 (kotorblender:123)
        multiplier: Intensity multiplier - controller type 140
            Reference: reone:46, kotorblender:40,72,99
            Combined with radius to calculate light power
    
    Notes:
    -----
        Negative color values indicate a "negative light" that subtracts illumination
        Reference: kotorblender:60,62,81,98,108,120-121
    """

    COMPARABLE_FIELDS = ("flare_radius", "light_priority", "ambient_only", "dynamic_type", "shadow", "flare", "fading_light")
    COMPARABLE_SEQUENCE_FIELDS = ("flare_sizes", "flare_positions", "flare_color_shifts", "flare_textures")

    def __init__(
        self,
    ):
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:48,80,107
        # Radius for lens flare visibility (0.0 = disabled, typical range 0.0-10.0)
        self.flare_radius: float = 0.0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:41,76,103
        # Light priority for dynamic light culling (0-5, higher = more important)
        self.light_priority: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:43,74,101
        # 1 = ambient-only (no diffuse), 0 = full lighting
        self.ambient_only: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:44,78,105
        # Dynamic behavior: 0=static, 1=dynamic, 2=animated
        self.dynamic_type: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:38,63-66,75,102
        # 1 = casts shadows, 0 = no shadows
        self.shadow: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:47,83-84,110
        # 1 = lens flares enabled, 0 = disabled
        self.flare: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:46,77,104
        # vendor/reone/src/libs/scene/node/light.cpp:40,52-66
        # 1 = fades in/out at 2.0 units/sec, 0 = instant toggle
        self.fading_light: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:28,90
        # Lens flare element sizes (one per flare texture)
        self.flare_sizes: list[float] = []
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:29,91
        # Flare positions along view ray: 0.0=light, negative=toward camera, positive=away
        self.flare_positions: list[float] = []
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:30,89
        # Color shift values for each flare element
        self.flare_color_shifts: list[float] = []
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/light.py:27,88
        # Texture names for lens flare elements (e.g. "flaretex01")
        self.flare_textures: list[str] = []

    def __repr__(self):
        return f"{self.__class__.__name__}(flare_radius={self.flare_radius!r}, light_priority={self.light_priority!r}, ambient_only={self.ambient_only!r}, dynamic_type={self.dynamic_type!r}, shadow={self.shadow!r}, flare={self.flare!r}, fading_light={self.fading_light!r})"

    def __eq__(self, other):
        if not isinstance(other, MDLLight):
            return NotImplemented
        return (
            self.flare_radius == other.flare_radius
            and self.light_priority == other.light_priority
            and self.ambient_only == other.ambient_only
            and self.dynamic_type == other.dynamic_type
            and self.shadow == other.shadow
            and self.flare == other.flare
            and self.fading_light == other.fading_light
            and self.flare_sizes == other.flare_sizes
            and self.flare_positions == other.flare_positions
            and self.flare_color_shifts == other.flare_color_shifts
            and self.flare_textures == other.flare_textures
        )

    def __hash__(self):
        return hash((
            self.flare_radius,
            self.light_priority,
            self.ambient_only,
            self.dynamic_type,
            self.shadow,
            self.flare,
            self.fading_light,
            tuple(self.flare_sizes),
            tuple(self.flare_positions),
            tuple(self.flare_color_shifts),
            tuple(self.flare_textures)
        ))


class MDLEmitter(ComparableMixin):
    """Particle emitter data for special effects.
    
    Emitters generate particle effects like smoke, fire, sparks, lightning, explosions,
    and force fields. They support multiple update modes (fountain, single, explosion,
    lightning), rendering modes, and extensive particle appearance/physics properties.
    
    References:
    ----------
        vendor/reone/src/libs/scene/node/emitter.cpp:44-319 (emitter scene node)
        vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:27-305 (emitter properties)
    
    Update Modes (update field):
    ---------------------------
        "Fountain" - Continuous particle stream at birthrate
            Reference: reone:132-140, kotorblender:236
        "Single" - Single particle, respawns if loop=True
            Reference: reone:141-146, kotorblender:236
        "Explosion" - Burst of particles then stop
            Reference: kotorblender:236
        "Lightning" - Lightning bolt effects with branching
            Reference: reone:147-151, kotorblender:236
    
    Render Modes (render field):
    ----------------------------
        "Normal" - Standard billboard particles
        "Linked" - Particles connected by lines/trails
        "Billboard_to_Local_Z" - Billboards aligned to emitter Z axis
        "Billboard_to_World_Z" - Billboards aligned to world Z axis
        "Aligned_to_World_Z" - Particles aligned to world Z
        "Aligned_to_Particle_Dir" - Particles face movement direction
        "Motion_Blur" - Particles with motion blur trails
            Reference: kotorblender:244-259, reone:41
    
    Spawn Types (spawn_type field):
    -------------------------------
        0 = "Normal" - Spawn at emitter position
        1 = "Trail" - Spawn along particle path
            Reference: kotorblender:229-233
    
    Blend Modes (blend field):
    --------------------------
        "Normal" - Standard alpha blending
        "Punch-Through" - Binary alpha (0 or 1)
        "Lighten" - Additive blending (common for fire/energy)
            Reference: kotorblender:260-267
    
    Attributes:
    ----------
        dead_space: Inner radius where no particles spawn (meters)
            Reference: kotorblender:113
        blast_radius: Outer radius for explosion/blast effects (meters)
            Reference: kotorblender:114
        blast_length: Length of blast wave propagation (meters)
            Reference: kotorblender:115
        branch_count: Number of lightning branches
            Reference: kotorblender:116
        control_point_smoothing: Smoothing factor for control point paths (0.0-1.0)
            Reference: kotorblender:117
        x_grid: Texture atlas grid width (for animated textures)
            Reference: kotorblender:118
        y_grid: Texture atlas grid height (for animated textures)
            Reference: kotorblender:119
        spawn_type: Spawn location mode (0=Normal, 1=Trail)
            Reference: kotorblender:120,229-233
        update: Update mode string ("Fountain", "Single", "Explosion", "Lightning")
            Reference: kotorblender:121,234-242, reone:131-151
        render: Render mode string (see Render Modes above)
            Reference: kotorblender:122,244-259
        blend: Blend mode string ("Normal", "Punch-Through", "Lighten")
            Reference: kotorblender:123,260-267
        texture: Main particle texture name
            Reference: kotorblender:124
        chunk_name: Chunk model name for mesh-based particles
            Reference: kotorblender:125
        two_sided_texture: 1 = render both sides, 0 = single-sided
            Reference: kotorblender:126
        loop: 1 = loop/repeat emission, 0 = emit once
            Reference: kotorblender:127, reone:142
        render_order: Rendering priority/sorting order
            Reference: kotorblender:128
        frame_blender: 1 = blend between animation frames, 0 = snap
            Reference: kotorblender:129
        depth_texture: Depth texture name for soft particles
            Reference: kotorblender:130,146
        flags: Emitter behavior flags (see MDLEmitterFlags)
            Reference: kotorblender:131-143
            Flags include: p2p, p2p_sel, affected_by_wind, tinted, bounce,
                          random, inherit, inheritvel, inherit_local, splat,
                          inherit_part, depth_texture
    
    Controller Properties (animated via keyframes):
    -----------------------------------------------
        birthrate: Particles spawned per second
            Reference: reone:45,134,138, kotorblender:148
        lifeExp: Particle lifetime in seconds (-1 = infinite)
            Reference: reone:46,110, kotorblender:157
        xSize/ySize: Emitter spawn area dimensions (meters)
            Reference: reone:48-49, kotorblender:172-173
        frameStart/frameEnd: Texture atlas animation range
            Reference: reone:50-56, kotorblender:154-155
        fps: Texture atlas animation speed (frames/second)
            Reference: reone:58, kotorblender:153
        spread: Particle spawn cone angle (degrees)
            Reference: reone:59, kotorblender:169
        velocity: Initial particle velocity (meters/second)
            Reference: reone:60, kotorblender:171
        randVel: Random velocity variation (meters/second)
            Reference: reone:61, kotorblender:162
        mass: Particle mass (affects gravity)
            Reference: reone:62, kotorblender:158
        grav: Gravity acceleration (meters/second^2)
            Reference: reone:63, kotorblender:156
        sizeStart/sizeMid/sizeEnd: Particle size over lifetime
            Reference: reone:73-75, kotorblender:163-165
        colorStart/colorMid/colorEnd: Particle RGB color over lifetime
            Reference: reone:76-78, kotorblender:189-191
        alphaStart/alphaMid/alphaEnd: Particle opacity over lifetime (0.0-1.0)
            Reference: reone:79-81, kotorblender:145-147
        lightningDelay/Radius/Scale/SubDiv: Lightning effect parameters
            Reference: reone:64-71, kotorblender:174-178
    
    Notes:
    -----
        Particles transition through three lifecycle stages: Start -> Mid -> End
        The "Mid" stage occurs at 50% of particle lifetime
        Reference: reone:73-81, kotorblender:163-165
    """

    def __init__(
        self,
    ):
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:113
        # Inner dead zone radius where no particles spawn
        self.dead_space: float = 0.0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:114
        # Outer blast/explosion radius
        self.blast_radius: float = 0.0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:115
        # Blast wave propagation length
        self.blast_length: float = 0.0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:116
        # Number of lightning branches
        self.branch_count: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:117
        # Control point path smoothing factor
        self.control_point_smoothing: float = 0.0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:118
        # Texture atlas grid width
        self.x_grid: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:119
        # Texture atlas grid height
        self.y_grid: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:120,229-233
        # Spawn location: 0=Normal (at emitter), 1=Trail (along path)
        self.spawn_type: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:121,234-242
        # vendor/reone/src/libs/scene/node/emitter.cpp:131-151
        # Update mode: "Fountain", "Single", "Explosion", "Lightning"
        self.update: str = ""
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:122,244-259
        # Render mode: "Normal", "Linked", "Billboard_to_Local_Z", etc.
        self.render: str = ""
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:123,260-267
        # Blend mode: "Normal", "Punch-Through", "Lighten"
        self.blend: str = ""
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:124
        # Main particle texture name
        self.texture: str = ""
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:125
        # Chunk model name for mesh-based particles
        self.chunk_name: str = ""
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:126
        # 1 = two-sided rendering, 0 = single-sided
        self.two_sided_texture: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:127
        # vendor/reone/src/libs/scene/node/emitter.cpp:142
        # 1 = loop emission, 0 = emit once
        self.loop: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:128
        # Rendering priority/sorting order
        self.render_order: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:129
        # 1 = blend animation frames, 0 = snap between frames
        self.frame_blender: int = 0
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:130,146
        # Depth texture for soft particle effects
        self.depth_texture: str = ""
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/emitter.py:131-143
        # Behavior flags (see MDLEmitterFlags)
        self.flags: int = 0


class MDLReference(ComparableMixin):
    """Reference node data for attaching external model resources.
    
    Reference nodes allow models to dynamically attach other models at specific
    attachment points. This is commonly used for:
    - Equipping weapons, armor, and accessories on characters
    - Attaching placeable items to character hands
    - Mounting riders on creatures
    - Adding modular parts to placeables
    
    The referenced model is loaded and attached at runtime when needed, enabling
    dynamic equipment systems without requiring every equipment combination to be
    a separate model file.
    
    References:
    ----------
        vendor/kotorblender/io_scene_kotor/scene/modelnode/reference.py:25-57
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:545-561 (reference reading)
    
    Attributes:
    ----------
        model: Name of the external model resource to attach (without file extension)
            Reference: kotorblender:30, reone:552
            Example: "w_lghtsbr_001" for a lightsaber model
            The model is loaded from the game's model resources at runtime
        reattachable: Whether the reference can be dynamically replaced
            Reference: kotorblender:31, reone:553
            True = can swap models (e.g. changing equipped weapons)
            False = permanent attachment
    
    Common Reference Node Names:
    ---------------------------
        rhand - Right hand attachment point (weapons, tools)
        lhand - Left hand attachment point (shields, off-hand weapons)
        head - Head attachment point (helmets, masks)
        back - Back attachment point (backpacks, cloaks)
        hook - Generic attachment point (various items)
        
    Example Usage:
    -------------
        Character model has "rhand" reference node
        When equipped with lightsaber, game loads "w_lghtsbr_001.mdl"
        Lightsaber model is attached at rhand node's transform
        If reattachable=True, can swap to different weapon model
    """

    def __init__(
        self,
    ):
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/reference.py:30
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:552
        # External model resource name to attach at this node
        self.model: str = ""
        
        # vendor/kotorblender/io_scene_kotor/scene/modelnode/reference.py:31
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:553
        # True = can swap models dynamically, False = permanent attachment
        self.reattachable: bool = False

    def __repr__(self):
        return f"{self.__class__.__name__}(model={self.model!r}, reattachable={self.reattachable!r})"


class MDLMesh(ComparableMixin):
    """Mesh geometry data including vertices, faces, textures, and rendering properties.
    
    Meshes are the core geometry data in MDL models. They contain vertex positions, normals,
    UV coordinates, faces/triangles, textures, and various rendering properties. KotOR supports
    several advanced mesh features including UV animation, bump mapping, and lightmaps.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:148-487 (mesh reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:415-466 (trimesh loading)
        vendor/mdlops/MDLOpsM.pm:1600-1750 (mesh processing)
    
    Key Features:
    ------------
        - UV Animation: Texture scrolling for water, lava, holograms
        - Bump/Normal Mapping: Advanced lighting with tangent space
        - Lightmaps: Pre-baked lighting for static geometry
        - Transparency: Alpha blending and transparency hints
    """

    def __init__(
        self,
    ):
        # Basic geometry
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:386-416
        # vendor/mdlops/MDLOpsM.pm:1650-1700
        self.faces: list[MDLFace] = []
        
        # Material properties
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:435-438
        self.diffuse: Color = Color.WHITE
        self.ambient: Color = Color.WHITE
        self.transparency_hint: int = 0
        
        # Textures
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:461-467
        # texture_1 is diffuse map, texture_2 is lightmap
        self.texture_1: str = ""
        self.texture_2: str = ""
        
        # Saber-specific unknowns (not fully documented in vendors)
        self.saber_unknowns: tuple[int, int, int, int, int, int, int, int] = (3, 0, 0, 0, 0, 0, 0, 0)
        
        # UV Animation for scrolling textures (water, lava, holograms, forcefields)
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:457-460
        # vendor/mdlops/MDLOpsM.pm:3204-3210
        # When animate_uv is true, texture coordinates scroll in uv_direction at runtime
        self.animate_uv: bool = False
        
        # Bounding geometry for culling and collision
        # vendor/mdlops/MDLOpsM.pm:1685-1695
        self.radius: float = 0.0
        self.bb_min: Vector3 = Vector3.from_null()
        self.bb_max: Vector3 = Vector3.from_null()
        self.average: Vector3 = Vector3.from_null()
        self.area: float = 0.0
        
        # UV Animation direction and jitter parameters
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:459
        # Direction vector for texture scrolling (units per second)
        # Used for animated water, lava flows, hologram scan lines, etc.
        self.uv_direction_x: float = 0.0
        self.uv_direction_y: float = 0.0
        
        # UV jitter for random texture offset variations
        # Creates shimmering/wavering effect on textures
        self.uv_jitter: float = 0.0
        self.uv_jitter_speed: float = 0.0
        
        # Rendering flags
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:475-478
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:439-444
        self.has_lightmap: bool = False        # Has pre-baked lighting (texture_2)
        self.rotate_texture: bool = False       # Rotate texture 90 degrees
        self.background_geometry: bool = False  # Render in background pass
        self.shadow: bool = False               # Cast shadows
        self.beaming: bool = False              # Special hologram effect
        self.render: bool = True                # Should be rendered
        
        # Vertex data arrays
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:381-384
        # All vertex arrays must have same length (1:1 correspondence)
        self.vertex_positions: list[Vector3] = []
        
        # vendor/mdlops/MDLOpsM.pm:5603-5791 (vertex normal calculation)
        # Normals can be area/angle weighted for smooth shading
        self.vertex_normals: list[Vector3] | None = None
        
        # UV texture coordinates (2D)
        # uv1 is diffuse texture coords, uv2 is lightmap coords
        self.vertex_uv1: list[Vector2] | None = None
        self.vertex_uv2: list[Vector2] | None = None
        
        # NOTE: Tangent space data (for bump/normal mapping) is stored separately in MDX
        # vendor/mdlops/MDLOpsM.pm:5379-5597 (tangent space calculation)
        # vendor/mdlops/MDLOpsM.pm:256 (MDX_TANGENT_SPACE = 0x00000080)
        # Each vertex with tangent space has: bitangent (3 floats) + tangent (3 floats)
        # Total 6 additional floats per vertex for bump mapping support
        # Tangent space enables advanced lighting (normal maps, parallax, etc.)
        
        # KotOR 2 Only - Enhanced effects
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:445-448
        self.dirt_enabled: bool = False          # Dirt/weathering overlay texture
        self.dirt_texture: str = ""              # Dirt texture name
        self.dirt_coordinate_space: int = 0      # UV space for dirt
        self.hide_in_hologram: bool = False      # Don't render in hologram effect

    def gen_normals(self):
        ...


class MDLSkin(ComparableMixin):
    """Skin data for skeletal animation (skinned mesh).
    
    Skinned meshes are meshes whose vertices are influenced by multiple bones in a skeleton,
    allowing for smooth deformation during character animation. Each vertex can be weighted
    to up to 4 bones, and the mesh deforms based on bone transformations.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723 (prepareSkinMeshes)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:468-485 (skin loading)
        vendor/mdlops/MDLOpsM.pm:1755-1820 (skin node processing)
    
    Attributes:
    ----------
        bone_indices: Fixed array of 16 bone indices that this skin references
            Reference: mdlops:1760 - bone index array
        qbones: Quaternion rotations for each bone's bind pose
            Reference: mdlops:1765 - bone orientations
        tbones: Translation vectors for each bone's bind pose  
            Reference: mdlops:1768 - bone positions
        bonemap: Maps local bone indices to global skeleton bone numbers
            Reference: reone:709-720 - bone mapping preparation
            This is critical for multi-part character models where each part
            references bones in the full skeleton
        vertex_bones: Per-vertex bone weights and indices for skinning
            Reference: reone:261-268, kotorblender:478-485
            Each vertex can be influenced by up to 4 bones with normalized weights
    """

    def __init__(
        self,
    ):
        # vendor/mdlops/MDLOpsM.pm:1760 - Fixed 16-bone index array
        self.bone_indices: tuple[int, ...] = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # vendor/mdlops/MDLOpsM.pm:1765 - Bone quaternion orientations (bind pose)
        self.qbones: list[Vector4] = []
        
        # vendor/mdlops/MDLOpsM.pm:1768 - Bone translation positions (bind pose)
        self.tbones: list[Vector3] = []
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:709-720
        # Maps local bone index to global skeleton bone number
        # Critical for multi-part models where each part references the full skeleton
        self.bonemap: list[int] = []
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-268
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-485
        # Per-vertex skinning data: up to 4 bone influences per vertex
        self.vertex_bones: list[MDLBoneVertex] = []
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:712-713
        # Prepared lookup tables for bone serial numbers and node numbers
        # These are computed from bonemap during skin mesh preparation
        self.bone_serial: list[int] = []  # Maps bone index to serial number in model
        self.bone_node_number: list[int] = []  # Maps bone index to node number in hierarchy
    
    def prepare_bone_lookups(self, nodes: list["MDLNode"]) -> None:
        """Prepare bone serial and node number lookup tables from the bone map.
        
        This method creates lookup tables that map bone indices to their serial positions
        and node numbers in the model hierarchy. This is essential for multi-part character
        models where each part needs to reference bones in the full skeleton.
        
        Args:
        ----
            nodes: List of all nodes in the model, in order
        
        References:
        ----------
            vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:703-723 - prepareSkinMeshes()
            Algorithm: For each bone in bonemap, store its serial position and node number
        
        Notes:
        -----
            This should be called after loading the skin data and before rendering.
            The bonemap contains local-to-global bone index mappings (reone:709-710).
            Invalid bone indices (0xFFFF) are skipped (reone:715-717).
        """
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:708-721
        # Build a lookup of node_id -> serial index to correctly map global bone IDs.
        node_index_by_id: dict[int, int] = {}
        for serial_index, node in enumerate(nodes):
            if node.node_id >= 0 and node.node_id not in node_index_by_id:
                node_index_by_id[node.node_id] = serial_index

        for local_index, bone_idx_value in enumerate(self.bonemap):
            # Bone map values are stored as floats in binary MDL; convert to int safely.
            try:
                bone_idx = int(bone_idx_value)
            except (TypeError, ValueError):
                continue

            # Ensure lookup arrays are large enough for this bone index.
            if bone_idx >= len(self.bone_serial):
                self.bone_serial.extend([0] * (bone_idx + 1 - len(self.bone_serial)))
                self.bone_node_number.extend([0] * (bone_idx + 1 - len(self.bone_node_number)))

            # Skip invalid bone indices (0xFFFF = unused slot).
            if bone_idx == 0xFFFF or bone_idx < 0:
                continue

            # Map global bone ID to the correct node serial.
            serial_index = node_index_by_id.get(bone_idx)
            if serial_index is None:
                # Fallback: if bonemap entry is the serial itself (legacy behaviour), accept it.
                if local_index < len(nodes):
                    serial_index = local_index
                else:
                    continue

            bone_node = nodes[serial_index]
            self.bone_serial[bone_idx] = serial_index
            self.bone_node_number[bone_idx] = bone_node.node_id


class MDLConstraint:
    """Constraint data that can be attached to a node."""
    def __init__(
        self,
    ):
        self.name: str = ""
        self.type: int = 0
        self.target: int = 0
        self.target_node: int = 0


class MDLDangly(ComparableMixin):
    """Dangly mesh physics data for cloth, hair, and soft body simulation.
    
    Dangly meshes are special meshes that simulate cloth or hair physics in KotOR.
    They use a simplified physics model with constraints and vertex positions that
    update based on movement and gravity. Common uses include capes, robes, and hair.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:276-291 (dangly reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:487-497 (dangly loading)
        vendor/mdlops/MDLOpsM.pm:1823-1870 (dangly node processing)
    
    Attributes:
    ----------
        constraints: List of constraint data defining how vertices can move
            Reference: reone:276-291, mdlops:1835-1850
            Constraints limit vertex movement to create realistic cloth behavior
        verts: Current vertex positions (updated by physics)
            Reference: reone:283, kotorblender:491-493
            These positions change during animation as cloth physics are simulated
        verts_original: Original bind pose vertex positions
            Reference: mdlops:1860
            Used as reference for resetting or calculating displacement
    """

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:276-291
        # vendor/mdlops/MDLOpsM.pm:1835-1850
        # Constraints define how vertices can move (springs, limits, etc.)
        self.constraints: list[MDLConstraint] = []
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:283
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:491-493
        # Current positions updated by physics simulation
        self.verts: list[Vector3] = []
        
        # vendor/mdlops/MDLOpsM.pm:1860 - Original bind pose positions
        self.verts_original: list[Vector3] = []

    def __repr__(self):
        return f"{self.__class__.__name__}(constraints={self.constraints!r}, verts={self.verts!r}, verts_original={self.verts_original!r})"



class MDLWalkmesh(ComparableMixin):
    """Walkmesh collision data using Axis-Aligned Bounding Box (AABB) tree.
    
    Walkmeshes define where characters can walk in a level. They use an AABB tree
    (binary space partitioning tree) for efficient collision detection. Each node
    in the tree represents a bounding volume that can be tested for intersection.
    
    The AABB tree is a hierarchical structure where:
    - Leaf nodes contain actual collision faces/triangles
    - Branch nodes subdivide space and have left/right children
    - Most significant plane axis determines split direction
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:489-509 (AABB tree reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:499-520 (AABB loading)
        vendor/mdlops/MDLOpsM.pm:1873-1935 (walkmesh/AABB processing)
    
    Attributes:
    ----------
        aabbs: List of AABB tree nodes forming the collision hierarchy
            Reference: reone:489-509 - AABB tree structure
            Each node contains:
            - Bounding box (min/max points)
            - Face index (for leaf nodes, -1 for branch nodes)
            - Most significant plane (split axis)
            - Left/right child offsets (for branch nodes)
    
    Notes:
    -----
        The AABB tree enables O(log n) collision detection instead of O(n).
        Reone implements efficient tree traversal with early rejection.
        Reference: reone:490-496 for bounding box format
    """
    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:489-509
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:499-520
        # Hierarchical AABB tree for efficient collision detection
        # Each node contains bounding box and either face index (leaf) or child pointers (branch)
        self.aabbs: list[MDLNode] = []


class MDLSaber(ComparableMixin):
    """Lightsaber blade mesh data.
    
    Lightsaber blades are special procedurally-generated meshes in KotOR that
    create the iconic glowing blade effect. The blade geometry is generated
    at runtime based on parameters like length, width, color, and type.
    
    Saber meshes have a fixed vertex count (176 vertices) and use a specific
    vertex layout optimized for the blade effect with transparency and glow.
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:308-378 (saber generation)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:522-540 (saber loading)
        vendor/mdlops/MDLOpsM.pm:1937-2010 (saber node processing)
    
    Attributes:
    ----------
        saber_type: Type of lightsaber (single, double-bladed, etc.)
            Reference: mdlops:1945
        saber_color: Blade color (red, blue, green, etc.)
            Reference: mdlops:1947, reone:319-320
        saber_length: Length of the blade in meters
            Reference: mdlops:1948, reone:312-314
        saber_width: Width/thickness of the blade  
            Reference: mdlops:1949
        saber_flare_color: Color of the blade's lens flare effect
            Reference: mdlops:1950
        saber_flare_radius: Radius of the lens flare effect
            Reference: mdlops:1951
    
    Notes:
    -----
        Saber vertices are generated procedurally with 176 vertices total:
        - 88 vertices for each side of the blade (176 total)
        - Each segment uses 8 vertices (kNumSaberPieceVertices = 8)
        - Faces are generated from predefined indices
        Reference: reone:32-33, reone:327-449 for generation algorithm
    """
    def __init__(
        self,
    ):
        # vendor/mdlops/MDLOpsM.pm:1945 - Saber type (single/double-bladed)
        self.saber_type: int = 0
        
        # vendor/mdlops/MDLOpsM.pm:1947 - Blade color
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:319-320
        self.saber_color: int = 0
        
        # vendor/mdlops/MDLOpsM.pm:1948 - Blade length in meters
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:312-314
        self.saber_length: float = 0.0
        
        # vendor/mdlops/MDLOpsM.pm:1949 - Blade width/thickness
        self.saber_width: float = 0.0
        
        # vendor/mdlops/MDLOpsM.pm:1950 - Lens flare color
        self.saber_flare_color: int = 0
        
        # vendor/mdlops/MDLOpsM.pm:1951 - Lens flare radius
        self.saber_flare_radius: float = 0.0


# endregion


# region Geometry Data
class MDLBoneVertex(ComparableMixin):
    """Per-vertex skinning data for skeletal animation.
    
    Each vertex in a skinned mesh can be influenced by up to 4 bones with different
    weights. The weights are normalized (sum to 1.0) and determine how much each bone's
    transformation affects the vertex position during animation.
    
    This is the core data structure for smooth character deformation in skeletal animation.
    When a character animates, each vertex position is computed as:
        final_pos = w0*bone0*orig_pos + w1*bone1*orig_pos + w2*bone2*orig_pos + w3*bone3*orig_pos
    
    References:
    ----------
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-268 (vertex bone reading)
        vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-485 (bone weight loading)
        vendor/mdlops/MDLOpsM.pm:1785-1800 (vertex skinning data)
    
    Attributes:
    ----------
        vertex_weights: Normalized weights for up to 4 bone influences (w0, w1, w2, w3)
            Reference: reone:264-266, kotorblender:481-483
            Weights should sum to 1.0 for proper blending
            Unused weights are set to 0.0
        vertex_indices: Bone indices for up to 4 bone influences (bone0, bone1, bone2, bone3)
            Reference: reone:261-263, kotorblender:478-480
            Indices reference bones in the skin's bonemap array
            Unused indices are set to -1.0 (yes, stored as float in MDX)
    
    Notes:
    -----
        KotOR uses up to 4 bones per vertex for smooth deformation.
        The game engine performs hardware-accelerated vertex skinning on GPU.
        Weight normalization is critical for avoiding visual artifacts.
    """
    COMPARABLE_FIELDS = ("vertex_weights", "vertex_indices")

    def __init__(
        self,
    ):
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:264-266
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:481-483
        # Normalized blend weights (must sum to 1.0)
        self.vertex_weights: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
        
        # vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:261-263
        # vendor/kotorblender/io_scene_kotor/format/mdl/reader.py:478-480
        # Bone indices into skin's bonemap (-1.0 = unused)
        self.vertex_indices: tuple[float, float, float, float] = (-1.0, -1.0, -1.0, -1.0)

    def __repr__(self):
        return f"{self.__class__.__name__}(vertex_weights={self.vertex_weights!r}, vertex_indices={self.vertex_indices!r})"


class MDLFace(ComparableMixin):
    COMPARABLE_FIELDS = ("v1", "v2", "v3", "material", "a1", "a2", "a3", "coefficient", "normal")

    def __init__(
        self,
    ):
        self.v1: int = 0
        self.v2: int = 0
        self.v3: int = 0
        # TODO: deconstruct self.material to full comprehensive data structures.
        # Face material is a packed 32-bit value in binary MDL files.
        # Low 5 bits (0-31) store walkmesh surface material for BWM/KotOR (surfacemat.2da).
        # Upper bits encode smoothgroup ID, lightmap info, and other vendor-specific data.
        # MDLOps reuses this field for smoothgroups when exporting ASCII (vendor/mdlops/MDLOpsM.pm:1292-1298).
        # KotOR.js and reone both treat it as opaque 32-bit integer (vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:395-408,
        # vendor/KotOR.js/src/odyssey/OdysseyModel.ts:face.material).
        # We therefore store it as an integer to avoid lossy enum conversion.
        self.material: int = 0
        self.a1: int = 0
        self.a2: int = 0
        self.a3: int = 0
        self.coefficient: int = 0
        self.normal: Vector3 = Vector3.from_null()


# endregion

class MDLController(ComparableMixin):
    """Controller for animating node properties over time.
    
    Controllers define how node properties (position, orientation, color, etc.) change over time.
    They can use either linear interpolation (default) or bezier interpolation for smooth curves.
    
    References:
    ----------
        vendor/mdlops/MDLOpsM.pm:1649-1778 - Controller data structure and bezier flag detection
        vendor/mdlops/MDLOpsM.pm:1704-1710 - Bezier flag extraction from column count (bit 4)
        vendor/mdlops/MDLOpsM.pm:3764-3802 - ASCII controller reading with bezier support
        vendor/reone/src/libs/graphics/format/mdlmdxreader.cpp:664-690 - Binary controller reading
    
    Attributes:
    ----------
        controller_type: The type of controller (position, orientation, color, etc.)
        rows: List of keyframe data rows (time + values)
        is_bezier: True if using bezier interpolation, False for linear interpolation
            Reference: mdlops:1704-1710 - Detected from column_count & 16 flag
    
    Notes:
    -----
        Bezier controllers store 3 values per column instead of 1:
        - Value at keyframe
        - In-tangent (control point before keyframe)
        - Out-tangent (control point after keyframe)
        Reference: mdlops:1721-1723, 1749-1756
    """

    COMPARABLE_FIELDS = ("controller_type", "is_bezier")
    COMPARABLE_SEQUENCE_FIELDS = ("rows",)

    def __init__(
        self,
        controller_type: MDLControllerType,
        rows: list[MDLControllerRow],
        is_bezier: bool = False,
    ):
        # vendor/mdlops/MDLOpsM.pm:1666-1673 - Controller type and data rows
        self.controller_type: MDLControllerType = controller_type
        self.rows: list[MDLControllerRow] = rows
        
        # vendor/mdlops/MDLOpsM.pm:1704-1710 - Bezier flag from column count bit 4
        # vendor/mdlops/MDLOpsM.pm:3764-3770 - Bezier detection in ASCII reading
        self.is_bezier: bool = is_bezier

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}(controller_type={self.controller_type!r}, rows={self.rows!r}, is_bezier={self.is_bezier!r})"


class MDLControllerRow(ComparableMixin):
    COMPARABLE_FIELDS = ("time", "data")

    def __init__(
        self,
        time: float,
        data: list[float],
    ):
        self.time: float = time
        self.data: list[float] = data

    def __repr__(
        self,
    ):
        return f"{self.__class__.__name__}({self.time!r}, {self.data!r})"

    def __str__(
        self,
    ):
        return f"{self.time} {self.data}".replace(",", "").replace("[", "").replace("]", "")


# endregion
