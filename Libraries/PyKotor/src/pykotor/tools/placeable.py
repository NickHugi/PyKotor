from __future__ import annotations

from typing import TYPE_CHECKING

from pykotor.resource.formats.twoda import TwoDA, read_2da
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.extract.installation import Installation
    from pykotor.resource.generics.utp import UTP
    from pykotor.resource.type import SOURCE_TYPES


def get_model(
    utp: UTP,
    installation: Installation,
    *,
    placeables: TwoDA | SOURCE_TYPES | None = None,
) -> str:
    """Returns the model name for the given placeable.

    If no value is specified for the placeable parameters then it will be loaded from the given installation.

    Args:
    ----
        utp: UTP object of the placeable to lookup the model for.
        installation: The relevant installation.
        placeables: The placeables.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns the model name for the placeable.
    """
    if placeables is None:
        result = installation.resource("placeables", ResourceType.TwoDA)
        if not result:
            raise ValueError("Resource 'placeables.2da' not found in the installation, cannot get UTP model.")
        placeables = read_2da(result.data)
    elif not isinstance(placeables, TwoDA):
        placeables = read_2da(placeables)

    return placeables.get_row(utp.appearance_id).get_string("modelname")
