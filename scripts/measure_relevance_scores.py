"""Measure the BM25 score distribution used to calibrate evidence_retrieval.WEAK_BM25_THRESHOLD.

Runs the 25 audit probes (tests/test_retrieval_regression_25.py) and the unrelated queries
(tests/test_relevance_threshold.py) with the filter disabled, on a temporary index. Read-only for the repo.
Usage: python scripts/measure_relevance_scores.py
"""
import json
import statistics
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
import evidence_retrieval as er  # noqa: E402
from test_relevance_threshold import UNRELATED  # noqa: E402
from test_retrieval_regression_25 import AUDIT_25, EXPLICIT_DEMO  # noqa: E402


def _stats(values):
    values = sorted(values)
    if not values:
        return {'n': 0}
    return {'n': len(values), 'min': round(values[0], 3), 'p50': round(statistics.median(values), 3),
            'p90': round(values[int(0.9 * (len(values) - 1))], 3), 'max': round(values[-1], 3)}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    er.INDEX = Path(tempfile.mkdtemp()) / 'evidence.sqlite'
    er.WEAK_BM25_THRESHOLD = float('-inf')
    buckets = {'audit_answered_entityMatched': [], 'audit_answered_keywordOnly': [],
               'audit_insufficient_entityMatched': [], 'audit_insufficient_keywordOnly': [], 'unrelated_all': []}
    for question, scope, *_ in AUDIT_25:
        result = er.query(question, scope, include_demo=question in EXPLICIT_DEMO)
        kind = 'insufficient' if result['status'] == 'insufficient_evidence' else 'answered'
        for e in result['evidence']:
            buckets[f"audit_{kind}_{'entityMatched' if e['entityMatched'] else 'keywordOnly'}"].append(e['bm25Score'])
    for question in UNRELATED:
        buckets['unrelated_all'].extend(e['bm25Score'] for e in er.query(question)['evidence'])
    print(json.dumps({'algorithm': er.VERSION, 'auditQueries': len(AUDIT_25), 'unrelatedQueries': len(UNRELATED),
                      'bm25': {k: _stats(v) for k, v in buckets.items()}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
