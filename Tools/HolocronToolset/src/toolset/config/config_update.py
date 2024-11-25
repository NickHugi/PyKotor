from __future__ import annotations

import base64
import json
import re

from contextlib import suppress
from typing import Any, Literal

import requests

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtWidgets import QMessageBox

from toolset.config.config_info import LOCAL_PROGRAM_INFO
from utility.error_handling import universal_simplify_exception


def fetch_update_info(
    update_link: str,
    timeout: int = 15,
) -> dict[str, Any]:
    req: requests.Response = requests.get(
        update_link,
        timeout=timeout,
    )
    req.raise_for_status()
    file_data: dict[str, Any] = req.json()
    return file_data


def get_remote_toolset_update_info(
    *,
    use_beta_channel: bool = False,
    silent: bool = False,
) -> Exception | dict[str, Any]:
    if use_beta_channel:
        update_info_link: str = LOCAL_PROGRAM_INFO["updateBetaInfoLink"]
    else:
        update_info_link: str = LOCAL_PROGRAM_INFO["updateInfoLink"]

    try:
        timeout: Literal[2, 10] = 2 if silent else 10
        file_data: dict[str, Any] = fetch_update_info(update_info_link, timeout)
        base64_content: str = file_data["content"]
        decoded_content: bytes = base64.b64decode(base64_content)
        decoded_content_str: str = decoded_content.decode(encoding="utf-8")
        json_data_match: re.Match[str] | None = re.search(r"<---JSON_START--->\s*\#\s*(.*?)\s*\#\s*<---JSON_END--->", decoded_content_str, flags=re.DOTALL)

        if not json_data_match:
            raise ValueError(f"JSON data not found or markers are incorrect: {json_data_match}")  # noqa: TRY301
        json_str: str = json_data_match[1]
        remote_info: dict[str, Any] = json.loads(json_str)
        if not isinstance(remote_info, dict):
            raise TypeError(f"Expected remote_info to be a dict, instead got type {remote_info.__class__.__name__}")  # noqa: TRY301
    except Exception as e:  # noqa: BLE001
        err_msg: str = str(universal_simplify_exception(e))
        result: int | QMessageBox.StandardButton = silent or QMessageBox.question(
            None,
            "Error occurred fetching update information.",
            ("An error occurred while fetching the latest toolset information.<br><br>" + err_msg.replace("\n", "<br>") + "<br><br>" + "Would you like to check against the local database instead?"),  # noqa: E501
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if result not in {QMessageBox.StandardButton.Yes, True}:
            return e
        remote_info: dict[str, Any] = LOCAL_PROGRAM_INFO
    return remote_info


def is_remote_version_newer(
    local_version: str,
    remote_version: str,
) -> bool | None:
    version_check: bool | None = None
    with suppress(Exception):
        from packaging import version

        version_check = version.parse(remote_version) > version.parse(local_version)
    if version_check is None:
        RobustLogger().warning(f"Version string might be malformed, attempted 'packaging.version.parse({local_version}) > packaging.version.parse({remote_version})'")
        with suppress(Exception):
            from distutils.version import LooseVersion

            version_check = LooseVersion(remote_version) > LooseVersion(local_version)
    return version_check
