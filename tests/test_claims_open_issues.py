"""Keep CLAIMS_OPEN_ISSUES.md aligned with live conflict / pending-review scan."""
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/check_claims_open_issues.py'


def test_open_issues_ledger_matches_claims():
    ns = runpy.run_path(str(SCRIPT))
    assert ns['main'](['--check']) == 0
