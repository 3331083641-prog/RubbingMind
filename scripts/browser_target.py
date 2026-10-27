"""RT-003: refuse default user/dev ports 8000 and 5180 for browser/smoke scripts."""
from __future__ import annotations

import os
import sys
from urllib.parse import urlparse

FORBIDDEN_PORTS = {8000, 5180}


def _port_of(url: str) -> int | None:
    parsed = urlparse(url)
    if parsed.port is not None:
        return parsed.port
    if parsed.scheme == "https":
        return 443
    if parsed.scheme == "http":
        return 80
    return None


def assert_safe_target(url: str, *, label: str = "url") -> str:
    """Return url if allowed; otherwise print guidance and exit nonzero."""
    if not url or not str(url).strip():
        print(
            f"RT-003: missing {label}. Pass an explicit test URL "
            f"(e.g. http://127.0.0.1:8740) via CLI flag or env; "
            f"ports {sorted(FORBIDDEN_PORTS)} are refused.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    url = str(url).strip()
    port = _port_of(url)
    if port in FORBIDDEN_PORTS:
        print(
            f"RT-003: refused {label}={url!r} (port {port} is a user/dev default). "
            f"Use a project test port such as 8740/5740/8710/5710.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return url


def require_env_url(env_name: str, *, label: str | None = None) -> str:
    return assert_safe_target(os.environ.get(env_name, ""), label=label or env_name)