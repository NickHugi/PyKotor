from __future__ import annotations

import ast
import builtins
import json
import os
import pathlib
import re
import sys
import typing

from abc import ABC
from contextlib import suppress
from dataclasses import MISSING, dataclass, fields
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar, Union, get_args, get_origin, overload

from utility.system.path import Path, PurePath

if TYPE_CHECKING:

    from typing_extensions import Self


if __name__ == "__main__":
    with suppress(Exception):
        def update_sys_path(path: pathlib.Path):
            working_dir = str(path)
            if working_dir not in sys.path:
                sys.path.append(working_dir)

        file_absolute_path = pathlib.Path(__file__).resolve()

        pykotor_path = file_absolute_path.parents[6] / "Libraries" / "PyKotor" / "src" / "pykotor"
        if pykotor_path.exists():
            update_sys_path(pykotor_path.parent)
        pykotor_gl_path = file_absolute_path.parents[6] / "Libraries" / "PyKotorGL" / "src" / "pykotor"
        if pykotor_gl_path.exists():
            update_sys_path(pykotor_gl_path.parent)
        utility_path = file_absolute_path.parents[6] / "Libraries" / "Utility" / "src"
        if utility_path.exists():
            update_sys_path(utility_path)
        toolset_path = file_absolute_path.parents[5] / "Tools/HolocronToolset/src/toolset"
        if toolset_path.exists():
            update_sys_path(toolset_path.parent)
            os.chdir(toolset_path)

T = TypeVar("T")

