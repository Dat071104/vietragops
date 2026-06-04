from __future__ import annotations

from app.main import should_load_dotenv


def test_should_skip_dotenv_when_python_dotenv_disabled(monkeypatch):
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")

    assert should_load_dotenv() is False


def test_should_load_dotenv_by_default(monkeypatch):
    monkeypatch.delenv("PYTHON_DOTENV_DISABLED", raising=False)

    assert should_load_dotenv() is True
