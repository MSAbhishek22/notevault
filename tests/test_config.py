"""Tests: default Otari model. No network.

The default model is mistralai/mistral-small-latest — verified live on
Otari 9 Nov 2026. openai:gpt-4o-mini is NOT offered on Otari (gateway
424 provider_not_configured, no OpenAI provider in the catalogue), so
it must never again be the default. It remains a valid explicit choice:
the parser accepts the provider:model form unchanged.
"""
import os

from notes_agent.config import Config, config_from_env

DEFAULT_MODEL = "mistralai/mistral-small-latest"


def test_dataclass_default_model_is_mistral_small(tmp_path):
    assert Config(notes_root=tmp_path).model == DEFAULT_MODEL


def test_config_from_env_default_model_without_env_var(tmp_path, monkeypatch):
    monkeypatch.delenv("OTARI_MODEL", raising=False)
    assert config_from_env(tmp_path).model == DEFAULT_MODEL


def test_config_from_env_explicit_colon_form_still_honoured(tmp_path, monkeypatch):
    monkeypatch.setenv("OTARI_MODEL", "openai:gpt-4o-mini")
    assert config_from_env(tmp_path).model == "openai:gpt-4o-mini"


def test_config_from_env_explicit_vendor_form_still_honoured(tmp_path, monkeypatch):
    monkeypatch.setenv("OTARI_MODEL", "mistralai/mistral-small-latest")
    assert config_from_env(tmp_path).model == DEFAULT_MODEL


def test_default_model_is_not_the_unavailable_openai_model(tmp_path):
    assert Config(notes_root=tmp_path).model != "openai:gpt-4o-mini"
