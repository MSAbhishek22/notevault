"""Tests: Otari routing display, budget meter, fallback, web payloads. No network."""
import json
import threading
import urllib.request

import pytest

from notes_agent.agent import NotesAgent
from notes_agent.config import Config
from notes_agent.llm import MockProvider
from notes_agent.routing import BudgetTracker, choose_route, parse_model
from notes_agent.web import make_server


class FailingProvider:
    def complete(self, system, user):
        raise RuntimeError("primary provider down")


def _config(tmp_path, **overrides):
    kwargs = dict(notes_root=tmp_path, provider="mock")
    kwargs.update(overrides)
    return Config(**kwargs)


def _seed(tmp_path):
    (tmp_path / "a.md").write_text("# Abhiverse idea\nPhone remote for laptop. #project", encoding="utf-8")


def test_parse_model_valid_and_invalid():
    assert parse_model("openai:gpt-4o-mini") == ("openai", "gpt-4o-mini")
    # Colon form with a slash-form model name is unchanged.
    assert parse_model("mistral:mistral-small-latest") == ("mistral", "mistral-small-latest")
    # Otari dashboard IDs use the vendor/model slash form: split on the
    # first slash for the provider, keep the full ID as the model name.
    assert parse_model("mistralai/mistral-small-latest") == ("mistralai", "mistral-small-latest")
    assert parse_model("together-ai/meta-llama/Llama-3-8b") == ("together-ai", "meta-llama/Llama-3-8b")
    for bad in ("", "gpt-4o-mini", "openai:", ":gpt-4o-mini", "mistralai/", "/mistral-small-latest", "mistralai"):
        with pytest.raises(ValueError, match="provider:model"):
            parse_model(bad)


def test_choose_route_slash_form_keeps_full_id():
    route = choose_route("mistralai/mistral-small-latest", gateway="https://api.otari.ai", mode="mock")
    assert route.chosen.provider == "mistralai"
    assert route.chosen.model == "mistralai/mistral-small-latest"
    assert route.to_dict()["chosen"] == {
        "provider": "mistralai",
        "model": "mistralai/mistral-small-latest",
        "reason": route.chosen.reason,
    }


def test_choose_route_default_and_user_selected_reasons():
    default = choose_route("openai:gpt-4o-mini", gateway="https://api.otari.ai", mode="mock")
    assert default.chosen.provider == "openai"
    assert "Default model" in default.chosen.reason
    assert default.fallback_chain == []
    chosen = choose_route(
        "openai:gpt-4o-mini", fallback_model="anthropic:claude-test",
        user_selected=True, mode="mock",
    )
    assert "User-selected" in chosen.chosen.reason
    assert chosen.fallback_chain[0].model == "anthropic:claude-test"
    d = chosen.to_dict()
    assert d["gateway"] == "https://api.otari.ai"
    assert "[mock]" in d["mode_label"]


def test_budget_tracker_remaining_and_exhaustion():
    b = BudgetTracker(limit=2)
    assert b.remaining == 2 and not b.exhausted
    b.charge()
    assert (b.used, b.remaining, b.percent_used) == (1, 1, 50)
    b.charge()
    assert b.exhausted
    with pytest.raises(RuntimeError, match="budget"):
        b.charge()


