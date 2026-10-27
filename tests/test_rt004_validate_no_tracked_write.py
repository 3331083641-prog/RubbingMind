"""RT-004: validate_stele_asset must not dirty tracked asset-validation.json during pytest."""
from pathlib import Path
import subprocess
import hashlib

from scripts.validate_stele_asset import run


def test_run_default_does_not_write_tracked_report():
    tracked = Path("screenshots/stele-final/asset-validation.json")
    before = tracked.read_bytes() if tracked.exists() else None
    before_hash = hashlib.sha256(before).hexdigest() if before is not None else None
    result = run()  # report_path=None => no write
    assert result["pass"] is True
    after = tracked.read_bytes() if tracked.exists() else None
    after_hash = hashlib.sha256(after).hexdigest() if after is not None else None
    assert before_hash == after_hash


def test_run_can_write_to_tmp(tmp_path):
    out = tmp_path / "asset-validation.json"
    result = run(report_path=out)
    assert out.is_file()
    assert result["pass"] is True
