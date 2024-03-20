from __future__ import annotations

from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.type import ResourceType


# This will eventually be an entire mapping of the 2DA in the game.
# e.g. some 2da reference each other's rows/columns for information.
# Currently due to the scale of the project this will only link the strrefs to the TLK.


# Confirmed in K1. Some others list strrefs but are blank/zero so we won't include them for brevity/usability reasons.
TWODA_REFS: dict[ResourceIdentifier, set[str]] = {
    ResourceIdentifier("crtemplates", ResourceType.TwoDA): {"name", "strref"},
    ResourceIdentifier("creaturesize", ResourceType.TwoDA): {"strref"},
    ResourceIdentifier("credits", ResourceType.TwoDA): {"name"},
    ResourceIdentifier("loadscreenhints", ResourceType.TwoDA): {"gameplayhint", "storyhint"},
    ResourceIdentifier("actions", ResourceType.TwoDA): {"string_ref"},
    ResourceIdentifier("aiscripts", ResourceType.TwoDA): {"name_strref", "description_strref"},
    ResourceIdentifier("ambientmusic", ResourceType.TwoDA): {"description"},
    ResourceIdentifier("ambientsound", ResourceType.TwoDA): {"description"},
    ResourceIdentifier("bodybag", ResourceType.TwoDA): {"name"},
    ResourceIdentifier("appearance", ResourceType.TwoDA): {"string_ref"},
    ResourceIdentifier("baseitems", ResourceType.TwoDA): {"name"},
    ResourceIdentifier("bindablekeys", ResourceType.TwoDA): {"keynamestrref"},
    ResourceIdentifier("classes", ResourceType.TwoDA): {"name", "description"},
    ResourceIdentifier("difficultyopt", ResourceType.TwoDA): {"name"},
    ResourceIdentifier("doortypes", ResourceType.TwoDA): {"stringrefgame"},
    ResourceIdentifier("effecticons", ResourceType.TwoDA): {"strref"},
    ResourceIdentifier("encdifficulty", ResourceType.TwoDA): {"strref"},
    ResourceIdentifier("feat", ResourceType.TwoDA): {"name", "description"},
    ResourceIdentifier("feedbacktext", ResourceType.TwoDA): {"strref"},
}
class TwoDAStrRefInfo:
    def __init__(self):
        ...