from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING, Any

from toolset.config import get_remote_toolset_update_info
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from concurrent.futures import Future


def fetch_update_info(use_beta: bool, silent: bool) -> dict[str, Any]:
    result = get_remote_toolset_update_info(useBetaChannel=use_beta, silent=silent)
    if isinstance(result, Exception):
        raise result
    return result

def check_for_updates(
    silent: bool = False,
) -> tuple[Future[dict[str, Any]], Future[dict[str, Any]], bool]:
    edge_info: dict[str, Any] = {}
    master_info: dict[str, Any] = {}

    with ProcessPoolExecutor() as executor:
        if GlobalSettings().useBetaChannel:
            edge_future = executor.submit(fetch_update_info, True, silent)
        master_future = executor.submit(fetch_update_info, False, silent)

        if GlobalSettings().useBetaChannel:
            edge_info = edge_future.result()
        master_info = master_future.result()

    return master_info, edge_info, silent
