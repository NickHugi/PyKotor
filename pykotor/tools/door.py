from typing import Optional

from pykotor.resource.generics.utd import UTD

from pykotor.extract.installation import Installation
from pykotor.resource.formats.twoda import TwoDA
from pykotor.resource.generics.utp import UTP
from pykotor.resource.type import ResourceType


def get_model(
        utd: UTD,
        installation: Installation,
        *,
        genericdoors: Optional[TwoDA] = None,
) -> str:
    """
    Returns the model name for the given door.

    If no value is specified for the genericdoor parameters then it will be loaded from the given installation.

    Args:
        utd: UTD object of the target door.
        installation: The relevant installation.
        genericdoors: The genericdoors.2da loaded into a TwoDA object.

    Returns:
        Returns the model name for the door.
    """
    if genericdoors is None:
        genericdoors = installation.resource("placeables", ResourceType.TwoDA)

    return genericdoors.get_row(utd.appearance_id).get_string("modelname")
