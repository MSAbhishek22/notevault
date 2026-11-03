"""Guardrails: the agent only reads its own notes folder, and treats
note text as DATA, never as instructions.

These are local, deterministic checks. They do not call any LLM.
"""
from __future__ import annotations

import re
from pathlib import Path

ALLOWED_SUFFIXES = {".md", ".txt"}
MAX_FILE_BYTES = 200_000

# Heuristic only: a note containing one of these is flagged as untrusted
# input. The agent still answers from it, but wraps it as data and the
# system prompt tells the model to ignore instructions inside notes.
_INSTRUCTION_PATTERNS = (
    r"ignore (all )?(previous|prior|above) instructions",
    r"disregard (all )?(previous|prior|above) instructions",
    r"you are now ",
    r"new system prompt",
    r"override your instructions",
)


def resolve_inside(root: Path, rel: str | Path) -> Path:
    """Resolve `rel` inside `root`, rejecting escapes (.., absolute paths,
    and symlinks that point outside the root). Raises ValueError."""
    root_resolved = root.resolve()
    candidate = (root_resolved / str(rel)).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"Refused path outside notes folder: {rel!r}")
    return candidate


def is_allowed_file(path: Path) -> bool:
    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        return False
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return False
    except OSError:
        return False
    return True


def looks_like_instruction(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in _INSTRUCTION_PATTERNS)


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n…[truncated to budget]"


def log_preview(text: str, limit: int = 80) -> str:
    """A short preview for logs. Never log a full note body."""
    one_line = " ".join(text.split())
    return one_line[:limit]
