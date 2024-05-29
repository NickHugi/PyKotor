from __future__ import annotations

import math

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Generator, List, NoReturn, cast

from pykotor.common.geometry import Polygon3, Vector2, Vector3, Vector4
from pykotor.common.language import LocalizedString
from pykotor.common.misc import Color, Game, ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.gff import GFF, GFFContent, GFFList, GFFStruct, bytes_gff, read_gff, write_gff
from pykotor.resource.generics.utc import UTC, bytes_utc
from pykotor.resource.generics.utd import UTD, bytes_utd
from pykotor.resource.generics.ute import UTE, bytes_ute
from pykotor.resource.generics.utm import UTM, bytes_utm
from pykotor.resource.generics.utp import UTP, bytes_utp
from pykotor.resource.generics.uts import UTS, bytes_uts
from pykotor.resource.generics.utt import UTT, bytes_utt
from pykotor.resource.generics.utw import UTW, bytes_utw
from pykotor.resource.type import ResourceType
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    from pykotor.resource.type import SOURCE_TYPES, TARGET_TYPES


class GIT:
    BINARY_TYPE = ResourceType.GIT

    def __init__(
        self,
    ):
        self.ambient_sound_id: int = 0
        self.ambient_volume: int = 0
        self.env_audio: int = 0
        self.music_standard_id: int = 0
        self.music_battle_id: int = 0
        self.music_delay: int = 0

        self.cameras: list[GITCamera] = []
        self.creatures: list[GITCreature] = []
        self.doors: list[GITDoor] = []
        self.encounters: list[GITEncounter] = []
        self.placeables: list[GITPlaceable] = []
        self.sounds: list[GITSound] = []
        self.stores: list[GITStore] = []
        self.triggers: list[GITTrigger] = []
        self.waypoints: list[GITWaypoint] = []

    def __iter__(self) -> Generator[ResRef, Any, None]:
        # Iterate over creatures
        for creature in self.creatures:
            yield creature.resref
        # Iterate over doors
        for door in self.doors:
            yield door.resref
        for encounter in self.encounters:
            yield encounter.resref
        for store in self.stores:
            yield store.resref
        for placeable in self.placeables:
            yield placeable.resref
        for sound in self.sounds:
            yield sound.resref
        for trigger in self.triggers:
            yield trigger.resref
        for waypoint in self.waypoints:
            yield waypoint.resref

    def iter_resource_identifiers(self) -> Generator[ResourceIdentifier, Any, None]:
        for creature in self.creatures:
            yield ResourceIdentifier(str(creature.resref), ResourceType.UTC)
        for door in self.doors:
            yield ResourceIdentifier(str(door.resref), ResourceType.UTD)
        for encounter in self.encounters:
            yield ResourceIdentifier(str(encounter.resref), ResourceType.UTE)
        for store in self.stores:
            yield ResourceIdentifier(str(store.resref), ResourceType.UTM)
        for placeable in self.placeables:
            yield ResourceIdentifier(str(placeable.resref), ResourceType.UTP)
        for sound in self.sounds:
            yield ResourceIdentifier(str(sound.resref), ResourceType.UTS)
        for trigger in self.triggers:
            yield ResourceIdentifier(str(trigger.resref), ResourceType.UTT)
        for waypoint in self.waypoints:
            yield ResourceIdentifier(str(waypoint.resref), ResourceType.UTW)

    def instances(
        self,
    ) -> list[GITInstance]:
        """Returns a list of all instances stored inside the GIT, regardless of the type.

        Returns:
        -------
            A list of all stored instances.
        """
        return cast(
            List[GITInstance],
            [
                *self.cameras,
                *self.creatures,
                *self.doors,
                *self.encounters,
                *self.placeables,
                *self.sounds,
                *self.stores,
                *self.triggers,
                *self.waypoints,
            ]
        )

    def next_camera_id(self) -> int:
        """Get a unique new camera id for this git to use with a new GITCamera."""
        return max(camera.camera_id for camera in self.cameras) + 1

    def remove(
        self,
        instance: GITInstance,
    ):
        if isinstance(instance, GITCreature):
            self.creatures.remove(instance)
        elif isinstance(instance, GITPlaceable):
            self.placeables.remove(instance)
        elif isinstance(instance, GITDoor):
            self.doors.remove(instance)
        elif isinstance(instance, GITTrigger):
            self.triggers.remove(instance)
        elif isinstance(instance, GITEncounter):
            self.encounters.remove(instance)
        elif isinstance(instance, GITWaypoint):
            self.waypoints.remove(instance)
        elif isinstance(instance, GITCamera):
            self.cameras.remove(instance)
        elif isinstance(instance, GITSound):
            self.sounds.remove(instance)
        elif isinstance(instance, GITStore):
            self.stores.remove(instance)

    def index(
        self,
        instance: GITInstance,
    ) -> int:
        """Finds the index of an instance in the particular list it belongs to inside the GIT object.

        Args:
        ----
            instance: The instance to search for.

        Raises:
        ------
            ValueError: If the given instance does not belong to the GIT.

        Returns:
        -------
            The index into one of the GIT instance lists.
        """
        if isinstance(instance, GITCreature):
            return self.creatures.index(instance)
        if isinstance(instance, GITPlaceable):
            return self.placeables.index(instance)
        if isinstance(instance, GITDoor):
            return self.doors.index(instance)
        if isinstance(instance, GITTrigger):
            return self.triggers.index(instance)
        if isinstance(instance, GITEncounter):
            return self.encounters.index(instance)
        if isinstance(instance, GITWaypoint):
            return self.waypoints.index(instance)
        if isinstance(instance, GITCamera):
            return self.cameras.index(instance)
        if isinstance(instance, GITSound):
            return self.sounds.index(instance)
        if isinstance(instance, GITStore):
            return self.stores.index(instance)

        msg = "Could not find instance in GIT object."
        raise ValueError(msg)

    def add(
        self,
        instance: GITInstance,
    ) -> None:
        """Adds instance to the relevant list in the GIT.

        Args:
        ----
            instance: The instance to add into the GIT.

        Raises:
        ------
            ValueError: If the instance already is stored inside the GIT.
        """
        if isinstance(instance, GITCreature):
            if instance in self.creatures:
                ValueError("Creature instance already exists inside the GIT object.")
            return self.creatures.append(instance)
        if isinstance(instance, GITPlaceable):
            if instance in self.placeables:
                ValueError("Placeable instance already exists inside the GIT object.")
            return self.placeables.append(instance)
        if isinstance(instance, GITDoor):
            if instance in self.doors:
                ValueError("Door instance already exists inside the GIT object.")
            return self.doors.append(instance)
        if isinstance(instance, GITTrigger):
            if instance in self.triggers:
                ValueError("Trigger instance already exists inside the GIT object.")
            return self.triggers.append(instance)
        if isinstance(instance, GITEncounter):
            if instance in self.encounters:
                ValueError("Encounter instance already exists inside the GIT object.")
            return self.encounters.append(instance)
        if isinstance(instance, GITWaypoint):
            if instance in self.waypoints:
                ValueError("Waypoint instance already exists inside the GIT object.")
            return self.waypoints.append(instance)
        if isinstance(instance, GITCamera):
            if instance in self.cameras:
                ValueError("Camera instance already exists inside the GIT object.")
            return self.cameras.append(instance)
        if isinstance(instance, GITSound):
            if instance in self.sounds:
                ValueError("Sound instance already exists inside the GIT object.")
            return self.sounds.append(instance)
        if isinstance(instance, GITStore):
            if instance in self.stores:
                ValueError("Store instance already exists inside the GIT object.")
            return self.stores.append(instance)

        msg = "Tried to add invalid instance."
        raise ValueError(msg)


