"""ES-3: write lift_claim_summary.json from existing ci_by_artifact.json.

Does NOT re-run bootstrap. Labels use may_claim_positive_lift / lift_claim_label only.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from experiments.eval_export_contract import (
    lift_claim_label,
    may_claim_positive_lift,
    summarize_lift_claims,
)

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ("2026-10-17-v2", "2026-10-17-v2-text")
OUT_NAME = "lift_claim_summary.json"
SHANGHAI = ZoneInfo("Asia/Shanghai")


def build_summary(batch: str, ci: dict) -> dict:
    metric = "psnr"
    counts = summarize_lift_claims(ci, metric)
    min_reliable = ci.get("minReliableArtifacts") or 3
    positive_groups = []
    for g in ci.get("groups") or []:
        if lift_claim_label(g, metric) != "positive_lift_ci_excludes_zero":
            continue
        positive_groups.append({
            "split": g.get("split"),
            "method": g.get("method"),
            "degradation": g.get("degradation"),
            "scope": g.get("scope"),
            "artifactN": g.get("artifactN"),
            "psnrGainCI95Low": g.get("psnrGainCI95Low"),
            "psnrGainCI95High": g.get("psnrGainCI95High"),
            "ciReliable": g.get("ciReliable"),
            "liftClaimLabel": "positive_lift_ci_excludes_zero",
        })
    for g in positive_groups:
        assert may_claim_positive_lift(
            ci_low=g["psnrGainCI95Low"],
            ci_reliable=g["ciReliable"],
            artifact_n=g["artifactN"],
            min_reliable=min_reliable,
        )
    return {
        "batch": batch,
        "metric": metric,
        "derivedAt": datetime.now(SHANGHAI).isoformat(timespec="seconds"),
        "derivedBy": "experiments/export_lift_claim_summary.py",
        "source": "derived/ci_by_artifact.json",
        "sourceResultsSha256": ci.get("sourceResultsSha256"),
        "appliedStatusSha256": ci.get("appliedStatusSha256"),
        "bootstrap": ci.get("bootstrap"),
        "seed": ci.get("seed"),
        "minReliableArtifacts": min_reliable,
        "groupCount": len(ci.get("groups") or []),
        "claimCounts": counts,
        "positiveLiftGroups": positive_groups,
        "rule": "only claim 提升 when bootstrap CI lower bound > 0, ciReliable, artifactN >= minReliable",
        "note": "ES-3 gateable summary; no bootstrap recompute; do not treat spans_zero/negative as 提升",
    }


def export_batch(batch: str, *, dry_run: bool = False) -> Path:
    ci_path = ROOT / "experiments" / "results" / batch / "derived" / "ci_by_artifact.json"
    ci = json.loads(ci_path.read_text(encoding="utf-8"))
    out = build_summary(batch, ci)
    out_path = ci_path.parent / OUT_NAME
    if not dry_run:
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", choices=BATCHES, action="append")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for batch in args.batch or list(BATCHES):
        path = export_batch(batch, dry_run=args.dry_run)
        print(batch, path if not args.dry_run else "(dry-run)", flush=True)


if __name__ == "__main__":
    main()