def test_ask_detailed_shows_routing_budget_citations_and_mock_label(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    result = agent.ask_detailed("What is Abhiverse?")
    assert result.mode == "mock"
    assert result.sources == [{"title": "Abhiverse idea", "rel_path": "a.md"}]
    assert result.routing["gateway"] == "https://api.otari.ai"
    assert result.routing["chosen"]["model"] == "mistralai/mistral-small-latest"
    assert result.routing["attempted"] == ["mistralai/mistral-small-latest"]
    assert result.routing["fallback_used"] is False
    assert result.budget["used"] == 1 and result.budget["remaining"] == 4
    assert "[mock]" in result.answer  # mock answers are always labelled


def test_ask_detailed_refusal_spends_no_budget_and_attempts_no_route(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    result = agent.ask_detailed("quantum bananas")
    assert result.refused is True
    assert result.routing["refused_before_routing"] is True
    assert result.routing["attempted"] == []
    assert result.budget["used"] == 0


def test_fallback_used_when_primary_fails(tmp_path):
    _seed(tmp_path)
    config = _config(tmp_path, fallback_model="anthropic:claude-test")
    agent = NotesAgent(config, provider=FailingProvider(), fallback_provider=MockProvider())
    result = agent.ask_detailed("Abhiverse")
    assert result.routing["fallback_used"] is True
    assert result.routing["attempted"] == ["mistralai/mistral-small-latest", "anthropic:claude-test"]
    assert result.budget["used"] == 2  # one charge per provider attempt
    assert "[mock]" in result.answer


def test_both_providers_failing_raises_no_fabricated_answer(tmp_path):
    _seed(tmp_path)
    config = _config(tmp_path, fallback_model="anthropic:claude-test")
    agent = NotesAgent(config, provider=FailingProvider(), fallback_provider=FailingProvider())
    with pytest.raises(RuntimeError, match="primary provider down"):
        agent.ask_detailed("Abhiverse")


def test_user_selected_model_is_recorded_in_routing(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    result = agent.ask_detailed("Abhiverse", model="openai:gpt-4o-mini")
    assert result.routing["chosen"]["model"] == "openai:gpt-4o-mini"
    assert "User-selected" in result.routing["chosen"]["reason"]


def test_bad_user_model_rejected_before_llm_call(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    with pytest.raises(ValueError, match="provider:model"):
        agent.ask_detailed("Abhiverse", model="not-a-model-string")
    assert agent.budget.used == 0


def test_slash_model_from_config_routes_with_full_id(tmp_path):
    _seed(tmp_path)
    config = _config(tmp_path, model="mistralai/mistral-small-latest")
    agent = NotesAgent(config, provider=MockProvider())
    result = agent.ask_detailed("What is Abhiverse?")
    assert result.routing["chosen"]["provider"] == "mistralai"
    assert result.routing["chosen"]["model"] == "mistralai/mistral-small-latest"
    assert result.routing["attempted"] == ["mistralai/mistral-small-latest"]
    assert "[mock]" in result.answer


def test_user_selected_slash_model_is_recorded_and_used(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    result = agent.ask_detailed("Abhiverse", model="mistralai/mistral-small-latest")
    assert result.routing["chosen"]["provider"] == "mistralai"
    assert result.routing["chosen"]["model"] == "mistralai/mistral-small-latest"
    assert "User-selected" in result.routing["chosen"]["reason"]


def test_bad_slash_user_model_rejected_before_llm_call(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    with pytest.raises(ValueError, match="provider:model"):
        agent.ask_detailed("Abhiverse", model="mistralai/")
    assert agent.budget.used == 0


def test_status_dict_never_contains_token(tmp_path):
    _seed(tmp_path)
    config = _config(tmp_path, otari_token="secret-should-not-appear")
    agent = NotesAgent(config, provider=MockProvider())
    assert "secret-should-not-appear" not in json.dumps(agent.status_dict())


def test_web_status_and_ask_endpoints(tmp_path):
    _seed(tmp_path)
    agent = NotesAgent(_config(tmp_path), provider=MockProvider())
    server = make_server(agent, host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        with urllib.request.urlopen(base + "/api/status") as resp:
            status = json.loads(resp.read())
        assert status["mode"] == "mock" and status["notes_count"] == 1
        req = urllib.request.Request(
            base + "/api/ask",
            data=json.dumps({"question": "What is Abhiverse?"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read())
        assert payload["routing"]["chosen"]["provider"] == "mistralai"
        assert payload["budget"]["used"] == 1
        assert payload["sources"][0]["title"] == "Abhiverse idea"
    finally:
        server.shutdown()
        server.server_close()
