"""Base dialog classes and utilities."""

from __future__ import annotations

from enum import IntEnum
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Sequence, TypeVar, cast

from pykotor.common.misc import ResRef
from pykotor.resource.generics.dlg.links import DLGLink
from pykotor.resource.generics.dlg.nodes import DLGEntry, DLGNode, DLGReply
from pykotor.resource.type import ResourceType

if TYPE_CHECKING:
    from pykotor.resource.generics.dlg.stunts import DLGStunt

T = TypeVar("T", bound=DLGNode)


class DLGComputerType(IntEnum):
    """Type of computer interface for dialog."""

    Modern = 0
    Ancient = 1


class DLGConversationType(IntEnum):
    """Type of conversation for dialog."""

    Human = 0
    Computer = 1
    Other = 2


class DLG:
    """Stores dialog data.

    Attributes:
    ----------
        word_count: "NumWords" field.
        on_abort: "EndConverAbort" field.
        on_end: "EndConversation" field.
        skippable: "Skippable" field.
        ambient_track: "AmbientTrack" field.
        animated_cut: "AnimatedCut" field.
        camera_model: "CameraModel" field.
        computer_type: "ComputerType" field.
        conversation_type: "ConversationType" field.
        old_hit_check: "OldHitCheck" field.
        unequip_hands: "UnequipHItem" field.
        unequip_items: "UnequipItems" field.
        vo_id: "VO_ID" field.

        alien_race_owner: "AlienRaceOwner" field. KotOR 2 Only.
        post_proc_owner: "PostProcOwner" field. KotOR 2 Only.
        record_no_vo: "RecordNoVO" field. KotOR 2 Only.
        next_node_id: "NextNodeID" field. KotOR 2 Only.

        delay_entry: "DelayEntry" field. Not used by the game engine.
        delay_reply: "DelayReply" field. Not used by the game engine.
    """

    BINARY_TYPE = ResourceType.DLG

    def __init__(
        self,
    ):
        self.starters: list[DLGLink[DLGEntry]] = []
        self.stunts: list[DLGStunt] = []

        self.ambient_track: ResRef = ResRef.from_blank()
        self.animated_cut: int = 0
        self.camera_model: ResRef = ResRef.from_blank()
        self.computer_type: DLGComputerType = DLGComputerType.Modern
        self.conversation_type: DLGConversationType = DLGConversationType.Human
        self.on_abort: ResRef = ResRef.from_blank()
        self.on_end: ResRef = ResRef.from_blank()
        self.word_count: int = 0
        self.old_hit_check: bool = False
        self.skippable: bool = False
        self.unequip_items: bool = False
        self.unequip_hands: bool = False
        self.vo_id: str = ""

        # KotOR 2:
        self.alien_race_owner: int = 0
        self.next_node_id: int = 0
        self.post_proc_owner: int = 0
        self.record_no_vo: int = 0

        # Deprecated:
        self.delay_entry: int = 0
        self.delay_reply: int = 0

    def find_paths(
        self,
        target: DLGEntry | DLGReply | DLGLink,
    ) -> list[PureWindowsPath]:
        """Find all paths to a target node or link.

        Args:
            target: The target node or link to find paths to

        Returns:
            A list of paths to the target
        """
        paths: list[PureWindowsPath] = []

        if isinstance(target, DLGLink):
            parent_node: DLGEntry | DLGReply | DLG | None = self.get_link_parent(target)
            if parent_node is None:
                raise ValueError(f"Target {target.__class__.__name__} doesn't have a parent, and also not found in starters.")
            if isinstance(parent_node, DLG):
                paths.append(PureWindowsPath("StartingList", str(target.list_index)))
            else:
                self._find_paths_for_link(parent_node, target, paths)
        else:
            self._find_paths_recursive(self.starters, target, PureWindowsPath(), paths, set())

        return paths

    def _find_paths_for_link(
        self,
        parent_node: DLGNode,
        target: DLGLink,
        paths: list[PureWindowsPath],
    ):
        """Find paths for a link from its parent node.

        Args:
            parent_node: The parent node containing the link
            target: The target link to find paths to
            paths: List to store found paths in
        """
        if isinstance(parent_node, DLGEntry):
            node_list_name = "EntryList"
        else:
            node_list_name = "ReplyList"
        parent_path = PureWindowsPath(node_list_name, str(parent_node.list_index))

        if isinstance(parent_node, DLGEntry):
            link_list_name = "RepliesList"
        else:
            link_list_name = "EntriesList"

        paths.append(parent_path / link_list_name / str(target.list_index))

    def _find_paths_recursive(
        self,
        links: Sequence[DLGLink[T]],
        target: DLGNode,
        current_path: PureWindowsPath,
        paths: list[PureWindowsPath],
        seen_links_and_nodes: set[DLGNode | DLGLink],
    ):
        """Recursively find paths to a target node.

        Args:
            links: The links to search through
            target: The target node to find paths to
            current_path: The current path being built
            paths: List to store found paths in
            seen_links_and_nodes: Set of already visited links and nodes
        """
        for link in links:
            if link is None or link in seen_links_and_nodes:
                continue

            seen_links_and_nodes.add(link)
            node: DLGNode = link.node
            assert node is not None, "Corrupted DLG/buggy code detected"

            if node == target:
                if node in seen_links_and_nodes:
                    continue
                seen_links_and_nodes.add(node)
                if isinstance(node, DLGEntry):
                    paths.append(PureWindowsPath("EntryList", str(node.list_index)))
                else:
                    paths.append(PureWindowsPath("ReplyList", str(node.list_index)))
                continue

            if node not in seen_links_and_nodes:
                seen_links_and_nodes.add(node)
                if isinstance(node, DLGEntry):
                    node_list_name, link_list_name = "EntryList", "RepliesList"
                else:
                    node_list_name, link_list_name = "ReplyList", "EntriesList"
                node_path = PureWindowsPath(node_list_name, str(node.list_index))

                # Cast to handle type variance
                self._find_paths_recursive(
                    cast(Sequence[DLGLink[T]], node.links),
                    target,
                    current_path / node_path / link_list_name,
                    paths,
                    seen_links_and_nodes,
                )

    def get_link_parent(
        self,
        target_link: DLGLink,
    ) -> DLGEntry | DLGReply | DLG | None:
        """Find the parent node of a given link.

        Args:
            target_link: The link to find the parent for

        Returns:
            The parent node or None if not found
        """
        if target_link in self.starters:
            return self
        return next(
            (node for node in self.all_entries() + self.all_replies() if target_link in node.links),
            None,
        )

    def all_entries(
        self,
        *,
        as_sorted: bool = False,
    ) -> list[DLGEntry]:
        """Get all entries in the dialog.

        Args:
            as_sorted: Whether to sort entries by list_index

        Returns:
            List of all entries
        """
        entries: list[DLGEntry] = self._all_entries()
        if not as_sorted:
            return entries
        return sorted(
            entries,
            key=lambda entry: (entry.list_index == -1, entry.list_index),
        )

    def _all_entries(
        self,
        links: Sequence[DLGLink[DLGEntry]] | None = None,
        seen_entries: set[DLGEntry] | None = None,
    ) -> list[DLGEntry]:
        """Recursively collect all entries.

        Args:
            links: Links to search through
            seen_entries: Set of already seen entries

        Returns:
            List of all entries found
        """
        entries: list[DLGEntry] = []

        links = self.starters if links is None else links
        seen_entries = set() if seen_entries is None else seen_entries

        for link in links:
            entry: DLGNode | None = link.node
            if entry is None:
                continue
            if entry in seen_entries:
                continue
            if not isinstance(entry, DLGEntry):
                continue
            entries.append(entry)
            seen_entries.add(entry)
            for reply_link in entry.links:
                reply: DLGNode = reply_link.node
                entries.extend(self._all_entries(cast(Sequence[DLGLink[DLGEntry]], reply.links), seen_entries))

        return entries

    def all_replies(
        self,
        *,
        as_sorted: bool = False,
    ) -> list[DLGReply]:
        """Get all replies in the dialog.

        Args:
            as_sorted: Whether to sort replies by list_index

        Returns:
            List of all replies
        """
        replies: list[DLGReply] = self._all_replies()
        if not as_sorted:
            return replies
        return sorted(replies, key=lambda reply: (reply.list_index == -1, reply.list_index))

    def _all_replies(
        self,
        links: Sequence[DLGLink] | None = None,
        seen_replies: list[DLGReply] | None = None,
    ) -> list[DLGReply]:
        """Recursively collect all replies.

        Args:
            links: Links to search through
            seen_replies: List of already seen replies

        Returns:
            List of all replies found
        """
        replies: list[DLGReply] = []

        links = [_ for link in self.starters if link.node is not None for _ in link.node.links] if links is None else links
        seen_replies = [] if seen_replies is None else seen_replies

        for link in links:
            reply: DLGNode = link.node
            if reply in seen_replies:
                continue
            if not isinstance(reply, DLGReply):
                continue
            replies.append(reply)
            seen_replies.append(reply)
            for entry_link in reply.links:
                entry: DLGNode | None = entry_link.node
                if entry is None:
                    continue
                replies.extend(self._all_replies(cast(Sequence[DLGLink], entry.links), seen_replies))

        return replies
