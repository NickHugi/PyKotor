from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.twoda import read_2da
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.extract.installation import Installation
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.utd import UTD


def get_model(
    utd: UTD,
    installation: Installation,
    *,
    genericdoors: TwoDA | None = None,
) -> str:
    """Returns the model name for the given door.

    If no value is specified for the genericdoor parameters then it will be loaded from the given installation.

    Args:
    ----
        utd: UTD object of the target door.
        installation: The relevant installation.
        genericdoors: The genericdoors.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns the model name for the door.
    """
    if genericdoors is None:
        result = installation.resource("placeables", ResourceType.TwoDA)
        if not result:
            raise ValueError("Resource 'placeables.2da' not found in the installation, cannot get UTD model.")
        genericdoors = read_2da(result.data)

    return genericdoors.get_row(utd.appearance_id).get_string("modelname")
