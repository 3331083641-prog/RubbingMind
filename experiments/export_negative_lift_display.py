"""ES-5: write negative_lift_display.json companion (measured primary / rule secondary).

Does NOT rewrite negative_lift_causes.json. Display rows only.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from experiments.eval_export_contract import negative_lift_display

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ("2026-10-17-v2", "2026-10-17-v2-text", "2026-10-15")
OUT_NAME = "negative_lift_display.json"
SHANGHAI = ZoneInfo("Asia/Shanghai")


def build_display(batch: str, nlc: dict) -> dict:
    rows = []
    for case in nlc.get("cases") or []:
        view = negative_lift_display(case)
        evidence = view["measuredEvidence"]
        triggered = [ev.get("measure") for ev in evidence if ev.get("triggered")]
        rows.append({
            "caseId": case.get("caseId"),
            "sampleId": case.get("sampleId"),
            "method": case.get("method"),
            "split": case.get("split"),
            "degradation": case.get("degradation"),
            "psnrDelta": view["psnrDelta"],
            "primaryMeasuredCauses": view["primaryMeasuredCauses"],
            "measuredEvidenceCount": len(evidence),
            "triggeredMeasures": triggered,
            "secondaryRuleInferred": view["secondaryRuleInferred"],
            "forbidden": view["forbidden"],
            "evidenceSource": "derived/negative_lift_causes.json#cases[].measuredEvidence",
        })
    return {
        "batch": batch,
        "derivedAt": datetime.now(SHANGHAI).isoformat(timespec="seconds"),
        "derivedBy": "experiments/export_negative_lift_display.py",
        "source": "derived/negative_lift_causes.json",
        "measuredCriteriaVersion": nlc.get("measuredCriteriaVersion"),
        "negativeLiftN": nlc.get("negativeLiftN"),
        "rowCount": len(rows),
        "rows": rows,
        "note": "ES-5 口径：measuredCauses 主列；ruleInferred 仅次列并标注启发式；禁止把 ruleInferredCause 写成测量原因",
    }


def export_batch(batch: str, *, dry_run: bool = False) -> Path | None:
    nlc_path = ROOT / "experiments" / "results" / batch / "derived" / "negative_lift_causes.json"
    if not nlc_path.is_file():
        return None
    nlc = json.loads(nlc_path.read_text(encoding="utf-8"))
    out = build_display(batch, nlc)
    out_path = nlc_path.parent / OUT_NAME
    if not dry_run:
        out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", action="append")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for batch in args.batch or list(BATCHES):
        path = export_batch(batch, dry_run=args.dry_run)
        print(batch, path if path else "missing NLC", flush=True)


if __name__ == "__main__":
    main()