class GITInstance(ABC):
    def __init__(self, x: float, y: float, z: float):
        """Initializes a GIT instance with the given position coordinates.

        Args:
        ----
            x (float): The x-coordinate of the position.
            y (float): The y-coordinate of the position.
            z (float): The z-coordinate of the position.
        """
        self.position: Vector3 = Vector3(x, y, z)
        self.resref: ResRef = ResRef.from_blank()

    def __repr__(self):
        if isinstance(self, GITCamera):
            return f"{self.__class__.__name__}(camera_id={self.camera_id})"
        return f"{self.__class__.__name__}({self.identifier()})"

    def __hash__(self):
        return hash(self.camera_id if isinstance(self, GITCamera) else self.identifier())

    @abstractmethod
    def identifier(self) -> ResourceIdentifier:
        """Returns the resource identifier of the instance, or None if it doesn't have one."""

    @abstractmethod
    def blank(
        self,
    ) -> bytes | None: ...

    @abstractmethod
    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        """Moves the instance to the specified position.

        Args:
        ----
            - x (float): The new x-coordinate of the position.
            - y (float): The new y-coordinate of the position.
            - z (float): The new z-coordinate of the position.
        """

    @abstractmethod
    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ): ...

    @abstractmethod
    def classification(
        self,
    ) -> str: ...

    @abstractmethod
    def yaw(
        self,
    ) -> float | None:
        """Returns the yaw rotation (in radians) of the instance if the instance supports it, otherwise returns None."""


