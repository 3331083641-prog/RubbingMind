"""RT-004: keep pytest off tracked files and real data/*.sqlite.

Redirects mutable runtime paths into pytest's tmp area for every test.
Individual tests may still monkeypatch further; this is the safety net.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _rt004_isolate_mutable_state(tmp_path_factory, monkeypatch):
    root = Path(tmp_path_factory.mktemp("rubbingmind_mutable"))
    db = root / "rubbingmind.sqlite"
    runtime = root / "runtime"
    uploads = root / "uploads"
    results = root / "results"
    runtime.mkdir(parents=True, exist_ok=True)
    uploads.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("RUBBINGMIND_DB_PATH", str(db))
    monkeypatch.setenv("RUBBINGMIND_RUNTIME_DIR", str(runtime))
    monkeypatch.setenv("RUBBINGMIND_UPLOAD_DIR", str(uploads))
    monkeypatch.setenv("RUBBINGMIND_RESULTS_DIR", str(results))

    # Patch already-imported module constants (env alone is too late after import).
    try:
        import database

        monkeypatch.setattr(database, "DB_PATH", str(db), raising=False)
    except Exception:
        pass

    try:
        import evidence_retrieval as er

        monkeypatch.setattr(er, "INDEX", runtime / "evidence-v2.sqlite", raising=False)
    except Exception:
        pass

    try:
        import upload_storage as us

        if hasattr(us, "UPLOAD_DIR"):
            monkeypatch.setattr(us, "UPLOAD_DIR", uploads, raising=False)
    except Exception:
        pass

    yield root