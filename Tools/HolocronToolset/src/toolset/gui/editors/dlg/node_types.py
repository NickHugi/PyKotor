from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, ClassVar

from loggerplus import RobustLogger

if TYPE_CHECKING:
    from pykotor.resource.generics.dlg.links import DLGLink
    from pykotor.resource.generics.dlg.nodes import DLGNode


class NodeCategory(Enum):
    """Categories of dialogue nodes."""

    ENTRY = auto()  # NPC dialogue line
    REPLY = auto()  # Player response
    STARTER = auto()  # Entry point node


class NodeStyle(Enum):
    """Visual styles for nodes."""

    DEFAULT = auto()  # Standard node appearance
    HIGHLIGHTED = auto()  # Currently selected/focused
    DISABLED = auto()  # Conditions not met
    ERROR = auto()  # Invalid state
    WARNING = auto()  # Potential issues
    SUCCESS = auto()  # Conditions met/valid


@dataclass
class NodeValidationRule:
    """Rule for validating node connections."""

    source_category: NodeCategory  # Category of source node
    target_category: NodeCategory  # Category of target node
    error_message: str  # Message if validation fails
    is_required: bool = False  # Whether connection is required


@dataclass
class NodeTypeInfo:
    """Metadata about a node type."""

    category: NodeCategory  # Node category
    display_name: str  # Human-readable name
    description: str  # Detailed description
    can_have_children: bool  # Whether node can have child nodes
    can_have_parent: bool  # Whether node can have parent nodes
    max_children: int | None = None  # Maximum number of child nodes (None for unlimited)
    min_children: int = 0  # Minimum number of child nodes
    validation_rules: list[NodeValidationRule] = field(default_factory=list)  # Rules for valid connections


class NodeTypes:
    """Registry of available node types and validation rules."""

    # Default validation rules
    DEFAULT_RULES: ClassVar[list[NodeValidationRule]] = [
        # Entry nodes can only connect to Reply nodes
        NodeValidationRule(
            source_category=NodeCategory.ENTRY,
            target_category=NodeCategory.REPLY,
            error_message="Entry nodes can only connect to Reply nodes",
        ),
        # Reply nodes can only connect to Entry nodes
        NodeValidationRule(
            source_category=NodeCategory.REPLY,
            target_category=NodeCategory.ENTRY,
            error_message="Reply nodes can only connect to Entry nodes",
        ),
        # Starter nodes must connect to Entry nodes
        NodeValidationRule(
            source_category=NodeCategory.STARTER,
            target_category=NodeCategory.ENTRY,
            error_message="Starter nodes must connect to Entry nodes",
            is_required=True,
        ),
    ]

    # Node type definitions
    TYPES: ClassVar[dict[NodeCategory, NodeTypeInfo]] = {
        NodeCategory.ENTRY: NodeTypeInfo(
            category=NodeCategory.ENTRY,
            display_name="Entry",
            description="NPC dialogue line",
            can_have_children=True,
            can_have_parent=True,
            validation_rules=[
                NodeValidationRule(
                    source_category=NodeCategory.ENTRY,
                    target_category=NodeCategory.REPLY,
                    error_message="Entry nodes can only connect to Reply nodes",
                ),
            ],
        ),
        NodeCategory.REPLY: NodeTypeInfo(
            category=NodeCategory.REPLY,
            display_name="Reply",
            description="Player response option",
            can_have_children=True,
            can_have_parent=True,
            validation_rules=[
                NodeValidationRule(
                    source_category=NodeCategory.REPLY,
                    target_category=NodeCategory.ENTRY,
                    error_message="Reply nodes can only connect to Entry nodes",
                ),
            ],
        ),
        NodeCategory.STARTER: NodeTypeInfo(
            category=NodeCategory.STARTER,
            display_name="Start",
            description="Dialogue entry point",
            can_have_children=True,
            can_have_parent=False,
            max_children=1,
            validation_rules=[
                NodeValidationRule(
                    source_category=NodeCategory.STARTER,
                    target_category=NodeCategory.ENTRY,
                    error_message="Starter nodes must connect to Entry nodes",
                    is_required=True,
                ),
            ],
        ),
    }

    @classmethod
    def get_type_info(
        cls,
        category: NodeCategory,
    ) -> NodeTypeInfo:
        """Get type information for a node category."""
        return cls.TYPES[category]

    @classmethod
    def validate_connection(
        cls,
        source_node: DLGNode,
        target_node: DLGNode,
    ) -> tuple[bool, str]:
        """Validate a connection between two nodes.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            source_category: NodeCategory = cls.get_node_category(source_node)
            target_category: NodeCategory = cls.get_node_category(target_node)

            # Check source node's validation rules
            source_info: NodeTypeInfo = cls.get_type_info(source_category)
            for rule in source_info.validation_rules:
                if rule.source_category == source_category and rule.target_category != target_category:
                    return False, rule.error_message

            # Check target node's validation rules
            target_info: NodeTypeInfo = cls.get_type_info(target_category)
            if not target_info.can_have_parent:
                return False, f"{target_info.display_name} nodes cannot have parent nodes"

            # Check child count limits
            if source_info.max_children is not None:
                child_count: int = len(source_node.links)
                if child_count >= source_info.max_children:
                    return False, f"{source_info.display_name} nodes cannot have more than {source_info.max_children} children"

        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error validating connection between {source_node!r} and {target_node!r}")
            return False, "Error validating connection"
        else:
            return True, ""

    @classmethod
    def validate_node(
        cls,
        node: DLGNode,
    ) -> tuple[bool, list[str]]:
        """Validate a node's current state.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        try:
            errors: list[str] = []
            category: NodeCategory = cls.get_node_category(node)
            type_info: NodeTypeInfo = cls.get_type_info(category)

            # Check minimum children requirement
            if len(node.links) < type_info.min_children:
                errors.append(f"{type_info.display_name} nodes must have at least {type_info.min_children} children")

            # Check maximum children limit
            if type_info.max_children is not None and len(node.links) > type_info.max_children:
                errors.append(f"{type_info.display_name} nodes cannot have more than {type_info.max_children} children")

            # Check required connection rules
            for rule in type_info.validation_rules:
                if rule.is_required:
                    has_required: bool = any(cls.get_node_category(link.node) == rule.target_category for link in node.links)
                    if not has_required:
                        errors.append(rule.error_message)

        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error validating node {node!r}")
            return False, ["Error validating node"]

        else:
            return not errors, errors

    @classmethod
    def get_node_category(
        cls,
        node: DLGNode,
    ) -> NodeCategory:
        """Determine the category of a node."""
        from pykotor.resource.generics.dlg import DLGEntry, DLGReply

        if isinstance(node, DLGEntry):
            return NodeCategory.ENTRY
        if isinstance(node, DLGReply):
            return NodeCategory.REPLY
        raise ValueError(f"Unknown node type: {type(node)}")

    @classmethod
    def get_node_style(
        cls,
        node: DLGNode,
        link: DLGLink | None = None,
    ) -> NodeStyle:
        """Get the visual style for a node."""
        try:
            # Validate node
            is_valid, errors = cls.validate_node(node)
            if not is_valid:
                return NodeStyle.ERROR

            # Check if node has any links
            if not node.links and cls.get_type_info(cls.get_node_category(node)).min_children > 0:
                return NodeStyle.WARNING

            # If link provided, check its conditions
            if link is not None and (link.active1 or link.active2):
                return NodeStyle.DISABLED

        except Exception:  # noqa: BLE001
            RobustLogger().exception(f"Error getting style for node {node!r}")
            return NodeStyle.ERROR
        else:
            return NodeStyle.DEFAULT
