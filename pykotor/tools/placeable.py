from pykotor.extract.installation import Installation
from pykotor.resource.formats.twoda import TwoDA
from pykotor.resource.generics.utp import UTP
from pykotor.resource.type import ResourceType


def get_model(
    utp: UTP,
    installation: Installation,
    *,
    placeables: TwoDA | None = None,
) -> str:
    """Returns the model name for the given placeable.

    If no value is specified for the placeable parameters then it will be loaded from the given installation.

    Args:
    ----
        utp: UTC object of the target placeable.
        installation: The relevant installation.
        placeables: The placeables.2da loaded into a TwoDA object.

    Returns:
    -------
        Returns the model name for the placeable.
    """
    if placeables is None:
        placeables = installation.resource("genericdoors", ResourceType.TwoDA)

    return placeables.get_row(utp.appearance_id).get_string("modelname")
