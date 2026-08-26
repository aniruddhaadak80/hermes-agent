"""Strength check for HERMES_DASHBOARD_SESSION_TOKEN — weak values fall back to generated tokens."""

import os
import secrets

import pytest


def test_resolve_session_token_rejects_empty_string(monkeypatch):
    from hermes_cli.web_server import _resolve_session_token

    monkeypatch.setenv("HERMES_DASHBOARD_SESSION_TOKEN", "")
    assert _resolve_session_token().startswith("eyJ") or len(_resolve_session_token()) > 32


def test_resolve_session_token_rejects_short_token(monkeypatch):
    from hermes_cli.web_server import _resolve_session_token

    monkeypatch.setenv("HERMES_DASHBOARD_SESSION_TOKEN", "short")
    result = _resolve_session_token()
    assert len(result) >= 32
    assert result != "short"


def test_resolve_session_token_rejects_placeholder(monkeypatch):
    from hermes_cli.web_server import _resolve_session_token

    monkeypatch.setenv("HERMES_DASHBOARD_SESSION_TOKEN", "***")
    result = _resolve_session_token()
    assert len(result) >= 32
    assert result != "***"


def test_resolve_session_token_rejects_placeholder(monkeypatch):
    from hermes_cli.web_server import _resolve_session_token

    monkeypatch.setenv("HERMES_DASHBOARD_SESSION_TOKEN", "your_api_key_here")
    result = _resolve_session_token()
    assert len(result) >= 32
    assert result != "your_api_key_here"


def test_resolve_session_token_accepts_valid_token(monkeypatch):
    from hermes_cli.web_server import _resolve_session_token

    # 16+ chars, not a known placeholder
    strong = "strong-random-token-123456"
    monkeypatch.setenv("HERMES_DASHBOARD_SESSION_TOKEN", strong)
    assert _resolve_session_token() == strong


def test_resolve_session_token_fallback_generated_is_urlsafe(monkeypatch):
    from hermes_cli.web_server import _resolve_session_token

    monkeypatch.delenv("HERMES_DASHBOARD_SESSION_TOKEN", raising=False)
    token = _resolve_session_token()
    # URL-safe base64: no +, /, =; length ~43 chars for 32 bytes
    assert len(token) >= 40
    assert set(token).isdisjoint(set("+/="))