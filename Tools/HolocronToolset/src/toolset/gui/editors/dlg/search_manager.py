from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Callable, Generator

from loggerplus import RobustLogger

from pykotor.resource.generics.dlg import DLGEntry

if TYPE_CHECKING:
    from pykotor.common.language import LocalizedString
    from pykotor.resource.generics.dlg.links import DLGLink
    from pykotor.resource.generics.dlg.nodes import DLGNode


class SearchCategory(Enum):
    """Categories for searching dialogue content."""

    TEXT = auto()  # Node text content
    SCRIPT = auto()  # Script content
    CONDITION = auto()  # Link conditions
    SPEAKER = auto()  # Entry speaker
    LISTENER = auto()  # Node listener
    SOUND = auto()  # Sound/voice content
    ANIMATION = auto()  # Animation content
    CAMERA = auto()  # Camera settings
    QUEST = auto()  # Quest-related content
    ALL = auto()  # Search all categories


@dataclass
class SearchResult:
    """Represents a search result with context."""

    node: DLGNode  # The node containing the match
    link: DLGLink | None  # The link containing the match, if applicable
    category: SearchCategory  # Category the match was found in
    match_text: str  # The matching text
    context: str  # Additional context about the match
    score: float = 1.0  # Relevance score


class SearchManager:
    """Manages advanced search functionality for the dialogue editor."""

    def __init__(self):
        self.recent_searches: list[str] = []
        self.search_filters: dict[SearchCategory, bool] = {cat: True for cat in SearchCategory}
        self.custom_filters: dict[str, Callable[[DLGNode], bool]] = {}
        self.indexed_nodes: set[DLGNode] = set()
        self.max_recent_searches: int = 10

    def _iter_nodes_and_links(
        self,
    ) -> Generator[tuple[DLGNode, DLGLink | None], None, None]:
        """Iterate through all indexed nodes and their links."""
        seen_nodes: set[DLGNode] = set()
        for node in self.indexed_nodes:
            if node in seen_nodes:
                continue
            seen_nodes.add(node)
            yield node, None  # Yield the node itself

            # Yield each link and its target node
            for link in node.links:
                if link.node in seen_nodes:
                    continue
                seen_nodes.add(link.node)
                yield link.node, link

    def search(
        self,
        query: str,
        categories: list[SearchCategory] | None = None,
        max_results: int = 100,
    ) -> list[SearchResult]:
        """Search for nodes and links matching the query.

        Args:
        ----
            query: Search string
            categories: Categories to search in, defaults to all enabled categories
            max_results: Maximum number of results to return

        Returns:
        -------
            List of search results sorted by relevance
        """
        if not query:
            return []

        try:
            # Add to recent searches
            if query not in self.recent_searches:
                self.recent_searches.insert(0, query)
                if len(self.recent_searches) > self.max_recent_searches:
                    self.recent_searches.pop()

            results: list[SearchResult] = []
            search_cats: list[SearchCategory] = categories or [cat for cat, enabled in self.search_filters.items() if enabled]
            query_lower: str = query.lower()

            for node, link in self._iter_nodes_and_links():
                for category in search_cats:
                    if category == SearchCategory.ALL:
                        continue

                    result: SearchResult | None = self._search_node_and_link(node, link, query_lower, category)
                    if result is None:
                        continue
                    results.append(result)

            # Sort by score and limit results
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:max_results]

        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error performing search for query: {query!r}")
            return []

    def _search_node_and_link(  # noqa: C901, PLR0911, PLR0912
        self,
        node: DLGNode,
        link: DLGLink | None,
        query: str,
        category: SearchCategory,
    ) -> SearchResult | None:
        """Search a node and its associated link in a specific category."""
        try:
            if category == SearchCategory.TEXT:
                text: LocalizedString = node.text
                text_str: str = str(text).lower()
                if query not in text_str:
                    return None
                return SearchResult(
                    node=node,
                    link=link,
                    category=category,
                    match_text=str(text),
                    context=f"Text match: {text_str[:50]}...",
                    score=1.0 if query == text_str else 0.8,
                )

            if category == SearchCategory.SCRIPT:
                scripts: list[str] = [str(node.script1), str(node.script2)]
                for script in scripts:
                    script_lower: str = script.lower()
                    if query not in script_lower:
                        continue
                    return SearchResult(
                        node=node,
                        link=link,
                        category=category,
                        match_text=script,
                        context=f"Script match: {script[:50]}...",
                        score=0.7,
                    )

            elif category == SearchCategory.CONDITION and link is not None:
                conditions: list[str] = [
                    str(link.active1),
                    str(link.active2),
                ]
                for condition in conditions:
                    condition_lower: str = condition.lower()
                    if query not in condition_lower:
                        continue
                    return SearchResult(
                        node=node,
                        link=link,
                        category=category,
                        match_text=condition,
                        context=f"Condition match: {condition[:50]}...",
                        score=0.6,
                    )

            elif category == SearchCategory.SPEAKER and isinstance(node, DLGEntry):
                speaker_lower: str = node.speaker.lower()
                if query not in speaker_lower:
                    return None
                return SearchResult(
                    node=node,
                    link=link,
                    category=category,
                    match_text=node.speaker,
                    context=f"Speaker match: {node.speaker}",
                    score=0.9,
                )

            elif category == SearchCategory.LISTENER:
                listener_lower: str = node.listener.lower()
                if query not in listener_lower:
                    return None
                return SearchResult(
                    node=node,
                    link=link,
                    category=category,
                    match_text=node.listener,
                    context=f"Listener match: {node.listener}",
                    score=0.9,
                )

            elif category == SearchCategory.SOUND:
                sound_str: str = str(node.sound).lower()
                vo_str: str = str(node.vo_resref).lower()
                if query not in sound_str:
                    return None
                return SearchResult(
                    node=node,
                    link=link,
                    category=category,
                    match_text=str(node.sound),
                    context="Sound match",
                    score=0.5,
                )
                if query not in vo_str:
                    return None
                return SearchResult(
                    node=node,
                    link=link,
                    category=category,
                    match_text=str(node.vo_resref),
                    context="Voice-over match",
                    score=0.5,
                )

            elif category == SearchCategory.QUEST:
                quest_lower: str = node.quest.lower()
                if query not in quest_lower:
                    return None
                return SearchResult(
                    node=node,
                    link=link,
                    category=category,
                    match_text=node.quest,
                    context=f"Quest match: {node.quest}",
                    score=0.8,
                )

        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error searching node {node!r} in category {category!r}")

        return None

    def add_custom_filter(
        self,
        name: str,
        filter_func: Callable[[DLGNode], bool],
    ) -> None:
        """Add a custom search filter."""
        self.custom_filters[name] = filter_func

    def remove_custom_filter(
        self,
        name: str,
    ) -> None:
        """Remove a custom search filter."""
        self.custom_filters.pop(name, None)

    def apply_custom_filters(
        self,
        results: list[SearchResult],
    ) -> list[SearchResult]:
        """Apply custom filters to search results."""
        filtered: list[SearchResult] = results[:]
        for filter_func in self.custom_filters.values():
            filtered = [r for r in filtered if filter_func(r.node)]
        return filtered

    def index_node(
        self,
        node: DLGNode,
    ) -> None:
        """Add a node to the search index."""
        self.indexed_nodes.add(node)

    def remove_from_index(
        self,
        node: DLGNode,
    ) -> None:
        """Remove a node from the search index."""
        self.indexed_nodes.discard(node)

    def clear_index(self) -> None:
        """Clear the entire search index."""
        self.indexed_nodes.clear()

    def get_recent_searches(self) -> list[str]:
        """Get list of recent searches."""
        return self.recent_searches[:]

    def clear_recent_searches(self) -> None:
        """Clear the recent searches list."""
        self.recent_searches.clear()

    def set_filter_enabled(
        self,
        category: SearchCategory,
        *,
        enabled: bool,
    ) -> None:
        """Enable or disable a search category filter."""
        self.search_filters[category] = enabled

    def get_filter_enabled(
        self,
        category: SearchCategory,
    ) -> bool:
        """Check if a search category filter is enabled."""
        return self.search_filters.get(category, True)
