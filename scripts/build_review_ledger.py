"""Build the C-06 review ledger (option A, decided by the user via Green on 2026-10-19).

The ledger sits beside the catalogue and the 28 evidence files and changes neither.
For each work it records two separate states:
  - catalogue approval: steles28.json sourceVerification.status (approved_by_user), whose only
    basis is the one-sentence approval in review_manifest.json;
  - evidence review: processing.human_review_status in the evidence file (third-round review pending).
Reviewer, date and approval scope are left empty for the user to fill in. They are never invented here,
and values already filled in the ledger are preserved when it is rebuilt.

Usage:
  python scripts/build_review_ledger.py          # write data/catalog/review_ledger.json and the web copy
  python scripts/build_review_ledger.py --check  # exit 1 if either file is out of date
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data' / 'catalog'
OUTPUTS = (CATALOG / 'review_ledger.json', ROOT / 'apps' / 'web' / 'src' / 'data' / 'reviewLedger.json')
PENDING_FILL = '待用户填写'
APPROVAL_FIELDS = ('approvedBy', 'approvedAt', 'approvalScope')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def evidence_label(status):
    if not status:
        return '证据复核状态缺失'
    if str(status).startswith('pending_third_round'):
        return '证据待第三轮复核'
    return f'证据复核状态：{status}'


def _claims_of(obj):
    if isinstance(obj, dict):
        if 'claimId' in obj:
            yield obj
        for value in obj.values():
            yield from _claims_of(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _claims_of(value)


def content_flags(stele_id):
    """reviewFlags from data/catalog/claims/<id>.json, passed through verbatim for the UI badges."""
    path = CATALOG / 'claims' / f'{stele_id}.json'
    if not path.exists():
        return []
    return [{'flag': flag, 'claimId': claim['claimId'], 'status': claim['status'], 'evidenceLevel': claim['evidenceLevel'],
             'file': f'data/catalog/claims/{stele_id}.json'}
            for claim in _claims_of(load(path)) for flag in claim.get('reviewFlags', [])]


def build(previous=None):
    kept = {r['id']: r.get('userApproval') or {} for r in (previous or {}).get('records', [])}
    manifest = load(CATALOG / 'review_manifest.json')
    records = []
    for item in load(CATALOG / 'steles28.json'):
        sv = item.get('sourceVerification') or {}
        evidence_file = sv.get('evidenceFile') or f'data/catalog/evidence/{item["id"]}.json'
        evidence = load(ROOT / evidence_file)
        processing = evidence.get('processing') or {}
        meta = evidence.get('reviewedMetadata') or {}
        old = kept.get(item['id'], {})
        user = {field: old.get(field) for field in APPROVAL_FIELDS}
        user['status'] = 'filled_by_user' if all(user[f] for f in APPROVAL_FIELDS) else PENDING_FILL
        records.append({
            'id': item['id'], 'title': item['title'],
            'catalogueApproval': {'status': sv.get('status'), 'field': 'data/catalog/steles28.json#sourceVerification.status',
                                  'label': '已批准（用户确认可用于项目）' if sv.get('status') == 'approved_by_user' else str(sv.get('status'))},
            'evidenceReview': {'humanReviewStatus': processing.get('human_review_status'),
                               'qualityStatus': processing.get('quality_status') or meta.get('quality_status'),
                               'candidateStatus': meta.get('candidate_status'), 'evidenceFile': evidence_file,
                               'label': evidence_label(processing.get('human_review_status'))},
            'sourceSha256': sv.get('sourceSha256'),
            'sourceSha256MatchesEvidence': bool(sv.get('sourceSha256')) and sv.get('sourceSha256') == meta.get('source_sha256'),
            'userApproval': user,
            'contentFlags': content_flags(item['id']),
        })
    return {
        'schemaVersion': 1,
        'purpose': 'C-06 复核台账：并列记录“目录已批准”和“证据复核”两个状态，不改原目录和 28 份证据文件',
        'decision': {'item': 'C-06', 'option': 'A', 'decidedBy': '用户（经 Green 传达）', 'recordedAt': '2026-10-19 12:35 Asia/Shanghai',
                     'recordedBy': 'RM-金石史料'},
        'manifestBasis': {'file': 'data/catalog/review_manifest.json', 'approval': manifest.get('approval'), 'count': manifest.get('count'),
                          'reviewerOrDateRecorded': any(k in manifest for k in ('reviewer', 'reviewedBy', 'approvedAt', 'date'))},
        'userApprovalFields': {'approvedBy': '批准人', 'approvedAt': '批准日期（Asia/Shanghai）',
                               'approvalScope': '批准范围，例如：影像可用 / 许可 / 著录字段',
                               'rule': '只能由用户本人填写，Agent 不代填；三项都填后 status 变为 filled_by_user'},
        'records': records,
    }


def render(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    previous = load(OUTPUTS[0]) if OUTPUTS[0].is_file() else None
    text = render(build(previous))
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p in OUTPUTS if not p.is_file() or p.read_text(encoding='utf-8') != text]
        print('review ledger up to date' if not stale else 'stale: ' + ', '.join(stale))
        return 1 if stale else 0
    for path in OUTPUTS:
        path.write_text(text, encoding='utf-8', newline='\n')
    print(f'wrote {len(load(OUTPUTS[0])["records"])} records')
    return 0


if __name__ == '__main__':
    sys.exit(main())
