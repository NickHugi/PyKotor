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
    
    DLG files are GFF-based format files that store dialog trees with entries, replies,
    links, and conversation metadata. The dialog system uses a graph structure where
    entries (NPC lines) and replies (player options) are connected via links with
    conditional logic.
    
    References:
    ----------
        vendor/reone/include/reone/resource/parser/gff/dlg.h:115-141 (DLG struct definition)
        vendor/reone/src/libs/resource/parser/gff/dlg.cpp:37-172 (DLG parsing from GFF)
        vendor/reone/include/reone/resource/dialog.h (Dialog resource abstraction)
        vendor/KotOR.js/src/resource/DLGObject.ts (DLG loading and dialog tree structure)
        vendor/KotOR.js/src/resource/DLGNode.ts (DLG node structure)
        vendor/xoreos-tools/src/xml/dlgdumper.cpp (DLG to XML conversion)
        vendor/xoreos-tools/src/xml/dlgcreator.cpp (XML to DLG conversion)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorDLG/DLG.cs (DLG structure)
        vendor/Kotor.NET/Kotor.NET/Resources/KotorDLG/DLGDecompiler.cs (DLG parsing)
        Note: DLG files are GFF format files with specific structure definitions

    Attributes:
    ----------
        starters: "StartingList" field. List of initial dialog links.
            Reference: reone/dlg.h:136 (StartingList vector)
            Reference: reone/dlg.cpp:170-171 (StartingList parsing)
            The entry points into the dialog tree.
        
        stunts: "StuntList" field. List of stunt model references.
            Reference: reone/dlg.h:56-59 (DLG_StuntList struct)
            Reference: reone/dlg.cpp:60-65 (StuntList parsing)
            Used for special dialog animations.
        
        word_count: "NumWords" field. Word count for dialog.
            Reference: reone/dlg.h:130 (NumWords field)
            Reference: reone/dlg.cpp:168 (NumWords parsing)
        
        on_abort: "EndConverAbort" field. Script to run on conversation abort.
            Reference: reone/dlg.h:126 (EndConverAbort field)
            Reference: reone/dlg.cpp:166 (EndConverAbort parsing)
        
        on_end: "EndConversation" field. Script to run when conversation ends.
            Reference: reone/dlg.h:127 (EndConversation field)
            Reference: reone/dlg.cpp:167 (EndConversation parsing)
        
        skippable: "Skippable" field. Whether dialog can be skipped.
            Reference: reone/dlg.h:135 (Skippable field)
            Reference: reone/dlg.cpp:169 (Skippable parsing)
        
        ambient_track: "AmbientTrack" field. Background music track.
            Reference: reone/dlg.h:117 (AmbientTrack field)
            Reference: reone/dlg.cpp:164 (AmbientTrack parsing)
        
        animated_cut: "AnimatedCut" field. Animated cutscene flag.
            Reference: reone/dlg.h:118 (AnimatedCut field)
            Reference: reone/dlg.cpp:165 (AnimatedCut parsing)
        
        camera_model: "CameraModel" field. Camera model ResRef.
            Reference: reone/dlg.h:119 (CameraModel field)
            Reference: reone/dlg.cpp:163 (CameraModel parsing)
        
        computer_type: "ComputerType" field. Type of computer interface.
            Reference: reone/dlg.h:120 (ComputerType field)
            Reference: reone/dlg.cpp:162 (ComputerType parsing)
            Values: 0=Modern, 1=Ancient
        
        conversation_type: "ConversationType" field. Type of conversation.
            Reference: reone/dlg.h:121 (ConversationType field)
            Reference: reone/dlg.cpp:161 (ConversationType parsing)
            Values: 0=Human, 1=Computer, 2=Other
        
        old_hit_check: "OldHitCheck" field. Legacy hit check flag.
            Reference: reone/dlg.h:131 (OldHitCheck field)
            Reference: reone/dlg.cpp:160 (OldHitCheck parsing)
        
        unequip_hands: "UnequipHItem" field. Unequip hand items flag.
            Reference: reone/dlg.h:138 (UnequipHItem field)
            Reference: reone/dlg.cpp:159 (UnequipHItem parsing)
        
        unequip_items: "UnequipItems" field. Unequip all items flag.
            Reference: reone/dlg.h:139 (UnequipItems field)
            Reference: reone/dlg.cpp:158 (UnequipItems parsing)
        
        vo_id: "VO_ID" field. Voice-over identifier string.
            Reference: reone/dlg.h:140 (VO_ID field)
            Reference: reone/dlg.cpp:157 (VO_ID parsing)

        alien_race_owner: "AlienRaceOwner" field. KotOR 2 Only.
            Reference: reone/dlg.h:116 (AlienRaceOwner field)
            Reference: reone/dlg.cpp:155 (AlienRaceOwner parsing)
            Alien race for dialog processing.
        
        post_proc_owner: "PostProcOwner" field. KotOR 2 Only.
            Reference: reone/dlg.h:132 (PostProcOwner field)
            Reference: reone/dlg.cpp:156 (PostProcOwner parsing)
            Post-processing owner ID.
        
        record_no_vo: "RecordNoVO" field. KotOR 2 Only.
            Reference: reone/dlg.h:133 (RecordNoVO field)
            Reference: reone/dlg.cpp:154 (RecordNoVO parsing)
            Flag to record without voice-over.
        
        next_node_id: "NextNodeID" field. KotOR 2 Only.
            Reference: reone/dlg.h:129 (NextNodeID field)
            Reference: reone/dlg.cpp:153 (NextNodeID parsing)
            Next available node ID for new nodes.

        delay_entry: "DelayEntry" field. Not used by the game engine.
            Reference: reone/dlg.h:122 (DelayEntry field, deprecated)
        
        delay_reply: "DelayReply" field. Not used by the game engine.
            Reference: reone/dlg.h:123 (DelayReply field, deprecated)
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
        self.comment: str = ""

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
