"""LLM providers.

Real Otari path (verified 2026-11-02 against the installed `otari`
package, version from PyPI):
    pip install otari
    from otari import OtariClient
    client = OtariClient(platform_token=<OTARI_AI_TOKEN>)
    response = client.completion(
        model="openai:gpt-4o-mini",
        messages=[{"role": "user", "content": "..."}],
    )
    text = response.choices[0].message.content
With no `api_base`, the client defaults to the hosted gateway at
https://api.otari.ai. For a self-hosted gateway, pass
api_base="http://localhost:8000" (origin only, no /api/v1 suffix) and
api_key=<gateway key>; the SDK appends /api/v1 itself.

The model string is passed to the SDK exactly as configured — the
``provider:model`` form (``openai:gpt-4o-mini``) and the dashboard
``vendor/model`` form (``mistralai/mistral-small-latest``) are both
valid; nothing in this module rewrites the string. Only
``routing.parse_model`` splits it, for display and validation.

Mock path: deterministic, offline, no network. Used when no token is
configured, so the demo and tests always run. Mock output is always
prefixed "[mock]" so it can never be mistaken for a real Otari answer.
"""
from __future__ import annotations

import re
from typing import Any, Protocol

from .config import Config


class LLMProvider(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class MockProvider:
    """Deterministic extractive stand-in. Tracks calls for tests."""

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        # Answer from the note data, not from the question preamble: take
        # the text after the <notes-data>/<note-data> marker, if present.
        body = user
        for marker in ("<notes-data>", "<note-data"):
            if marker in user:
                body = user.split(marker, 1)[1]
                # Strip a possible <note-data title=...> opening tag remainder.
                body = re.sub(r"^[^>]*>", "", body, count=1) if marker == "<note-data" else body
                break
        body = re.sub(r"^---.*$", "", body, flags=re.M).strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
        content = next((s for s in sentences if len(s) > 20), sentences[0] if sentences else "")
        return f"[mock] {content}"


def _extract_content(response: Any) -> str:
    """Handle both the typed Otari response object and plain dicts."""
    try:
        choice = response.choices[0]
        message = choice.message
        content = message.content if not isinstance(message, dict) else message.get("content")
        if content:
            return str(content)
    except (AttributeError, IndexError, KeyError, TypeError):
        pass
    if isinstance(response, dict):
        try:
            return str(response["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError):
            pass
    raise RuntimeError("Otari returned an empty or unrecognised response")


class OtariProvider:
    """Thin wrapper over the real `otari` SDK. No network in __init__.

    Pass `client=` in tests to inject a fake client; production code
    passes nothing and the real SDK is constructed from env config.
    """

    def __init__(
        self,
        model: str,
        client: Any = None,
        token: str | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        if client is not None:
            self._client = client
            return
        if not token and not (api_base and api_key):
            raise RuntimeError(
                "No Otari credentials: set OTARI_AI_TOKEN (hosted otari.ai) "
                "or GATEWAY_API_BASE + GATEWAY_API_KEY (self-hosted), "
                "or run with --provider mock."
            )
        try:
            from otari import OtariClient
        except ImportError as exc:
            raise RuntimeError(
                "The `otari` package is not installed. Run: pip install otari"
            ) from exc
        if api_base:
            self._client = OtariClient(api_base=api_base, api_key=api_key)
        else:
            self._client = OtariClient(platform_token=token)

    def complete(self, system: str, user: str) -> str:
        response = self._client.completion(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return _extract_content(response)


def build_provider(config: Config, client: Any = None) -> LLMProvider:
    """Resolve provider from config. 'auto' -> otari if credentials exist,
    otherwise mock. Explicit 'otari' with no credentials raises."""
    effective = config.resolve_provider()
    if effective == "mock":
        return MockProvider()
    if effective == "otari":
        return OtariProvider(
            model=config.model,
            client=client,
            token=config.otari_token,
            api_base=config.gateway_api_base,
            api_key=config.gateway_api_key,
        )
    raise ValueError(f"Unknown provider: {config.provider!r}")
