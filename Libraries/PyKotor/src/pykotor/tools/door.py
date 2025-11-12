from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.extract.file import ResourceResult
    from pykotor.extract.installation import Installation
    from pykotor.resource.generics.utd import UTD
    from pykotor.resource.type import SOURCE_TYPES


def get_model(
    utd: UTD,
    installation: Installation,
    *,
    genericdoors: TwoDA | SOURCE_TYPES | None = None,
) -> str:
    """Returns the model name for the given door.
    
    References:
    ----------
        vendor/reone/src/libs/game/object/door.cpp (Door model lookup)
        vendor/KotOR.js/src/module/ModuleDoor.ts (Door appearance handling)
        Note: Door model lookup uses genericdoors.2da
    

    If no value is specified for the genericdoor parameters then it will be loaded from the given installation.

    Args:
    ----
        utd: UTD object of the door to lookup the model for.
        installation: The relevant installation.
        genericdoors: The genericdoors.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns the model name for the door.

    Raises:
    ------
        ValueError: genericdoors.2da not found in passed arguments OR the installation.
    """
    if genericdoors is None:
        result: ResourceResult | None = installation.resource("genericdoors", ResourceType.TwoDA)
        if not result:
            raise ValueError("Resource 'genericdoors.2da' not found in the installation, cannot get UTD model.")
        genericdoors = read_2da(result.data)
    if not isinstance(genericdoors, TwoDA):
        genericdoors = read_2da(genericdoors)

    return genericdoors.get_row(utd.appearance_id).get_string("modelname")
