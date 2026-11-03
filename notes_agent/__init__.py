"""NoteVault: a local-first notes agent that talks to LLMs via Otari."""
from .agent import NotesAgent
from .config import Config, config_from_env

__all__ = ["NotesAgent", "Config", "config_from_env"]
