"""ES-4: enrich mechanism step image captions with provenance (JSON only).

Does NOT rewrite PNG bytes, does NOT re-run mechanism_cases (R7 ban).
Adds batch / caseId / derivedAt / headCommit / sourcePath / captionNote to each
images[] entry so reports can show source file, batch, and generation time
without fabricating metrics.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCHES = ("2026-10-17-v2", "2026-10-17-v2-text")
CAPTION_NOTE = (
    "机制步骤图注：来源为本案例 derived/mechanism 目录；"
    "指标属 v2.0 已存，图属记录 headCommit 时重算；"
    "headCommit 落后 tip 时不得宣称与当前 tip 字节一致（见 MECHANISM_HEAD_NOTE）。"
)


def enrich_batch(batch: str, *, dry_run: bool = False) -> dict:
    mech_root = ROOT / "experiments" / "results" / batch / "derived" / "mechanism"
    index_path = mech_root / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    derived_at = index.get("derivedAt") or "未记录"
    head = index.get("headCommit") or "未记录"
    updated_files = 0
    updated_images = 0
    for case in index.get("cases") or []:
        case_id = case["caseId"]
        directory = case.get("directory") or f"derived/mechanism/{case_id}"
        folder = ROOT / "experiments" / "results" / batch / directory
        if not folder.is_dir():
            folder = mech_root / case_id
        mech_path = folder / "mechanism.json"
        if not mech_path.is_file():
            raise FileNotFoundError(mech_path)
        data = json.loads(mech_path.read_text(encoding="utf-8"))
        images = data.get("images") or []
        changed = False
        for entry in images:
            if not isinstance(entry, dict):
                continue
            rel = entry.get("file")
            if not rel or rel == "未记录":
                entry.setdefault("unavailableReason", entry.get("unavailableReason") or "未记录")
                continue
            before = dict(entry)
            entry["batch"] = batch
            entry["caseId"] = case_id
            entry["derivedAt"] = derived_at
            entry["headCommit"] = head
            entry["sourcePath"] = f"{directory.rstrip('/')}/{Path(str(rel)).name}"
            entry["captionNote"] = CAPTION_NOTE
            if entry != before:
                changed = True
                updated_images += 1
        if changed:
            updated_files += 1
            if not dry_run:
                mech_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
    index["captionProvenance"] = {
        "enrichedBy": "experiments/enrich_mechanism_captions.py",
        "fields": ["batch", "caseId", "derivedAt", "headCommit", "sourcePath", "captionNote"],
        "pngBytesUntouched": True,
        "note": CAPTION_NOTE,
    }
    if not dry_run:
        index_path.write_text(
            json.dumps(index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return {
        "batch": batch,
        "files": updated_files,
        "images": updated_images,
        "derivedAt": derived_at,
        "headCommit": head,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--batch", action="append", dest="batches")
    args = parser.parse_args(argv)
    batches = tuple(args.batches) if args.batches else BATCHES
    summary = [enrich_batch(b, dry_run=args.dry_run) for b in batches]
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