class AbstractAPIResult(ABC):  # noqa: B024
    _type_cache: ClassVar[dict] = {}

    def __getitem__(self, attr_name: str):
        return self.__dict__[attr_name]

    def __setitem__(self, attr_name: str, value: Any):
        self.__dict__[attr_name] = value

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> Self:
        assert isinstance(json_dict, dict), f"type {json_dict.__class__.__name__} with contents {json_dict}"
        processed_data = {}
        for this_field in fields(cls):
            key = this_field.name
            expected_type = this_field.metadata.get("default_type", (this_field.type,))
            if key not in json_dict:
                #print(f"{cls.__name__} Warning: Missing expected key '{key}' in data")
                processed_data[key] = this_field.default if this_field.default is not MISSING else None
            else:
                value = json_dict[key]
                processed_data[key] = cls.handle_casting(value, expected_type)

        #for key, value in json_dict.items():
            #if key not in processed_data:
            #    print(f"{cls.__name__} Warning: Unexpected key '{key}' in data with value '{value!r}'")

        return cls(**processed_data)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, AbstractAPIResult):
                result[field.name] = value.to_dict()
            elif isinstance(value, list):
                result[field.name] = [item.to_dict() if isinstance(item, AbstractAPIResult) else item for item in value]
            elif isinstance(value, dict):
                result[field.name] = {k: v.to_dict() if isinstance(v, AbstractAPIResult) else v for k, v in value.items()}
            else:
                result[field.name] = value
        return result

    @classmethod
    def resolve_type(cls, type_str: str):
        # sourcery skip: assign-if-exp, reintroduce-else
        def resolve(node):
            if isinstance(node, ast.Name):
                # Map 'list', 'dict' to typing versions when used in type annotations
                if node.id == "list":
                    return typing.List
                if node.id == "dict":
                    return typing.Dict
                if node.id == "None":
                    return type(None)
                # Check builtins and typing module for other types
                if hasattr(builtins, node.id):
                    return getattr(builtins, node.id)
                if hasattr(typing, node.id):
                    return getattr(typing, node.id)
                # Check current module's namespace
                if node.id in globals():
                    return globals()[node.id]
                # Check imported modules in current context
                if node.id in sys.modules:
                    return sys.modules[node.id]
            elif isinstance(node, ast.Subscript):
                base = resolve(node.value)
                if isinstance(node.slice, ast.Index):  # Python 3.8 and earlier
                    index = resolve(node.slice.value)
                elif isinstance(node.slice, ast.Tuple):  # Multiple type parameters
                    index = tuple(resolve(i) for i in node.slice.elts)
                else:
                    index = resolve(node.slice)
                # Handle 'None' within subscript parameters
                if isinstance(index, tuple):
                    index = tuple(i if i is not None else type(None) for i in index)
                    return base[index]
                # Handle the case where the entire index is None
                if index is None:
                    return typing.Union[base, type(None)]
                return base[index]
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                # Handle union types like 'int | None'
                left = resolve(node.left)
                right = resolve(node.right)
                return typing.Union[left, right]
            elif isinstance(node, ast.Constant) and node.value is None:
                return type(None)
            return None

        tree = ast.parse(type_str, mode="eval")
        assert not isinstance(tree, str), "Parsed tree should not be a string."
        resolved_type = resolve(tree.body)
        cls._type_cache[type_str] = resolved_type
        return resolved_type

    @classmethod
    def handle_casting(cls, value: Any, expected_types: tuple[type[T], ...]) -> T:
        # Optimize by caching converted types
        converted_types = tuple(cls._type_cache.get(t, cls.resolve_type(t) if isinstance(t, str) else t) for t in expected_types)
        cls._type_cache.update(zip(expected_types, converted_types))

        # Convert all string type names to actual types
        converted_types = []
        for this_type in expected_types:
            if isinstance(this_type, str):
                converted_types.append(cls.resolve_type(this_type))
            else:
                converted_types.append(this_type)
        converted_types = tuple(converted_types)

        if value is None:
            for this_type in converted_types:
                origin = get_origin(this_type) if hasattr(this_type, "__origin__") else this_type
                args = get_args(this_type)
                if origin is None:
                    return None
                if type(None) in args:
                    return None
            raise TypeError(f"Expected value of type(s) {converted_types}, got value of None")

        for this_type in converted_types:
            if this_type is typing.Any:
                return value
            origin = get_origin(this_type) if hasattr(this_type, "__origin__") else this_type
            args = get_args(this_type)

            if origin is Union:
                # Handle Union types
                for arg in args:
                    try:
                        return cls.handle_casting(value, (arg,))
                    except (TypeError, ValueError):  # noqa: S112, PERF203
                        continue
                raise ValueError(f"Value {value} does not match any type in {expected_types}")

            if origin and issubclass(origin, str):
                if isinstance(value, str):
                    return value
                raise ValueError(f"Expected value of type {origin}, got {type(value)}")

            if issubclass(origin, typing.Mapping):
                if not value and isinstance(value, origin):  # Empty check
                    return value
                # Handle mapping types
                key_type, value_type = args if len(args) == 2 else (Any, Any)
                return {cls.handle_casting(k, (key_type,)): cls.handle_casting(v, (value_type,)) for k, v in value.items()}

            if issubclass(origin, typing.Iterable):
                if not value and isinstance(value, origin):  # Empty check
                    return value
                # Handle iterable types
                item_type = args[0] if args else Any
                return [cls.handle_casting(item, (item_type,)) for item in value]

            # Handle non-generic types
            if isinstance(value, origin):
                return value
            if issubclass(origin, AbstractAPIResult):
                return origin.from_dict(value)

            # Attempt to convert the value to the expected type
            return origin(value)

        raise ValueError(f"Expected value of type {expected_types}, got {type(value)} with data '{value}'")


@dataclass
class Asset(AbstractAPIResult):
    url: str = ""
    id: int = -1
    name: str = ""
    label: str | None = None
    state: str = ""
    content_type: str = ""
    size: int = -1
    download_count: int = -1
    created_at: str = ""
    updated_at: str = ""
    browser_download_url: str = ""
    node_id: int = -1
    uploader: str = ""


@dataclass
class LinksData(AbstractAPIResult):
    self: str
    git: str | None
    html: str


@dataclass
class ContentInfoData(AbstractAPIResult):
    name: str
    path: str
    sha: str
    size: int
    url: str
    html_url: str
    git_url: str
    download_url: str | None
    type: str
    _links: LinksData


@dataclass
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



@dataclass
class LinksData(AbstractAPIResult):
    self: str
    git: str | None
    html: str


