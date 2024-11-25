"""HolocronAI - Character AI system using DITTO self-alignment and Beyond Dialog concepts."""

from holocron_ai.core.beyond_dialog import BeyondDialogProcessor
from holocron_ai.core.character_agent import CharacterAgent
from holocron_ai.core.dialog_processor import DialogProcessor
from holocron_ai.core.ditto_framework import DITTOFramework
from holocron_ai.core.self_alignment import SelfAlignmentProcessor

__version__ = "0.1.0"

__all__ = [
    "BeyondDialogProcessor",
    "CharacterAgent",
    "DITTOFramework",
    "DialogProcessor",
    "SelfAlignmentProcessor",
]
