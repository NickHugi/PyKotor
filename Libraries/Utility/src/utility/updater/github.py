from __future__ import annotations

import dataclasses

from typing import TYPE_CHECKING, Any

from utility.system.path import Path, PurePath

if TYPE_CHECKING:
    import os


@dataclasses.dataclass
class Asset:
    url: str
    id: int
    name: str
    label: str | None
    state: str
    content_type: str
    size: int
    download_count: int
    created_at: str
    updated_at: str
    browser_download_url: str
    node_id: Any
    uploader: Any

@dataclasses.dataclass
class GithubRelease:
    url: str
    assets_url: str
    upload_url: str
    html_url: str
    id: int
    author: dict
    node_id: str
    tag_name: str
    target_commitish: str
    name: str
    draft: bool
    prerelease: bool
    created_at: str
    published_at: str
    assets: list[Asset]
    tarball_url: str
    zipball_url: str
    body: str

    @staticmethod
    def from_json(json_dict: dict) -> GithubRelease:
        assets = [Asset(**asset) for asset in json_dict.get("assets", [])]
        return GithubRelease(
            url=json_dict["url"],
            assets_url=json_dict["assets_url"],
            upload_url=json_dict["upload_url"],
            html_url=json_dict["html_url"],
            id=json_dict["id"],
            author=json_dict["author"],
            node_id=json_dict["node_id"],
            tag_name=json_dict["tag_name"],
            target_commitish=json_dict["target_commitish"],
            name=json_dict["name"],
            draft=json_dict["draft"],
            prerelease=json_dict["prerelease"],
            created_at=json_dict["created_at"],
            published_at=json_dict["published_at"],
            assets=assets,
            tarball_url=json_dict["tarball_url"],
            zipball_url=json_dict["zipball_url"],
            body=json_dict["body"]
        )

def download_github_file(
    url_or_repo: str,
    local_path: os.PathLike | str,
    repo_path: os.PathLike | str | None = None,
    timeout: int | None = None,
):
    import requests
    timeout = 180 if timeout is None else timeout
    local_path = Path(local_path).absolute()
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if repo_path is not None:
        # Construct the API URL for the file in the repository
        owner, repo = PurePath(url_or_repo).parts[-2:]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{PurePath(repo_path).as_posix()}"

        file_info: dict[str, str] = _request_api_data(api_url)
        # Check if it's a file and get the download URL
        if file_info["type"] == "file":
            download_url = file_info["download_url"]
        else:
            msg = "The provided repo_path does not point to a file."
            raise ValueError(msg)
    else:
        # Direct URL
        download_url = url_or_repo

    # Download the file
    with requests.get(download_url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with local_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def download_github_directory(
    repo: os.PathLike | str,
    local_dir: os.PathLike | str,
    repo_path: os.PathLike | str,
):
    """This method should not be used due to github's api restrictions. Use download_file to get a .zip of the folder instead."""  # noqa: D404
    repo = PurePath(repo)
    repo_path = PurePath(repo_path)
    api_url = f"https://api.github.com/repos/{repo.as_posix()}/contents/{repo_path.as_posix()}"
    data = _request_api_data(api_url)
    for item in data:
        item_path = Path(item["path"])
        local_path = item_path.relative_to("toolset")

        if item["type"] == "file":
            download_github_file(item["download_url"], Path(local_dir, local_path))
        elif item["type"] == "dir":
            download_github_directory(repo, item_path, local_path)


def download_github_directory_fallback(
    repo: os.PathLike | str,
    local_dir: os.PathLike | str,
    repo_path: os.PathLike | str,
):
    """There were two versions of this function and I can't remember which one worked."""
    repo = PurePath.pathify(repo)
    repo_path = PurePath.pathify(repo_path)
    api_url = f"https://api.github.com/repos/{repo.as_posix()}/contents/{repo_path.as_posix()}"
    data = _request_api_data(api_url)
    for item in data:
        item_path = Path(item["path"])
        local_path = item_path.relative_to("toolset")

        if item["type"] == "file":
            download_github_file(item["download_url"], local_path)
        elif item["type"] == "dir":
            download_github_directory(repo, item_path, local_path)


def _request_api_data(api_url: str) -> Any:
    import requests
    response: requests.Response = requests.get(api_url, timeout=15)
    response.raise_for_status()
    return response.json()
