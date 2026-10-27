"""RT-005: security response headers; remote hides OpenAPI surface."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient as StarletteTestClient

from runtime_guard import SecurityHeadersMiddleware


def test_security_headers_middleware_sets_basics():
    async def homepage(request):
        return PlainTextResponse("ok")

    app = Starlette(routes=[Route("/", homepage)])
    app.add_middleware(SecurityHeadersMiddleware)
    client = StarletteTestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "SAMEORIGIN"
    assert "frame-ancestors" in (r.headers.get("content-security-policy") or "")


def test_main_app_emits_security_headers():
    import main as main_mod

    client = TestClient(main_mod.app)
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "SAMEORIGIN"
    assert "frame-ancestors" in (r.headers.get("content-security-policy") or "")


def test_remote_deployment_disables_docs_openapi():
    """Fresh interpreter with RUBBINGMIND_DEPLOYMENT=remote => /docs & openapi gone."""
    root = Path(__file__).resolve().parents[1]
    script = r"""
import os
os.environ["RUBBINGMIND_DEPLOYMENT"] = "remote"
os.environ.pop("RUBBINGMIND_ADMIN_TOKEN", None)
from fastapi.testclient import TestClient
import main
c = TestClient(main.app)
assert c.get("/docs").status_code == 404, c.get("/docs").status_code
assert c.get("/redoc").status_code == 404
assert c.get("/openapi.json").status_code == 404
# health still works
h = c.get("/api/health")
assert h.status_code == 200
print("remote-docs-ok")
"""
    env = os.environ.copy()
    env["RUBBINGMIND_DEPLOYMENT"] = "remote"
    env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
    # isolate mutable paths so import does not touch tracked DBs
    import tempfile
    td = tempfile.mkdtemp(prefix="rt005_")
    env["RUBBINGMIND_DB_PATH"] = str(Path(td) / "t.sqlite")
    env["RUBBINGMIND_RUNTIME_DIR"] = str(Path(td) / "runtime")
    env["RUBBINGMIND_UPLOAD_DIR"] = str(Path(td) / "uploads")
    env["RUBBINGMIND_RESULTS_DIR"] = str(Path(td) / "results")
    Path(env["RUBBINGMIND_RUNTIME_DIR"]).mkdir()
    Path(env["RUBBINGMIND_UPLOAD_DIR"]).mkdir()
    Path(env["RUBBINGMIND_RESULTS_DIR"]).mkdir()
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "remote-docs-ok" in proc.stdout