@dataclass
class ForkContentsData(AbstractAPIResult):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: UserInfoData
    html_url: str
    description: str | None
    has_discussions: bool
    fork: bool
    url: str
    forks_url: str
    keys_url: str
    collaborators_url: str
    teams_url: str
    hooks_url: str
    issue_events_url: str
    events_url: str
    assignees_url: str
    branches_url: str
    tags_url: str
    blobs_url: str
    git_tags_url: str
    git_refs_url: str
    trees_url: str
    statuses_url: str
    languages_url: str
    stargazers_url: str
    contributors_url: str
    subscribers_url: str
    subscription_url: str
    commits_url: str
    git_commits_url: str
    comments_url: str
    issue_comment_url: str
    contents_url: str
    compare_url: str
    merges_url: str
    archive_url: str
    downloads_url: str
    issues_url: str
    pulls_url: str
    milestones_url: str
    notifications_url: str
    labels_url: str
    releases_url: str
    deployments_url: str
    created_at: str
    updated_at: str
    pushed_at: str
    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: str
    homepage: str | None
    size: int
    stargazers_count: int
    watchers_count: int
    language: str | None
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    forks_count: int
    mirror_url: str | None
    archived: bool
    disabled: bool
    open_issues_count: int
    license: dict[str, Any] | None
    allow_forking: bool
    is_template: bool
    web_commit_signoff_required: bool
    topics: list[str]
    visibility: str
    forks: int
    open_issues: int
    watchers: int
    default_branch: str


@dataclass
class RepoIndexData(ForkContentsData):
    temp_clone_token: str | None
    custom_properties: dict[str, Any]
    organization: UserInfoData | None
    network_count: int
    subscribers_count: int


@dataclass
class CommitTreeInfo(AbstractAPIResult):
    sha: str
    url: str


@dataclass
class UserInfoData(AbstractAPIResult):
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    site_admin: bool


@dataclass
class ContributorsInfoData(UserInfoData):
    contributions: int


@dataclass
class AuthorInfoData(AbstractAPIResult):
    name: str
    email: str
    date: str


@dataclass
class CommitDetailData(AbstractAPIResult):
    author: AuthorInfoData
    committer: AuthorInfoData
    message: str
    tree: CommitTreeInfo
    url: str
    comment_count: int
    verification: VerificationInfoData


@dataclass
class VerificationInfoData(AbstractAPIResult):
    verified: bool
    reason: str
    signature: str | None
    payload: str | None


@dataclass
class CommitInfoData(AbstractAPIResult):
    sha: str
    node_id: str
    commit: CommitDetailData
    url: str
    html_url: str
    comments_url: str
    author: UserInfoData
    committer: UserInfoData
    parents: list[ParentCommitInfoData]


@dataclass
class ParentCommitInfoData(CommitTreeInfo):
    html_url: str


@dataclass
class BranchInfoData(AbstractAPIResult):
    name: str
    commit: CommitTreeInfo
    protected: bool


@dataclass
class TreeInfoData(AbstractAPIResult):
    path: str
    mode: str
    type: str
    sha: str
    size: int | None
    url: str


