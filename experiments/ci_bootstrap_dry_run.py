"""ES-3: read-only dry-run verification of frozen bootstrap CI derived files.

Does NOT recompute bootstrap endpoints and does NOT write derived/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from experiments.eval_export_contract import (
    MARKER_UNEVALUATED,
    summarize_lift_claims,
)

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ("2026-10-17-v2", "2026-10-17-v2-text")
EXPECT = {
    "bootstrap": 1000,
    "seed": 20261019,
    "artifactN": 14,
    "minReliableArtifacts": 3,
    "groupCount": 324,
    "claimCounts": {
        "2026-10-17-v2": {
            "positive_lift_ci_excludes_zero": 35,
            "no_positive_lift_claim": 197,
            MARKER_UNEVALUATED: 92,
        },
        "2026-10-17-v2-text": {
            "positive_lift_ci_excludes_zero": 35,
            "no_positive_lift_claim": 191,
            MARKER_UNEVALUATED: 98,
        },
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_batch(batch: str) -> dict:
    derived = ROOT / "experiments" / "results" / batch / "derived"
    ci_path = derived / "ci_by_artifact.json"
    summary_path = derived / "lift_claim_summary.json"
    results_path = ROOT / "experiments" / "results" / batch / "results.json"
    applied_path = derived / "applied_status.json"
    mismatches: list[str] = []
    open_findings: list[str] = []

    ci = json.loads(ci_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    for key in ("bootstrap", "seed", "artifactN", "minReliableArtifacts"):
        if ci.get(key) != EXPECT[key]:
            mismatches.append(f"{key}: got {ci.get(key)!r} want {EXPECT[key]!r}")

    groups = ci.get("groups") or []
    if len(groups) != EXPECT["groupCount"]:
        mismatches.append(f"groupCount: got {len(groups)} want {EXPECT['groupCount']}")

    results_sha = _sha256(results_path)
    applied_sha = _sha256(applied_path)
    if ci.get("sourceResultsSha256") != results_sha:
        mismatches.append("sourceResultsSha256 drift vs results.json")
    if ci.get("appliedStatusSha256") != applied_sha:
        open_findings.append(
            "appliedStatusSha256 drift vs applied_status.json "
            "(open finding; do not silent-rewrite ci_by_artifact)"
        )

    live_counts = summarize_lift_claims(ci, "psnr")
    frozen = EXPECT["claimCounts"][batch]
    if live_counts != frozen:
        mismatches.append(f"live claimCounts {live_counts} != frozen {frozen}")
    if summary.get("claimCounts") != frozen:
        mismatches.append(
            f"lift_claim_summary claimCounts {summary.get('claimCounts')} != frozen {frozen}"
        )
    if summary.get("claimCounts") != live_counts:
        mismatches.append("summary claimCounts != summarize_lift_claims(ci)")

    return {
        "batch": batch,
        "ok": not mismatches,
        "mismatches": mismatches,
        "openFindings": open_findings,
        "wroteDerived": False,
        "bootstrap": ci.get("bootstrap"),
        "seed": ci.get("seed"),
        "artifactN": ci.get("artifactN"),
        "groupCount": len(groups),
        "claimCounts": live_counts,
        "sourceResultsSha256Matches": ci.get("sourceResultsSha256") == results_sha,
        "appliedStatusSha256Matches": ci.get("appliedStatusSha256") == applied_sha,
        "note": "read-only; no bootstrap recompute; no derived write; openFindings keep ES-3 open",
    }


def dry_run(batches=BATCHES) -> dict:
    reports = [verify_batch(b) for b in batches]
    return {
        "wroteDerived": False,
        "recomputedBootstrap": False,
        "ok": all(r["ok"] for r in reports),
        "hasOpenFindings": any(r.get("openFindings") for r in reports),
        "batches": reports,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch",
        action="append",
        dest="batches",
        help="batch id (default: both v2 batches)",
    )
    args = parser.parse_args(argv)
    report = dry_run(tuple(args.batches) if args.batches else BATCHES)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())