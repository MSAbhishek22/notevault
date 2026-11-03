"""Configuration for the NoteVault agent.

No secrets are ever read from a file committed to the repo. Tokens come
only from the environment, and are never printed or logged.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    notes_root: Path
    provider: str = "auto"  # "auto" | "mock" | "otari"
    model: str = "openai:gpt-4o-mini"
    max_chars_per_note: int = 4000
    max_notes_per_answer: int = 3
    max_llm_calls_per_run: int = 5
    fallback_model: str | None = None
    otari_token: str | None = None
    gateway_api_base: str | None = None
    gateway_api_key: str | None = None

    @property
    def gateway_label(self) -> str:
        """Gateway origin for display only — never a token or key."""
        return self.gateway_api_base or "https://api.otari.ai"

    def resolve_provider(self) -> str:
        """Return the effective provider name, without side effects."""
        if self.provider == "auto":
            if self.otari_token or (self.gateway_api_base and self.gateway_api_key):
                return "otari"
            return "mock"
        return self.provider


def config_from_env(notes_root: Path | None = None) -> Config:
    """Build a Config from the environment. Never prints token values."""
    token = os.environ.get("OTARI_AI_TOKEN") or os.environ.get(
        "GATEWAY_PLATFORM_TOKEN"
    )
    return Config(
        notes_root=Path(notes_root or os.environ.get("NOTES_ROOT", "notes")),
        provider=os.environ.get("OTARI_PROVIDER", "auto"),
        model=os.environ.get("OTARI_MODEL", "openai:gpt-4o-mini"),
        fallback_model=os.environ.get("OTARI_FALLBACK_MODEL") or None,
        otari_token=token,
        gateway_api_base=os.environ.get("GATEWAY_API_BASE"),
        gateway_api_key=os.environ.get("GATEWAY_API_KEY"),
    )
