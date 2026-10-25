"""Overridable locations of mutable local state (ADR-007, ARCHITECTURE_DECISIONS R1-7).

Every default is exactly the historical in-repo location, so running without
any RUBBINGMIND_* variable behaves as before. Authoritative versioned data
(data/catalog, data/history, experiments) is intentionally NOT relocatable.

Variables (absolute or relative paths; empty means "use default"):
  RUBBINGMIND_DB_PATH      SQLite file          default <repo>/data/rubbingmind.sqlite
  RUBBINGMIND_RUNTIME_DIR  runtime state dir    default <repo>/data/runtime
  RUBBINGMIND_UPLOAD_DIR   user upload images   default <repo>/data/uploads
  RUBBINGMIND_RESULTS_DIR  processing runs      default <repo>/static/results
                           (still served under the URL /static/results)
"""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parent
ENV_VARS = ('RUBBINGMIND_DB_PATH', 'RUBBINGMIND_RUNTIME_DIR', 'RUBBINGMIND_UPLOAD_DIR', 'RUBBINGMIND_RESULTS_DIR')


def env_path(name: str) -> Path | None:
    value = os.environ.get(name, '').strip()
    return Path(value).expanduser().resolve() if value else None


def db_path() -> str:
    override = env_path('RUBBINGMIND_DB_PATH')
    return str(override) if override else os.path.join(str(REPO), 'data', 'rubbingmind.sqlite')


def runtime_dir() -> Path:
    return env_path('RUBBINGMIND_RUNTIME_DIR') or REPO / 'data' / 'runtime'


def upload_dir() -> Path:
    return env_path('RUBBINGMIND_UPLOAD_DIR') or REPO / 'data' / 'uploads'


def results_override() -> Path | None:
    """Only non-None when explicitly relocated; callers keep their historical default otherwise."""
    return env_path('RUBBINGMIND_RESULTS_DIR')


def describe() -> dict:
    """Effective locations, for startup logging. Contains paths only, never secrets."""
    return {
        'dbPath': db_path(), 'runtimeDir': str(runtime_dir()), 'uploadDir': str(upload_dir()),
        'resultsDir': str(results_override() or REPO / 'static' / 'results'),
        'overridden': [name for name in ENV_VARS if env_path(name)],
    }