@dataclass
class CompleteRepoData(AbstractAPIResult):
    repo_info: RepoIndexData
    branches: list[BranchInfoData]
    #commits: list[CommitInfoData]
    #issues: list[dict[str, Any]]
    #pulls: list[dict[str, Any]]
    #contributors: list[ContributorsInfoData]
    #releases: list[GithubRelease]
    #tags: list[dict[str, Any]]
    contents: list[ContentInfoData]
    #languages: dict[str, Any]
    forks: list[ForkContentsData]
    #stargazers: list[dict[str, Any]]
    #subscribers: list[dict[str, Any]]
    tree: list[TreeInfoData]

    def __getattr__(self, attr_name: str):
        return self.__dict__[attr_name]

    def get_main_branch_files(self) -> list[ContentInfoData]:
        main_branch = next((branch for branch in self.branches if branch.name == self.repo_info.default_branch), None)
        if not main_branch:
            raise ValueError(f"Main branch {self.repo_info.default_branch} not found in branches")

        return [content for content in self.contents if content.path.startswith(main_branch.commit.sha)]

    @classmethod
    def load_repo(cls, owner: str, repo_name: str, *, timeout: int = 15) -> CompleteRepoData:
        base_url = f"https://api.github.com/repos/{owner}/{repo_name}"

        endpoints = {
            "repo_info": base_url,
            "branches": f"{base_url}/branches",
            "contents": f"{base_url}/contents",
            "forks": f"{base_url}/forks"
        }

        repo_data = {}
        import requests
        for key, url in endpoints.items():
            print(f"Fetching {key}...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            repo_data[key] = response.json()

        # Fetch the tree using the correct default branch
        default_branch = repo_data.get("repo_info", {}).get("default_branch", "main")
        tree_url = f"{base_url}/git/trees/{default_branch}?recursive=1"
        print(f"Fetching tree from {tree_url}...")
        tree_response = requests.get(tree_url, timeout=timeout)
        if tree_response.status_code == 200:
            repo_data["tree"] = tree_response.json().get("tree", [])
        else:
            print(f"Failed to fetch tree from {tree_url}")

        instance = cls(
            repo_info=RepoIndexData.from_dict(repo_data.get("repo_info", {})),
            branches=[BranchInfoData.from_dict(item) for item in repo_data.get("branches", [])],
            contents=[ContentInfoData.from_dict(item) for item in repo_data.get("contents", [])],
            forks=[ForkContentsData.from_dict(item) for item in repo_data.get("forks", [])],
            tree=[TreeInfoData.from_dict(item) for item in repo_data.get("tree", [])]
        )
        print(f"Completed loading of '{base_url}'")
        return instance

    @classmethod
    def load_repo_from_files(cls, folder_path: str) -> CompleteRepoData:
        def load_json(file_path: str) -> Any:
            with open(file_path) as file:
                return json.load(file)

        repo_data = {
            "repo_info": load_json(os.path.join(folder_path, "repo_info.json")),
            "branches": load_json(os.path.join(folder_path, "branches.json")),
        #    "commits": load_json(os.path.join(folder_path, "commits.json")),
        #    "issues": load_json(os.path.join(folder_path, "issues.json")),
        #    "pulls": load_json(os.path.join(folder_path, "pulls.json")),
        #    "contributors": load_json(os.path.join(folder_path, "contributors.json")),
        #    "releases": load_json(os.path.join(folder_path, "releases.json")),
        #    "tags": load_json(os.path.join(folder_path, "tags.json")),
            "contents": load_json(os.path.join(folder_path, "contents.json")),
        #    "languages": load_json(os.path.join(folder_path, "languages.json")),
            "forks": load_json(os.path.join(folder_path, "forks.json")),
        #    "stargazers": load_json(os.path.join(folder_path, "stargazers.json")),
        #    "subscribers": load_json(os.path.join(folder_path, "subscribers.json")),
        }

        return cls(
            repo_info=RepoIndexData.from_dict(repo_data.get("repo_info", {})),
            branches=[BranchInfoData.from_dict(item) for item in repo_data.get("branches", [])],
        #    commits=[CommitInfoData.from_dict(item) for item in repo_data.get("commits", [])],
        #    issues=repo_data.get("issues", []),
        #    pulls=repo_data.get("pulls", []),
        #    contributors=[ContributorsInfoData.from_dict(item) for item in repo_data.get("contributors", [])],
        #    releases=[GithubRelease.from_dict(item) for item in repo_data.get("releases", [])],
        #    tags=repo_data.get("tags", []),
            contents=[ContentInfoData.from_dict(item) for item in repo_data.get("contents", [])],
        #    languages=repo_data.get("languages", {}),
            forks=[ForkContentsData.from_dict(item) for item in repo_data.get("forks", [])],
        #    stargazers=repo_data.get("stargazers", []),
        #    subscribers=repo_data.get("subscribers", []),
        )


def download_github_file(
    url_or_repo: str | tuple[str, str],
    local_path: os.PathLike | str,
    repo_path: os.PathLike | str | None = None,
    timeout: int | None = None,
):
    import requests
    timeout = 180 if timeout is None else timeout
    local_path = Path(local_path).absolute()
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(url_or_repo, tuple):
        owner, repo = url_or_repo
        base_url = f"https://api.github.com/repos/{owner}/{repo}"
    elif "https://api.github.com/repos/" in url_or_repo:
        base_url = url_or_repo.rsplit("/", 1)[0]
    else:
        owner, repo = url_or_repo.split("/")[-2:]
        base_url = f"https://api.github.com/repos/{owner}/{repo}"

    if repo_path is not None:
        api_url = f"{base_url}/contents/{PurePath(repo_path).as_posix()}"
        file_info: dict[str, str] = _request_api_data(api_url)
        if file_info["type"] == "file":
            download_url = file_info["download_url"]
        else:
            raise ValueError("The provided repo_path does not point to a file.")
    else:
        download_url = url_or_repo

    with requests.get(download_url, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        with local_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def download_github_directory(
    repo: str | tuple[str, str],
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


@overload
def fetch_repo_index(owner: str, repo: str, branch: str = "master") -> dict[str, str]: ...
@overload
def fetch_repo_index(repo: str, branch: str = "master") -> dict[str, str]: ...
def fetch_repo_index(owner_or_repo: str | tuple[str, str], repo: str=None, branch: str = "master") -> dict[str, str]:
    """Fetches the index of a GitHub repository.

    Args:
    ----
        owner: The owner of the repository.
        repo: The name of the repository.
        branch: The branch of the repository.

    Returns:
    -------
        A dictionary mapping file paths in the repo to their respective GitHub URLs.
    """
    import requests
    if repo is None:
        owner_or_repo, repo = extract_owner_repo(owner_or_repo)
    api_url = f"https://api.github.com/repos/{owner_or_repo}/{repo}/git/trees/{branch}?recursive=1"
    response = requests.get(api_url, timeout=15)
    response.raise_for_status()
    data: dict[str, Any] = response.json()

    repo_index = {
        item["path"]: f"https://github.com/{owner_or_repo}/{repo}/blob/{branch}/{item['path']}"
        for item in data.get("tree", [])
        if item["type"] == "blob"
    }
    return repo_index


def _request_api_data(api_url: str) -> Any:
    import requests
    response: requests.Response = requests.get(api_url, timeout=15)
    response.raise_for_status()
    return response.json()


@overload
def get_api_url(owner: str, repo: str) -> str: ...
@overload
def get_api_url(repo: str) -> str: ...
def get_api_url(owner: str, repo: str=None) -> str:
    if repo is None:
        owner, repo = extract_owner_repo(owner)
    return f"https://api.github.com/repos/{owner}/{repo}"


@overload
def get_forks_url(owner: str, repo: str) -> str: ...
@overload
def get_forks_url(repo: str) -> str: ...
def get_forks_url(owner: str, repo: str=None) -> str:
    if repo is None:
        owner, repo = extract_owner_repo(owner)
    return f"https://api.github.com/repos/{owner}/{repo}/forks"


@overload
def get_main_url(owner: str, repo: str) -> str: ...
@overload
def get_main_url(repo: str) -> str: ...
def get_main_url(owner: str, repo: str=None) -> str:
    if repo is None:
        owner, repo = extract_owner_repo(owner)
    return f"https://github.com/{owner}/{repo}"


def extract_owner_repo_from_api_url(url: str) -> tuple[str, str]:
    pattern = re.compile(r"https://api\.github\.com/repos/([^/]+)/([^/]+)")
    match = pattern.match(url)
    if not match:
        raise ValueError("Invalid GitHub API URL")
    return match[1], match[2]

def extract_owner_repo_from_raw_url(url: str) -> tuple[str, str]:
    pattern = re.compile(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)")
    match = pattern.match(url)
    if not match:
        raise ValueError("Invalid GitHub raw content URL")
    return match[1], match[2]

def extract_owner_repo_from_main_url(url: str) -> tuple[str, str]:
    pattern = re.compile(r"https://github\.com/([^/]+)/([^/]+)")
    match = pattern.match(url)
    if not match:
        raise ValueError("Invalid GitHub main URL")
    return match[1], match[2]

def extract_owner_repo(url: str) -> tuple[str, str]:
    if "api.github.com/repos" in url:
        return extract_owner_repo_from_api_url(url)
    if "raw.githubusercontent.com" in url:
        return extract_owner_repo_from_raw_url(url)
    if "github.com" in url:
        return extract_owner_repo_from_main_url(url)
    raise ValueError(f"Invalid GitHub URL format: {url}")

if __name__ == "__main__":
    import sys

    from toolset.__main__ import onAppCrash
    sys.excepthook = onAppCrash
    test1 = CompleteRepoData.load_repo_from_files(r"C:\GitHub\PyKotor\KOTORCommunityPatches_Vanilla_KOTOR_Script_Source\json files")
    test1_dict = test1.to_dict()
    print(json.dumps(test1_dict, indent=4))
