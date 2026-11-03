"""Local note indexing and keyword search. Stdlib only, no LLM calls."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .guardrails import is_allowed_file

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_TAG_RE = re.compile(r"(?:^|\s)#([A-Za-z0-9_-]+)")
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "what", "who", "how",
    "why", "when", "where", "for", "of", "to", "in", "on", "and", "or",
    "do", "does", "did", "can", "could", "tell", "me", "about",
}


@dataclass
class Note:
    rel_path: str
    title: str
    tags: list[str]
    body: str

    @property
    def word_count(self) -> int:
        return len(self.body.split())


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def parse_note(rel_path: str, text: str) -> Note:
    title = rel_path
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break
    tags: list[str] = []
    for tag in _TAG_RE.findall(text):
        if tag not in tags:
            tags.append(tag)
    return Note(rel_path=rel_path, title=title, tags=tags, body=text)


def index_notes(root: Path) -> list[Note]:
    """Walk `root` (sorted, deterministic) and parse allowed files."""
    if not root.is_dir():
        return []
    notes: list[Note] = []
    root_resolved = root.resolve()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not is_allowed_file(path):
            continue
        try:
            rel = path.resolve().relative_to(root_resolved)
        except ValueError:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        notes.append(parse_note(str(rel), text))
    return notes


def search_notes(notes: list[Note], query: str, limit: int = 5) -> list[Note]:
    """Keyword search: title hits weigh 3, tag hits 3, body hits 1."""
    query_tokens = set(tokenize(query)) - STOPWORDS
    if not query_tokens:
        return []
    scored: list[tuple[int, Note]] = []
    for note in notes:
        title_tokens = set(tokenize(note.title))
        body_tokens = set(tokenize(note.body))
        tag_tokens = {t.lower() for t in note.tags}
        score = (
            3 * len(query_tokens & title_tokens)
            + 3 * len(query_tokens & tag_tokens)
            + 1 * len(query_tokens & body_tokens)
        )
        if score > 0:
            scored.append((score, note))
    scored.sort(key=lambda pair: (-pair[0], pair[1].rel_path))
    return [note for _, note in scored[:limit]]
