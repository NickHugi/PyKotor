from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, TypeVar

from loggerplus import RobustLogger

from pykotor.resource.generics.dlg.nodes import DLGNode

if TYPE_CHECKING:
    from pykotor.common.language import LocalizedString
    from pykotor.resource.generics.dlg.links import DLGLink


class StateChangeType(Enum):
    """Types of state changes that can occur."""

    VARIABLE = auto()  # Variable value changed
    NODE_VISITED = auto()  # Node was visited
    LINK_TAKEN = auto()  # Link was traversed
    SCRIPT_EXECUTED = auto()  # Script was run
    CONDITION_EVALUATED = auto()  # Condition was checked


T = TypeVar("T", bound=DLGNode)
U = TypeVar("U")


@dataclass
class StateChange:
    """Represents a change in the dialogue state."""

    change_type: StateChangeType
    target_id: str  # ID of changed element (variable name, node hash, etc)
    old_value: Any  # Previous value
    new_value: Any  # New value
    timestamp: float  # When the change occurred


@dataclass
class DialogueState:
    """Current state of a dialogue execution."""

    variables: dict[str, Any] = field(default_factory=dict)
    visited_nodes: set[DLGNode] = field(default_factory=set)
    taken_links: set[DLGLink] = field(default_factory=set)
    current_node: DLGNode | None = None
    current_link: DLGLink | None = None
    history: list[StateChange] = field(default_factory=list)


class StateManager:
    """Manages the state of dialogue execution and variable tracking."""

    def __init__(self):
        self.state: DialogueState = DialogueState()
        self.state_stack: list[DialogueState] = []  # For state backtracking
        self.max_history: int = 1000  # Maximum number of state changes to track

    def push_state(self) -> None:
        """Push current state onto stack for backtracking."""
        import copy

        self.state_stack.append(copy.deepcopy(self.state))

    def pop_state(self) -> None:
        """Restore previous state from stack."""
        if not self.state_stack:
            raise RuntimeError("No state stack to pop from")
        self.state = self.state_stack.pop()

    def clear_state(self) -> None:
        """Reset state to initial values."""
        self.state = DialogueState()
        self.state_stack.clear()

    def set_variable(
        self,
        name: str,
        value: Any,
    ) -> None:
        """Set a variable's value in the current state."""
        try:
            old_value: Any | None = self.state.variables.get(name)
            self.state.variables[name] = value
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error setting variable {name!r} to {value!r}")
        else:
            self._record_change(StateChangeType.VARIABLE, name, old_value, value)

    def get_variable(
        self,
        name: str,
        default: U = None,
    ) -> Any | U:
        """Get a variable's value from the current state."""
        return self.state.variables.get(name, default)

    def visit_node(
        self,
        node: DLGNode,
    ) -> None:
        """Mark a node as visited and update current node."""
        try:
            old_node: DLGNode | None = self.state.current_node
            self.state.current_node = node
            self.state.visited_nodes.add(node)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error visiting node {node!r}")
        else:
            self._record_change(StateChangeType.NODE_VISITED, str(hash(node)), old_node, node)

    def take_link(
        self,
        link: DLGLink[T],
    ) -> T:
        """Mark a link as taken and update current link."""
        try:
            old_link: DLGLink[T] | None = self.state.current_link
            self.state.current_link = link
            self.state.taken_links.add(link)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error taking link {link!r}")
        else:
            self._record_change(StateChangeType.LINK_TAKEN, str(hash(link)), old_link, link)

        return link.node

    def evaluate_link_conditions(
        self,
        link: DLGLink,
    ) -> bool:
        """Evaluate if a link's conditions are met in current state."""
        try:
            # For now just track that evaluation occurred
            # Actual condition evaluation would be handled by game engine
            self._record_change(StateChangeType.CONDITION_EVALUATED, str(hash(link)), None, None)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error evaluating conditions for link {link!r}")
            return False
        else:
            return True

    def execute_node_scripts(
        self,
        node: DLGNode,
    ) -> None:
        """Execute a node's scripts in the current state.

        In reality all this needs to do is open the NSSEditor in a new window for
        that script.
        """
        try:
            # For now just track that scripts were executed
            # Actual script execution would be handled by game engine
            self._record_change(StateChangeType.SCRIPT_EXECUTED, str(hash(node)), None, None)
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error executing scripts for node {node!r}")

    def is_node_visited(
        self,
        node: DLGNode,
    ) -> bool:
        """Check if a node has been visited."""
        return node in self.state.visited_nodes

    def is_link_taken(
        self,
        link: DLGLink,
    ) -> bool:
        """Check if a link has been taken."""
        return link in self.state.taken_links

    def get_available_links(
        self,
        node: DLGNode,
    ) -> list[DLGLink]:
        """Get available links from a node based on current state."""
        try:
            return [link for link in node.links if self.evaluate_link_conditions(link)]
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error getting available links for node {node!r}")
            return []

    def get_node_text(
        self,
        node: DLGNode,
    ) -> LocalizedString:
        """Get a node's text, considering any state-based text variations."""
        try:
            # For now just return the node's text
            # Could be extended to handle conditional text variations
            return node.text
        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error getting text for node {node!r}")
            return node.text

    def _record_change(
        self,
        change_type: StateChangeType,
        target_id: str,
        old_value: Any,
        new_value: Any,
    ) -> None:
        """Record a state change in the history."""
        import time

        try:
            change = StateChange(
                change_type=change_type,
                target_id=target_id,
                old_value=old_value,
                new_value=new_value,
                timestamp=time.time(),
            )

            self.state.history.append(change)

            # Trim history if needed
            if len(self.state.history) > self.max_history:
                self.state.history = self.state.history[-self.max_history :]

        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error recording state change: type={change_type!r}, " f"target={target_id!r}, old={old_value!r}, new={new_value!r}")