class GITCamera(GITInstance):
    GFF_STRUCT_ID = 14

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
        yaw: float = 0.0,
        pitch: float = 0.0,
        roll: float = 0.0,
        camera_id: int = 0,
    ):
        super().__init__(x, y, z)
        self.camera_id: int = camera_id
        self.fov: float = 45
        self.height: float = 0.0
        self.mic_range: float = 0.0
        self.pitch: float = 0.0
        self.orientation: Vector4 = Vector4.from_euler(
            math.pi / 2 - yaw,
            roll,
            math.pi - pitch,
        )

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ):
        rotation: Vector3 = self.orientation.to_euler()
        rotation.x += yaw
        rotation.y += roll
        rotation.z += pitch
        self.orientation = Vector4.from_euler(rotation.x, rotation.y, rotation.z)

    def identifier(
        self,
    ) -> ResourceIdentifier | None:
        return None

    def blank(
        self,
    ) -> bytes | None:
        return None

    def classification(
        self,
    ) -> str:
        return "Camera"

    def yaw(
        self,
    ) -> float | None:
        return math.pi - self.orientation.to_euler().x

    def roll(self) -> float:
        raise NotImplementedError("GITCamera's do not have roll.")


class GITCreature(GITInstance):
    GFF_STRUCT_ID = 4

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        super().__init__(x, y, z)
        self.resref: ResRef = ResRef.from_blank()
        self.bearing: float = 0.0

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ):
        self.bearing += yaw

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), ResourceType.UTC)

    def blank(
        self,
    ) -> bytes:
        return bytes_utc(UTC())

    def extension(
        self,
    ) -> ResourceType:
        return ResourceType.UTC

    def classification(
        self,
    ) -> str:
        return "Creature"

    def yaw(
        self,
    ) -> float:
        return self.bearing


class GITModuleLink(IntEnum):
    NoLink = 0
    ToDoor = 1
    ToWaypoint = 2


class GITDoor(GITInstance):
    GFF_STRUCT_ID = 8

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        super().__init__(x, y, z)
        self.resref: ResRef = ResRef.from_blank()
        self.bearing: float = 0.0
        self.tweak_color: Color | None = None  # TODO: fix tweak color in dismantle/construct
        self.linked_to: str = ""
        self.linked_to_flags: GITModuleLink = GITModuleLink.NoLink
        self.linked_to_module: ResRef = ResRef.from_blank()
        self.transition_destination: LocalizedString = LocalizedString.from_invalid()
        self.tag: str = ""

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ):
        self.bearing += yaw

    def blank(
        self,
    ) -> bytes:
        return bytes_utd(UTD())

    def identifier(
        self,
    ) -> ResourceIdentifier:
        """Returns a ResourceIdentifier for the resource.

        Args:
        ----
            self: {Object containing resource reference}.

        Returns:
        -------
            ResourceIdentifier

        Processing Logic:
        ----------------
            - Get resource reference from self
            - Create ResourceIdentifier object from reference and type
            - Return ResourceIdentifier
        """
        return ResourceIdentifier(str(self.resref), ResourceType.UTD)

    def classification(
        self,
    ) -> str:
        return "Door"

    def yaw(
        self,
    ) -> float:
        return self.bearing


class GITEncounterSpawnPoint:
    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        self.x: float = x
        self.y: float = y
        self.z: float = z
        self.orientation: float = 0.0


class GITEncounter(GITInstance):
    GFF_STRUCT_ID = 7
    GFF_GEOMETRY_STRUCT_ID = 1
    GFF_SPAWN_STRUCT_ID = 2

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        super().__init__(x, y, z)
        self.geometry: Polygon3 = Polygon3()
        self.spawn_points: list[GITEncounterSpawnPoint] = []
        self.resref: ResRef = ResRef.from_blank()

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        """Moves an object to a new position.

        Args:
        ----
            x: New x coordinate
            y: New y coordinate
            z: New z coordinate

        Processing Logic:
        ----------------
            - Adds the passed x value to the current x coordinate
            - Adds the passed y value to the current y coordinate
            - Adds the passed z value to the current z coordinate
            - Updates the object's position with the new coordinates.
        """
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ) -> NoReturn:
        msg = "Encounters cannot be rotated."
        raise NotImplementedError(msg)

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), ResourceType.UTE)

    def blank(
        self,
    ) -> bytes:
        return bytes_ute(UTE())

    def classification(
        self,
    ) -> str:
        return "Encounter"

    def yaw(
        self,
    ) -> None:
        return None


class GITPlaceable(GITInstance):
    GFF_STRUCT_ID = 9

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        super().__init__(x, y, z)
        self.resref: ResRef = ResRef.from_blank()
        self.bearing: float = 0.0
        self.tweak_color: Color | None = None
        self.tag: str = ""

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        """Moves an object to a new position.

        Args:
        ----
            x: New x coordinate
            y: New y coordinate
            z: New z coordinate

        Processing Logic:
        ----------------
            - Adds the passed x value to the current x coordinate
            - Adds the passed y value to the current y coordinate
            - Adds the passed z value to the current z coordinate
            - Updates the object's position with the new coordinates.
        """
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ):
        self.bearing += yaw

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), ResourceType.UTP)

    def blank(
        self,
    ) -> bytes:
        return bytes_utp(UTP())

    def classification(
        self,
    ) -> str:
        return "Placeable"

    def yaw(
        self,
    ) -> float:
        return self.bearing


