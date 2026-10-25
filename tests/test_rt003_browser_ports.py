"""RT-003: browser helpers refuse ports 8000 and 5180."""
import pytest

from scripts.browser_target import assert_safe_target, FORBIDDEN_PORTS


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5180/",
    "http://localhost:8000/api",
])
def test_forbidden_ports_exit(url):
    with pytest.raises(SystemExit) as ei:
        assert_safe_target(url, label="url")
    assert ei.value.code == 2


def test_missing_url_exits():
    with pytest.raises(SystemExit) as ei:
        assert_safe_target("", label="url")
    assert ei.value.code == 2


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:8740",
    "http://127.0.0.1:5710/",
    "http://127.0.0.1:8710/health",
])
def test_safe_ports_pass(url):
    assert assert_safe_target(url, label="url") == url


def test_forbidden_set():
    assert FORBIDDEN_PORTS == {8000, 5180}
