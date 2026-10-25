"""RT-009: X-Forwarded-For / Forwarded must not count as trusted loopback."""
from __future__ import annotations

from starlette.datastructures import Headers

from catalog_assessment import review_allowed
from runtime_guard import client_is_trusted_local


def test_loopback_without_forward_is_trusted():
    assert client_is_trusted_local("127.0.0.1") is True
    assert client_is_trusted_local("::1") is True
    assert client_is_trusted_local("testclient") is True


def test_forwarded_for_rejects_even_on_loopback():
    h = Headers({"x-forwarded-for": "203.0.113.9"})
    assert client_is_trusted_local("127.0.0.1", h) is False


def test_forwarded_header_rejects():
    h = Headers({"forwarded": "for=203.0.113.9;proto=https"})
    assert client_is_trusted_local("127.0.0.1", h) is False


def test_non_loopback_never_trusted():
    assert client_is_trusted_local("203.0.113.1") is False
    assert client_is_trusted_local(None) is False


def test_review_allowed_requires_token_when_forwarded(monkeypatch):
    monkeypatch.delenv("RUBBINGMIND_REVIEW_TOKEN", raising=False)
    h = Headers({"x-forwarded-for": "1.2.3.4"})
    assert review_allowed("127.0.0.1", None, headers=h) is False
    monkeypatch.setenv("RUBBINGMIND_REVIEW_TOKEN", "secret-review")
    assert review_allowed("127.0.0.1", "wrong", headers=h) is False
    assert review_allowed("127.0.0.1", "secret-review", headers=h) is True


def test_review_allowed_loopback_ok_without_forward():
    h = Headers({})
    assert review_allowed("127.0.0.1", None, headers=h) is True