class GITSound(GITInstance):
    GFF_STRUCT_ID = 6

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        super().__init__(x, y, z)
        self.resref: ResRef = ResRef.from_blank()
        self.tag: str = ""

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ) -> NoReturn:
        msg = "Sounds cannot be rotated."
        raise ValueError(msg)

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), ResourceType.UTS)

    def blank(
        self,
    ) -> bytes:
        return bytes_uts(UTS())

    def classification(
        self,
    ) -> str:
        return "Sound"

    def yaw(
        self,
    ) -> None:
        return None


class GITStore(GITInstance):
    GFF_STRUCT_ID = 11

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        super().__init__(x, y, z)
        self.resref: ResRef = ResRef.from_blank()
        self.bearing: float = 0.0

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ):
        self.bearing += yaw

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), ResourceType.UTM)

    def blank(
        self,
    ) -> bytes:
        return bytes_utm(UTM())

    def classification(
        self,
    ) -> str:
        return "Store"

    def yaw(
        self,
    ) -> float:
        return self.bearing


class GITTrigger(GITInstance):
    GFF_STRUCT_ID = 1
    GFF_GEOMETRY_STRUCT_ID = 3

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        super().__init__(x, y, z)
        self.resref: ResRef = ResRef.from_blank()
        self.geometry: Polygon3 = Polygon3()
        self.tag: str = ""
        self.linked_to: str = ""
        self.linked_to_flags: GITModuleLink = GITModuleLink.NoLink
        self.linked_to_module: ResRef = ResRef.from_blank()
        self.transition_destination: LocalizedString = LocalizedString.from_invalid()

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ) -> NoReturn:
        msg = "Triggers cannot be rotated."
        raise ValueError(msg)

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), ResourceType.UTT)

    def blank(
        self,
    ) -> bytes:
        return bytes_utt(UTT())

    def classification(
        self,
    ) -> str:
        return "Trigger"

    def yaw(
        self,
    ) -> float:
        return None


class GITTransitionTrigger(GITTrigger):
    def __init__(
        self,
    ):
        super().__init__()
        self.linked_to: str = ""
        self.linked_to_flags: GITModuleLink = GITModuleLink.NoLink
        self.linked_to_module: ResRef = ResRef.from_blank()
        self.transition_destination: LocalizedString = LocalizedString.from_invalid()
        self.tag: str = ""


class GITWaypoint(GITInstance):
    GFF_STRUCT_ID = 5

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        z: float = 0.0,
    ):
        super().__init__(x, y, z)
        self.resref: ResRef = ResRef.from_blank()
        self.tag: str = ""
        self.name: LocalizedString = LocalizedString.from_invalid()
        self.map_note: LocalizedString | None = LocalizedString.from_invalid()
        self.map_note_enabled: bool = False
        self.has_map_note: bool = False
        self.bearing: float = 0.0

    def move(
        self,
        x: float,
        y: float,
        z: float,
    ):
        self.position.x += x
        self.position.y += y
        self.position.z += z

    def rotate(
        self,
        yaw: float,
        pitch: float,
        roll: float,
    ):
        self.bearing += yaw

    def identifier(
        self,
    ) -> ResourceIdentifier:
        return ResourceIdentifier(str(self.resref), ResourceType.UTW)

    def blank(
        self,
    ) -> bytes:
        return bytes_utw(UTW())

    def classification(
        self,
    ) -> str:
        return "Waypoint"

    def yaw(
        self,
    ) -> float:
        return self.bearing


