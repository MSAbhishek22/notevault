"""Tests: agent behaviour, mock provider, Otari provider wiring. No network."""
from pathlib import Path

import pytest

from notes_agent.agent import NotesAgent
from notes_agent.config import Config
from notes_agent.llm import MockProvider, OtariProvider, build_provider


class FakeChoiceMessage:
    def __init__(self, content):
        self.content = content


class FakeChoice:
    def __init__(self, content):
        self.message = FakeChoiceMessage(content)


class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoice(content)]


class FakeOtariClient:
    def __init__(self):
        self.calls = []

    def completion(self, model, messages):
        self.calls.append((model, messages))
        return FakeResponse("Fake Otari answer.")


def _config(tmp_path, **overrides):
    kwargs = dict(notes_root=tmp_path, provider="mock")
    kwargs.update(overrides)
    return Config(**kwargs)


def _seed(tmp_path):
    (tmp_path / "a.md").write_text("# Abhiverse idea\nPhone remote for laptop. #project", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Study\nLists keep order. #study", encoding="utf-8")


def test_ask_no_match_does_not_guess_and_does_not_call_llm(tmp_path):
    _seed(tmp_path)
    mock = MockProvider()
    agent = NotesAgent(_config(tmp_path), provider=mock)
    answer = agent.ask("quantum bananas")
    assert "couldn't find" in answer
    assert mock.calls == 0


def test_ask_with_match_cites_source(tmp_path):
    _seed(tmp_path)
    mock = MockProvider()
    agent = NotesAgent(_config(tmp_path), provider=mock)
    answer = agent.ask("What is Abhiverse?")
    assert "Abhiverse idea" in answer
    assert mock.calls == 1


def test_summarise_uses_mock_prefix(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    assert agent.summarise("a.md").startswith("[mock]")


def test_organise_plan_never_moves_files(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    plan = agent.organise_plan()
    assert "#project" in plan and "a.md" in plan
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.md", "b.md"]


def test_otari_provider_uses_injected_client(tmp_path):
    fake = FakeOtariClient()
    provider = OtariProvider(model="openai:gpt-4o-mini", client=fake)
    assert provider.complete("sys", "hello") == "Fake Otari answer."
    assert fake.calls[0][0] == "openai:gpt-4o-mini"
    assert fake.calls[0][1][0] == {"role": "system", "content": "sys"}


def test_otari_provider_without_credentials_raises_before_network():
    with pytest.raises(RuntimeError, match="No Otari credentials"):
        OtariProvider(model="openai:gpt-4o-mini")


def test_build_provider_auto_no_token_is_mock():
    assert isinstance(build_provider(Config(notes_root=Path("."), provider="auto")), MockProvider)


def test_llm_budget_is_enforced(tmp_path):
    _seed(tmp_path)
    config = _config(tmp_path, max_llm_calls_per_run=1)
    agent = NotesAgent(config, provider=MockProvider())
    agent.ask("Abhiverse")
    with pytest.raises(RuntimeError, match="budget"):
        agent.ask("Abhiverse")
