"""RT-008 vite host/pin, RT-010 CI draft, RT-013 soft-delete. Product tickets stay open."""
from __future__ import annotations

import json
from pathlib import Path

import museum_processing
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]


def test_rt008_vite_pinned_and_loopback_bound():
    pkg = json.loads((ROOT / "apps/web/package.json").read_text(encoding="utf-8"))
    vite_range = pkg["devDependencies"]["vite"]
    assert vite_range.startswith("^6.4.") or vite_range.startswith("6.4."), vite_range
    assert "--host 127.0.0.1" in pkg["scripts"]["dev"]
    assert "--host 127.0.0.1" in pkg["scripts"]["preview"]
    vite = (ROOT / "apps/web/vite.config.ts").read_text(encoding="utf-8")
    assert "host: '127.0.0.1'" in vite
    assert "RT-008" in vite
    assert (ROOT / "docs/product-upgrade/RT008_VITE_AUDIT.md").is_file()


def test_rt010_ci_draft_and_feature_triggers():
    assert (ROOT / "docs/product-upgrade/RT010_CI_DRAFT.md").is_file()
    draft = ROOT / "docs/product-upgrade/ci-feature.draft.yml"
    assert draft.is_file()
    assert "validate_history_gis.py" in draft.read_text(encoding="utf-8")
    # draft must NOT live under .github/workflows (would auto-run)
    assert not (ROOT / ".github/workflows/ci-feature.draft.yml").exists()
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert '"feature/**"' in ci or "feature/**" in ci


def test_rt006_remaining_decision_doc():
    doc = ROOT / "docs/product-upgrade/RT006_STATIC_INDEX_DECISION.md"
    assert doc.is_file()
    text = doc.read_text(encoding="utf-8")
    assert "Green" in text
    assert (ROOT / "static/index.html").is_file()  # not deleted without Green


def test_rt013_soft_delete_and_restore(monkeypatch, tmp_path):
    import base64
    from io import BytesIO

    from PIL import Image

    from main import ProcessRequest, app
    from museum_manager import museum_manager
    import shutil

    buf = BytesIO()
    Image.new("RGB", (4, 4)).save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode()

    class Engine:
        def process_rubbing(self, **kwargs):
            return {
                "restored_b64": encoded,
                "metrics": {"elapsed_ms": 1, "psnr": None},
                "diagnostic_metrics": {},
            }

    source = ROOT / "apps/web/public/assets/stele/museum-rubbings/qing_02_wushi_reerection_readable.jpg"
    if not source.is_file():
        # hermetic fallback: skip if asset absent in sparse checkout
        return
    input_copy = tmp_path / "apps/web/public/assets/stele/museum-rubbings/qing_02_wushi_reerection_readable.jpg"
    input_copy.parent.mkdir(parents=True)
    shutil.copyfile(source, input_copy)

    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setattr(museum_processing, "BASE", tmp_path)
    monkeypatch.setattr(museum_processing, "RESULTS_DIR", None)
    monkeypatch.setenv("RUBBINGMIND_RUNTIME_DIR", str(runtime))
    # reload runtime_dir binding used inside delete_run
    import runtime_paths

    monkeypatch.setattr(museum_processing, "runtime_dir", lambda: runtime)

    result = museum_processing.process_verified_request(
        ProcessRequest(stele_id="qing_02_wushi_reerection"), museum_manager, Engine()
    )
    run_id = result["runId"]
    run_dir = tmp_path / "static" / "results" / "qing_02_wushi_reerection" / run_id
    assert run_dir.is_dir()

    client = TestClient(app)
    r = client.delete(f"/api/steles/qing_02_wushi_reerection/runs/{run_id}?confirm=true")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("softDeleted") is True
    assert body.get("recoverable") is True
    assert not run_dir.exists()
    assert client.get("/api/steles/qing_02_wushi_reerection/runs").json() == []

    trash_hits = list((runtime / "trash" / "runs" / "qing_02_wushi_reerection").glob(f"{run_id}__*"))
    assert trash_hits, "expected soft-delete trash folder"
    assert (trash_hits[0] / "soft_delete.json").is_file()

    assert museum_processing.restore_run("qing_02_wushi_reerection", run_id) is True
    assert run_dir.is_dir()
    assert museum_processing.read_run("qing_02_wushi_reerection", run_id) is not None


def test_rt013_refuse_referenced_run(monkeypatch, tmp_path):
    monkeypatch.setattr(
        museum_processing,
        "_glyph_references_to_run",
        lambda stele_id, run_id: [{"kind": "glyph_inference", "inferenceId": "inf-1"}],
    )
    # fabricate a readable run without full process
    stele_id = "qing_02_wushi_reerection"
    run_id = "20261025T120000_deadbeef"
    root = tmp_path / "static" / "results" / stele_id / run_id
    root.mkdir(parents=True)
    (root / "processing.json").write_text(
        json.dumps(
            {
                "runId": run_id,
                "steleId": stele_id,
                "algorithmVersion": "test",
                "isPassthrough": False,
                "changedPixelCount": 1,
                "totalPixelCount": 1,
                "changedPixelRatio": 1.0,
                "maxAbsDiff": 1,
                "meanAbsDiff": 1.0,
                "passthroughCriterion": "pixel-equal-v1",
                "passthroughSource": "recorded",
                "passthroughUndeterminedReason": None,
                "effectiveParameters": {},
                "effectiveParametersSource": "recorded",
                "effectiveParametersUnavailableReason": None,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(museum_processing, "BASE", tmp_path)
    monkeypatch.setattr(museum_processing, "RESULTS_DIR", None)
    try:
        museum_processing.delete_run(stele_id, run_id)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert str(exc).startswith("run_referenced:")
    assert root.is_dir()  # not deleted
