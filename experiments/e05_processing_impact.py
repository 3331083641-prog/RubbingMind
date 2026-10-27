"""E-05 impact on single-image museum processing (read-only).

Runs RubbingAlgorithmEngine.process_rubbing on static/samples/*.png with the engine
at --base-commit (before the E-05 fix) and with this working tree, for every
filter_type accepted by the API, and compares the restored gray images pixel by pixel.
museum_processing.process_verified_request delegates to process_rubbing, so its
restored output changes exactly when this comparison changes.
Output: experiments/derived/e05_processing_impact.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import algorithm_engine as head  # noqa: E402

FILTERS = ('adaptive', 'notch', 'gaussian', 'butterworth')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-commit', default='f0c5886')
    args = parser.parse_args(argv)
    source = subprocess.check_output(['git', 'show', f'{args.base_commit}:algorithm_engine.py'], cwd=ROOT)
    old = types.ModuleType('algorithm_engine_base')
    exec(compile(source, f'{args.base_commit}:algorithm_engine.py', 'exec'), old.__dict__)
    rows = []
    for path in sorted((ROOT / 'static/samples').glob('*.png')):
        for filter_type in FILTERS:
            kwargs = dict(filter_type=filter_type, d0=48 if filter_type == 'notch' else 60)
            a = old.RubbingAlgorithmEngine().process_rubbing(str(path), **kwargs)
            b = head.RubbingAlgorithmEngine().process_rubbing(str(path), **kwargs)
            ra = head.base64_to_mat(a['restored_b64'], is_gray=True)
            rb = head.base64_to_mat(b['restored_b64'], is_gray=True)
            diff = np.abs(ra.astype(np.int16) - rb.astype(np.int16))
            rows.append({'sample': path.name, 'filterType': filter_type,
                         'notchApplied': b['frequency_details'].get('notchApplied'),
                         'restoredPixelEqual': bool((diff == 0).all()), 'changedPixelCount': int(np.count_nonzero(diff)),
                         'totalPixelCount': int(diff.size), 'maxAbsDiff': int(diff.max())})
    result = {'derivedAt': datetime.now(timezone.utc).isoformat(), 'baseCommit': args.base_commit,
              'headCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'rows': rows}
    out = ROOT / 'experiments/derived'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'e05_processing_impact.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(rows, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