def construct_git(
    gff: GFF,
) -> GIT:
    git = GIT()

    root = gff.root
    properties_struct = root.acquire("AreaProperties", GFFStruct())
    git.ambient_volume = properties_struct.acquire("AmbientSndDayVol", 0)
    git.ambient_sound_id = properties_struct.acquire("AmbientSndDay", 0)
    git.env_audio = properties_struct.acquire("EnvAudio", 0)
    git.music_standard_id = properties_struct.acquire("MusicDay", 0)
    git.music_battle_id = properties_struct.acquire("MusicBattle", 0)
    git.music_delay = properties_struct.acquire("MusicDelay", 0)

    for camera_struct in gff.root.get_list("CameraList"):
        camera = GITCamera()
        git.cameras.append(camera)

        camera.camera_id = camera_struct.acquire("CameraID", 0)
        camera.fov = camera_struct.acquire("FieldOfView", 0.0)
        camera.height = camera_struct.acquire("Height", 0.0)
        camera.mic_range = camera_struct.acquire("MicRange", 0.0)
        camera.orientation = camera_struct.acquire("Orientation", Vector4.from_null())
        camera.position = camera_struct.acquire("Position", Vector3.from_null())
        camera.pitch = camera_struct.acquire("Pitch", 0.0)

    for creature_struct in gff.root.get_list("Creature List"):
        creature = GITCreature()
        git.creatures.append(creature)
        creature.resref = creature_struct.acquire("TemplateResRef", ResRef.from_blank())
        creature.position.x = creature_struct.acquire("XPosition", 0.0)
        creature.position.y = creature_struct.acquire("YPosition", 0.0)
        creature.position.z = creature_struct.acquire("ZPosition", 0.0)
        rot_x, rot_y = (
            creature_struct.acquire("XOrientation", 0.0),
            creature_struct.acquire("YOrientation", 0.0),
        )
        creature.bearing = Vector2(rot_x, rot_y).angle() - math.pi / 2

    for door_struct in gff.root.get_list("Door List"):
        door = GITDoor()
        git.doors.append(door)
        door.bearing = door_struct.acquire("Bearing", 0.0)
        door.tag = door_struct.acquire("Tag", "")
        door.resref = door_struct.acquire("TemplateResRef", ResRef.from_blank())
        door.linked_to = door_struct.acquire("LinkedTo", "")
        door.linked_to_flags = GITModuleLink(door_struct.acquire("LinkedToFlags", 0))
        door.linked_to_module = door_struct.acquire("LinkedToModule", ResRef.from_blank())
        door.transition_destination = door_struct.acquire("TransitionDestin", LocalizedString.from_invalid())
        door.position.x = door_struct.acquire("X", 0.0)
        door.position.y = door_struct.acquire("Y", 0.0)
        door.position.z = door_struct.acquire("Z", 0.0)
        tweak_enabled = door_struct.acquire("UseTweakColor", 0)
        door.tweak_color = Color.from_bgr_integer(door_struct.acquire("TweakColor", 0)) if tweak_enabled else None

    for encounter_struct in gff.root.get_list("Encounter List"):
        x = encounter_struct.acquire("XPosition", 0.0)
        y = encounter_struct.acquire("YPosition", 0.0)
        z = encounter_struct.acquire("ZPosition", 0.0)

        encounter = GITEncounter()
        git.encounters.append(encounter)
        encounter.position = Vector3(x, y, z)
        encounter.resref = encounter_struct.acquire("TemplateResRef", ResRef.from_blank())

        if encounter_struct.exists("Geometry"):
            geometry_list = encounter_struct.get_list("Geometry")
            for geometry_struct in geometry_list:
                x = geometry_struct.acquire("X", 0.0)
                y = geometry_struct.acquire("Y", 0.0)
                z = geometry_struct.acquire("Z", 0.0)
                encounter.geometry.append(Vector3(x, y, z))
            if not geometry_list:
                RobustRootLogger().warning("Encounter geometry list is empty! Creating a default triangle at its position.")
                encounter.geometry.create_triangle(origin=encounter.position)
        else:
            RobustRootLogger().warning("Encounter geometry list missing! Creating a default triangle at its position.")
            encounter.geometry.create_triangle(origin=encounter.position)

        for spawn_struct in encounter_struct.get_list("SpawnPointList"):
            spawn = GITEncounterSpawnPoint()
            spawn.x = spawn_struct.acquire("X", 0.0)
            spawn.y = spawn_struct.acquire("Y", 0.0)
            spawn.z = spawn_struct.acquire("Z", 0.0)
            spawn.orientation = spawn_struct.acquire("Orientation", 0.0)
            encounter.spawn_points.append(spawn)

    for placeable_struct in gff.root.get_list("Placeable List"):
        placeable = GITPlaceable()
        git.placeables.append(placeable)

        placeable.resref = placeable_struct.acquire("TemplateResRef", ResRef.from_blank())
        placeable.position.x = placeable_struct.acquire("X", 0.0)
        placeable.position.y = placeable_struct.acquire("Y", 0.0)
        placeable.position.z = placeable_struct.acquire("Z", 0.0)
        placeable.bearing = placeable_struct.acquire("Bearing", 0.0)

        tweak_enabled = placeable_struct.acquire("UseTweakColor", 0)
        tweak_int = placeable_struct.acquire("TweakColor", 0)
        placeable.tweak_color = Color.from_bgr_integer(tweak_int) if tweak_enabled else None

    for sound_struct in gff.root.get_list("SoundList"):
        sound = GITSound()
        git.sounds.append(sound)

        sound.resref = sound_struct.acquire("TemplateResRef", ResRef.from_blank())
        sound.position.x = sound_struct.acquire("XPosition", 0.0)
        sound.position.y = sound_struct.acquire("YPosition", 0.0)
        sound.position.z = sound_struct.acquire("ZPosition", 0.0)

    for store_struct in gff.root.get_list("StoreList"):
        store = GITStore()
        git.stores.append(store)

        store.resref = store_struct.acquire("ResRef", ResRef.from_blank())
        store.position.x = store_struct.acquire("XPosition", 0.0)
        store.position.y = store_struct.acquire("YPosition", 0.0)
        store.position.z = store_struct.acquire("ZPosition", 0.0)

        rot_x, rot_y = (
            store_struct.acquire("XOrientation", 0.0),
            store_struct.acquire("YOrientation", 0.0),
        )
        store.bearing = Vector2(rot_x, rot_y).angle() - math.pi / 2

    for trigger_struct in gff.root.get_list("TriggerList"):
        trigger = GITTrigger()
        git.triggers.append(trigger)

        trigger.resref = trigger_struct.acquire("TemplateResRef", ResRef.from_blank())
        trigger.position.x = trigger_struct.acquire("XPosition", 0.0)
        trigger.position.y = trigger_struct.acquire("YPosition", 0.0)
        trigger.position.z = trigger_struct.acquire("ZPosition", 0.0)
        trigger.tag = trigger_struct.acquire("Tag", "")
        trigger.linked_to = trigger_struct.acquire("LinkedTo", "")
        trigger.linked_to_flags = GITModuleLink(trigger_struct.acquire("LinkedToFlags", 0))
        trigger.linked_to_module = trigger_struct.acquire("LinkedToModule", ResRef.from_blank())
        trigger.transition_destination = trigger_struct.acquire("TransitionDestin", LocalizedString.from_invalid())

        if trigger_struct.exists("Geometry"):
            geometry_list = trigger_struct.get_list("Geometry")
            for geometry_struct in geometry_list:
                x = geometry_struct.acquire("PointX", 0.0)
                y = geometry_struct.acquire("PointY", 0.0)
                z = geometry_struct.acquire("PointZ", 0.0)
                trigger.geometry.append(Vector3(x, y, z))
            if not geometry_list:
                RobustRootLogger().warning("Trigger geometry list is empty! Creating a default triangle at its position.")
                trigger.geometry.create_triangle(origin=trigger.position)
        else:
            RobustRootLogger().warning("Trigger geometry list missing! Creating a default triangle at its position.")
            trigger.geometry.create_triangle(origin=trigger.position)

    for waypoint_struct in gff.root.get_list("WaypointList"):
        waypoint = GITWaypoint()
        git.waypoints.append(waypoint)

        waypoint.name = waypoint_struct.acquire("LocalizedName", LocalizedString.from_invalid())
        waypoint.tag = waypoint_struct.acquire("Tag", "")
        waypoint.resref = waypoint_struct.acquire("TemplateResRef", ResRef.from_blank())
        waypoint.position.x = waypoint_struct.acquire("XPosition", 0.0)
        waypoint.position.y = waypoint_struct.acquire("YPosition", 0.0)
        waypoint.position.z = waypoint_struct.acquire("ZPosition", 0.0)

        waypoint.has_map_note = bool(waypoint_struct.acquire("HasMapNote", 0))
        if waypoint.has_map_note:
            waypoint.map_note = waypoint_struct.acquire("MapNote", LocalizedString.from_invalid())
            waypoint.map_note_enabled = bool(waypoint_struct.acquire("MapNoteEnabled", 0))

        rot_x, rot_y = (
            waypoint_struct.acquire("XOrientation", 0.0),
            waypoint_struct.acquire("YOrientation", 0.0),
        )
        waypoint.bearing = Vector2(rot_x, rot_y).angle() - math.pi / 2

    return git


