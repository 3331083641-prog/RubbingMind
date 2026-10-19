"""Derive passthrough / processed status for existing experiment batches.

Read-only on the historical batches: results.json, CSV and PNG files are opened
for reading only and never rewritten. Output goes to
<output-root>/experiments/results/<batch>/derived/applied_status.{csv,json}.

Criteria (recorded per row):
  pixel-equal-v1          output PNG decoded pixels equal the input PNG pixels.
                          byteIdentical (file SHA-256 equal) is also reported.
  input-from-degraded-v1  2026-10-15 rows have no input field; the method
                          'degraded' returns image.copy(), so its PNG for the
                          same sample and degradation is the input.
  no-images               batches without saved images (2026-10-18-v21-heldout):
                          isPassthrough stays null. Two indicators are reported
                          separately and are NOT used as the criterion:
                          psnrDeltaFromInput == 0, and an operator chain that
                          by code reading cannot change pixels.

Usage:
  python experiments/derive_applied_status.py --source-root D:\\RubbingMind --output-root .
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from degradation_analysis import change_stats  # noqa: E402
from experiments.applied_status import split_means  # noqa: E402
from experiments.notch_na_changes import OTHER, ROUNDING, annotate  # noqa: E402

# Operators that only copy input pixels (degradation_analysis v2.0/v2.1).
COPY_ONLY = {'skip_notch', 'identity', 'preserve_missing', 'fallback_identity'}
FIELDS = ['batch', 'experimentId', 'rowIndex', 'sampleId', 'split', 'degradation', 'strength', 'method',
          'applicabilityRecorded', 'appliedStatus', 'isPassthrough', 'criterion', 'byteIdentical',
          'changedPixelCount', 'totalPixelCount', 'changedPixelRatio', 'maxAbsDiff', 'meanAbsDiff',
          'inputFile', 'inputSha256Actual', 'outputFile', 'outputSha256Actual', 'shaMatchesRecord',
          'psnr', 'ssim', 'edgeF1', 'psnrDeltaFromInput', 'indicatorPsnrDeltaZero', 'indicatorCopyOnlyOperators',
          'undeterminedReason', 'appliedStatusDetail', 'naChangeEvidence']


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_gray(path: Path):
    image = cv2.imdecode(np.frombuffer(path.read_bytes(), np.uint8), cv2.IMREAD_UNCHANGED)
    if image is not None and image.ndim == 3:
        image = cv2.cvtColor(image[:, :, :3], cv2.COLOR_BGR2GRAY)
    return image


def _status(method, applicability, passthrough):
    if applicability == 'baseline' or method == 'degraded':
        return 'baseline'
    if applicability == 'failed':
        return 'failed'
    if passthrough is None:
        return 'undetermined'
    if passthrough:
        return 'passthrough_not_applicable' if applicability == 'not_applicable' else 'passthrough'
    return 'processed_not_applicable_label' if applicability == 'not_applicable' else 'processed'


def derive_batch(batch_dir: Path):
    data = json.loads((batch_dir / 'results.json').read_text(encoding='utf-8'))
    config = data.get('config') if isinstance(data.get('config'), dict) else {}
    experiment_id = config.get('experimentId') or data.get('experimentId')
    rows = data['rows']
    has_images = any(r.get('output') for r in rows)
    out = []
    cache = {}

    def file_info(name):
        if name not in cache:
            path = batch_dir / name
            cache[name] = (sha256(path), read_gray(path)) if path.is_file() else (None, None)
        return cache[name]

    for index, r in enumerate(rows):
        item = {k: None for k in FIELDS}
        item.update(batch=batch_dir.name, experimentId=experiment_id, rowIndex=index, sampleId=r.get('sampleId'),
                    split=r.get('split'), degradation=r.get('degradation'), strength=r.get('strength'),
                    method=r.get('method'), applicabilityRecorded=r.get('applicability'),
                    psnr=r.get('psnr'), ssim=r.get('ssim'), edgeF1=r.get('edgeF1'),
                    psnrDeltaFromInput=r.get('psnrDeltaFromInput'))
        if has_images:
            input_name = r.get('input')
            criterion = 'pixel-equal-v1'
            if not input_name:
                input_name = f"{r['sampleId']}_{r['degradation']}_degraded.png"
                criterion = 'pixel-equal-v1+input-from-degraded-v1'
            output_name = r.get('output')
            item.update(inputFile=input_name, outputFile=output_name, criterion=criterion)
            if r.get('error') or not output_name:
                item['undeterminedReason'] = '运行失败，无输出'
            else:
                in_sha, in_px = file_info(input_name)
                out_sha, out_px = file_info(output_name)
                item.update(inputSha256Actual=in_sha, outputSha256Actual=out_sha)
                recorded = [r.get('outputSha256')] + ([r.get('inputSha256')] if r.get('inputSha256') else [])
                actual = [out_sha] + ([in_sha] if r.get('inputSha256') else [])
                item['shaMatchesRecord'] = all(a == b for a, b in zip(actual, recorded) if b)
                if in_px is None or out_px is None or in_px.shape != out_px.shape:
                    item['undeterminedReason'] = '输入或输出文件缺失、无法解码或尺寸不同'
                else:
                    stats = change_stats(in_px, out_px)
                    item.update(isPassthrough=stats['isPassthrough'], byteIdentical=in_sha == out_sha,
                                changedPixelCount=stats['changedPixelCount'], totalPixelCount=stats['totalPixelCount'],
                                changedPixelRatio=stats['changedPixelRatio'], maxAbsDiff=stats['maxAbsDiff'],
                                meanAbsDiff=stats['meanAbsDiff'])
        else:
            operators = r.get('diagnosticsOperators') or []
            item.update(criterion='no-images', undeterminedReason='本批次未保存任何图像，无法逐像素判定',
                        indicatorPsnrDeltaZero=None if r.get('psnrDeltaFromInput') is None else r['psnrDeltaFromInput'] == 0,
                        indicatorCopyOnlyOperators=(bool(operators) and set(operators) <= COPY_ONLY) if r.get('method', '').startswith('adaptive') else None)
        item['appliedStatus'] = _status(item['method'], item['applicabilityRecorded'], item['isPassthrough'])
        if item['appliedStatus'] == 'undetermined' and item['undeterminedReason'] is None:
            item['undeterminedReason'] = '未知'
        out.append(item)
    if has_images:
        # E-05: explain notch rows labelled not_applicable whose pixels changed.
        annotate(batch_dir, out)
    return data, experiment_id, has_images, out


def summarize(items, keys):
    groups = {}
    for item in items:
        groups.setdefault(tuple(item[k] for k in keys), []).append(item)
    summary = []
    for key, members in sorted(groups.items(), key=lambda kv: tuple('' if v is None else str(v) for v in kv[0])):
        entry = dict(zip(keys, key))
        entry.update(split_means(members, ('psnr', 'ssim', 'edgeF1')))
        entry['passthroughCriterion'] = '|'.join(sorted({m['criterion'] for m in members if m['criterion']}))
        entry['notApplicableLabelButChangedN'] = sum(m['appliedStatus'] == 'processed_not_applicable_label' for m in members)
        entry['notApplicableModifiedRoundingN'] = sum(m['appliedStatusDetail'] == ROUNDING for m in members)
        entry['notApplicableModifiedOtherN'] = sum(m['appliedStatusDetail'] == OTHER for m in members)
        entry['indicatorPsnrDeltaZeroN'] = sum(m['indicatorPsnrDeltaZero'] is True for m in members)
        entry['indicatorCopyOnlyOperatorsN'] = sum(m['indicatorCopyOnlyOperators'] is True for m in members)
        summary.append(entry)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-root', default=str(ROOT), help='读取历史批次的仓库根目录（只读）')
    parser.add_argument('--output-root', default=str(ROOT), help='写入 derived 文件的仓库根目录')
    args = parser.parse_args(argv)
    source = Path(args.source_root).resolve() / 'experiments/results'
    target = Path(args.output_root).resolve() / 'experiments/results'
    report = []
    for results in sorted(source.glob('*/results.json')):
        batch_dir = results.parent
        data, experiment_id, has_images, items = derive_batch(batch_dir)
        keys_split = ['split', 'method'] if any(i['split'] for i in items) else ['method']
        payload = {
            'experimentId': experiment_id, 'batch': batch_dir.name,
            'derivedAt': datetime.now(timezone.utc).isoformat(),
            'derivedBy': 'experiments/derive_applied_status.py',
            'sourceResultsSha256': sha256(results),
            'imagesAvailable': has_images,
            'criterion': 'pixel-equal-v1' if has_images else 'no-images (isPassthrough=null)',
            'note': ('历史结果文件未改动；本文件只做派生标注。均值按 all / processed / passthrough 分别计算。'
                     if has_images else
                     '本批次没有保存图像，isPassthrough 一律为 null，不据 PSNR 或决策链猜测；两个指示量仅供参考。'),
            'summaryByMethod': summarize(items, ['method']),
            'summaryBySplitMethod': summarize(items, keys_split),
            'summaryByMethodDegradation': summarize(items, keys_split + ['degradation']),
            'rows': items,
        }
        out_dir = target / batch_dir.name / 'derived'
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / 'applied_status.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
        with (out_dir / 'applied_status.csv').open('w', encoding='utf-8-sig', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows([dict(i, naChangeEvidence=json.dumps(i['naChangeEvidence'], ensure_ascii=False) if i['naChangeEvidence'] else None) for i in items])
        report.append({'batch': batch_dir.name, 'rows': len(items),
                       'counts': {s: sum(i['appliedStatus'] == s for i in items) for s in sorted({i['appliedStatus'] for i in items})},
                       'shaMismatches': sum(i['shaMatchesRecord'] is False for i in items),
                       'appliedStatusDetail': {d: sum(i['appliedStatusDetail'] == d for i in items) for d in (ROUNDING, OTHER)}})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == '__main__':
    main()