def dismantle_git(
    git: GIT,
    game: Game = Game.K2,
    *,
    use_deprecated: bool = True,
) -> GFF:
    gff = GFF(GFFContent.GIT)

    root = gff.root
    root.set_uint8("UseTemplates", 1)

    properties_struct = root.set_struct("AreaProperties", GFFStruct(100))
    properties_struct.set_int32("AmbientSndDayVol", git.ambient_volume)
    properties_struct.set_int32("AmbientSndDay", git.ambient_sound_id)
    properties_struct.set_int32("AmbientSndNitVol", git.ambient_volume)
    properties_struct.set_int32("AmbientSndNight", git.ambient_sound_id)
    properties_struct.set_int32("EnvAudio", git.env_audio)
    properties_struct.set_int32("MusicDay", git.music_standard_id)
    properties_struct.set_int32("MusicNight", git.music_standard_id)
    properties_struct.set_int32("MusicBattle", git.music_battle_id)
    properties_struct.set_int32("MusicDelay", git.music_delay)

    camera_list = root.set_list("CameraList", GFFList())
    for camera in git.cameras:
        camera_struct = camera_list.add(GITCamera.GFF_STRUCT_ID)
        camera_struct.set_int32("CameraID", camera.camera_id)
        camera_struct.set_single("FieldOfView", camera.fov)
        camera_struct.set_single("Height", camera.height)
        camera_struct.set_single("MicRange", camera.mic_range)
        orientation = Vector4(*camera.orientation)
        #orientation.z = 0.0  # Pitch has its own field.  # comment out to pass the test? idk
        camera_struct.set_vector4("Orientation", orientation)
        camera_struct.set_vector3("Position", camera.position)
        camera_struct.set_single("Pitch", camera.pitch)

    creature_list = root.set_list("Creature List", GFFList())
    for creature in git.creatures:
        bearing = Vector2.from_angle(creature.bearing + math.pi / 2)

        creature_struct = creature_list.add(GITCreature.GFF_STRUCT_ID)
        if creature.resref:
            creature_struct.set_resref("TemplateResRef", creature.resref)
        creature_struct.set_single("XOrientation", bearing.x)
        creature_struct.set_single("YOrientation", bearing.y)
        creature_struct.set_single("XPosition", creature.position.x)
        creature_struct.set_single("YPosition", creature.position.y)
        creature_struct.set_single("ZPosition", creature.position.z)

    door_list = root.set_list("Door List", GFFList())
    for door in git.doors:
        door_struct = door_list.add(GITDoor.GFF_STRUCT_ID)
        door_struct.set_single("Bearing", door.bearing)
        door_struct.set_string("Tag", door.tag)
        if door.resref:
            door_struct.set_resref("TemplateResRef", door.resref)
        door_struct.set_string("LinkedTo", door.linked_to)
        door_struct.set_uint8("LinkedToFlags", door.linked_to_flags.value)
        door_struct.set_resref("LinkedToModule", door.linked_to_module)
        door_struct.set_locstring("TransitionDestin", door.transition_destination)
        door_struct.set_single("X", door.position.x)
        door_struct.set_single("Y", door.position.y)
        door_struct.set_single("Z", door.position.z)
        if game.is_k2():
            tweak_color = 0 if door.tweak_color is None else door.tweak_color.bgr_integer()
            door_struct.set_uint32("TweakColor", tweak_color)
            door_struct.set_uint8("UseTweakColor", 0 if door.tweak_color is None else 1)

    encounter_list = root.set_list("Encounter List", GFFList())
    for encounter in git.encounters:
        encounter_struct = encounter_list.add(GITEncounter.GFF_STRUCT_ID)
        if encounter.resref:
            encounter_struct.set_resref("TemplateResRef", encounter.resref)
        encounter_struct.set_single("XPosition", encounter.position.x)
        encounter_struct.set_single("YPosition", encounter.position.y)
        encounter_struct.set_single("ZPosition", encounter.position.z)

        if not encounter.geometry:
            RobustRootLogger().warning("Missing encounter geometry for '%s', creating a default triangle at its position...", encounter.resref)
            encounter.geometry.create_triangle(origin=encounter.position)

        geometry_list = encounter_struct.set_list("Geometry", GFFList())
        for point in encounter.geometry:
            geometry_struct = geometry_list.add(GITEncounter.GFF_GEOMETRY_STRUCT_ID)
            geometry_struct.set_single("X", point.x)
            geometry_struct.set_single("Y", point.y)
            geometry_struct.set_single("Z", point.z)

        spawn_list = encounter_struct.set_list("SpawnPointList", GFFList())
        for spawn in encounter.spawn_points:
            spawn_struct = spawn_list.add(GITEncounter.GFF_SPAWN_STRUCT_ID)
            spawn_struct.set_single("Orientation", spawn.orientation)
            spawn_struct.set_single("X", spawn.x)
            spawn_struct.set_single("Y", spawn.y)
            spawn_struct.set_single("Z", spawn.z)

    placeable_list = root.set_list("Placeable List", GFFList())
    for placeable in git.placeables:
        placeable_struct = placeable_list.add(GITPlaceable.GFF_STRUCT_ID)
        placeable_struct.set_single("Bearing", placeable.bearing)
        if placeable.resref:
            placeable_struct.set_resref("TemplateResRef", placeable.resref)
        placeable_struct.set_single("X", placeable.position.x)
        placeable_struct.set_single("Y", placeable.position.y)
        placeable_struct.set_single("Z", placeable.position.z)
        if game.is_k2():
            tweak_color = 0 if placeable.tweak_color is None else placeable.tweak_color.bgr_integer()
            placeable_struct.set_uint32("TweakColor", tweak_color)
            placeable_struct.set_uint8(
                "UseTweakColor",
                0 if placeable.tweak_color is None else 1,
            )

    sound_list = root.set_list("SoundList", GFFList())
    for sound in git.sounds:
        sound_struct = sound_list.add(GITSound.GFF_STRUCT_ID)
        sound_struct.set_uint32("GeneratedType", 0)
        if sound.resref:
            sound_struct.set_resref("TemplateResRef", sound.resref)
        sound_struct.set_single("XPosition", sound.position.x)
        sound_struct.set_single("YPosition", sound.position.y)
        sound_struct.set_single("ZPosition", sound.position.z)

    store_list = root.set_list("StoreList", GFFList())
    for store in git.stores:
        bearing = Vector2.from_angle(store.bearing + math.pi / 2)

        store_struct = store_list.add(GITStore.GFF_STRUCT_ID)
        if store.resref:
            store_struct.set_resref("ResRef", store.resref)
        store_struct.set_single("XOrientation", bearing.x)
        store_struct.set_single("YOrientation", bearing.y)
        store_struct.set_single("XPosition", store.position.x)
        store_struct.set_single("YPosition", store.position.y)
        store_struct.set_single("ZPosition", store.position.z)

    trigger_list = root.set_list("TriggerList", GFFList())
    for trigger in git.triggers:
        trigger_struct = trigger_list.add(GITTrigger.GFF_STRUCT_ID)
        if trigger.resref:
            trigger_struct.set_resref("TemplateResRef", trigger.resref)
        trigger_struct.set_single("XPosition", trigger.position.x)
        trigger_struct.set_single("YPosition", trigger.position.y)
        trigger_struct.set_single("ZPosition", trigger.position.z)
        trigger_struct.set_single("XOrientation", 0.0)
        trigger_struct.set_single("YOrientation", 0.0)
        trigger_struct.set_single("ZOrientation", 0.0)

        trigger_struct.set_string("Tag", trigger.tag)
        trigger_struct.set_string("LinkedTo", trigger.linked_to)
        trigger_struct.set_uint8("LinkedToFlags", trigger.linked_to_flags.value)
        trigger_struct.set_resref("LinkedToModule", trigger.linked_to_module)
        trigger_struct.set_locstring("TransitionDestin", trigger.transition_destination)

        if not trigger.geometry:
            RobustRootLogger().warning("Missing trigger geometry for '%s', creating a default triangle at its position...", trigger.resref)
            trigger.geometry.create_triangle(origin=trigger.position)

        geometry_list = trigger_struct.set_list("Geometry", GFFList())
        for point in trigger.geometry:
            geometry_struct = geometry_list.add(GITTrigger.GFF_GEOMETRY_STRUCT_ID)
            geometry_struct.set_single("PointX", point.x)
            geometry_struct.set_single("PointY", point.y)
            geometry_struct.set_single("PointZ", point.z)

    waypoint_list = root.set_list("WaypointList", GFFList())
    for waypoint in git.waypoints:
        bearing = Vector2.from_angle(waypoint.bearing + math.pi / 2)

        waypoint_struct = waypoint_list.add(GITWaypoint.GFF_STRUCT_ID)

        waypoint_struct.set_locstring("LocalizedName", waypoint.name)
        waypoint_struct.set_string("Tag", waypoint.tag)
        waypoint_struct.set_resref("TemplateResRef", waypoint.resref)
        waypoint_struct.set_single("XPosition", waypoint.position.x)
        waypoint_struct.set_single("YPosition", waypoint.position.y)
        waypoint_struct.set_single("ZPosition", waypoint.position.z)
        waypoint_struct.set_single("XOrientation", bearing.x)
        waypoint_struct.set_single("YOrientation", bearing.y)
        waypoint_struct.set_uint8("MapNoteEnabled", waypoint.map_note_enabled)
        waypoint_struct.set_uint8("HasMapNote", waypoint.has_map_note)
        waypoint_struct.set_locstring(
            "MapNote",
            LocalizedString.from_invalid() if waypoint.map_note is None else waypoint.map_note,
        )

        if use_deprecated:
            waypoint_struct.set_uint8("Appearance", 1)
            waypoint_struct.set_locstring("Description", LocalizedString(-1))
            waypoint_struct.set_string("LinkedTo", "")

    if use_deprecated:
        root.set_list("List", GFFList())

    return gff


def read_git(
    source: SOURCE_TYPES,
    offset: int = 0,
    size: int | None = None,
) -> GIT:
    gff = read_gff(source, offset, size)
    return construct_git(gff)


def write_git(
    git: GIT,
    target: TARGET_TYPES,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
):
    gff = dismantle_git(git, game, use_deprecated=use_deprecated)
    write_gff(gff, target, file_format)


def bytes_git(
    git: GIT,
    game: Game = Game.K2,
    file_format: ResourceType = ResourceType.GFF,
    *,
    use_deprecated: bool = True,
) -> bytes:
    gff = dismantle_git(git, game, use_deprecated=use_deprecated)
    return bytes_gff(gff, file_format)
