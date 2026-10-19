"""Read-only governance check for audit items C-06 (verification status chain) and C-08 (SQLite vs catalogue).

Never writes: SQLite is opened with URI mode=ro, JSON files are only read, and the
report goes to stdout. Decisions about what to change belong to Green and the user;
see docs/product-upgrade/JINSHI_GOVERNANCE_PLAN.md.

Coordinates of rows without a coordinate source are never printed (task 0 / C-08): the
report only says that they are present.

Usage:
  python scripts/check_catalog_governance.py [--db PATH] [--summary] [--strict] [--emit-sync-diff PATH | --check-sync-diff PATH]
  --db               SQLite file to compare (default: data/rubbingmind.sqlite under the repo root)
  --summary          print counts only
  --strict           exit 1 when any difference is found
  --emit-sync-diff   write the C-08 machine-readable sync diff (see docs/product-upgrade/C08_SYNC_SPEC.md)
                     to PATH; the SQLite file is still opened read-only
  --check-sync-diff  exit 1 if PATH differs from the diff the current SQLite and catalogue would produce
"""
import argparse
import hashlib
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data' / 'catalog'
# SQLite column -> catalogue field. Only fields with a one-to-one meaning are compared.
COLUMN_MAP = {'title': 'title', 'dynasty': 'dynasty', 'dynasty_value': 'dynasty_value', 'author': 'author',
              'script_type': 'scriptType', 'museum': 'rubbingCollectionInstitution', 'source_url': 'sourceUrl',
              'license': 'license', 'attribution': 'attribution'}
UNKNOWN = ('未核定', '未核实', '待考', '年代待考', '未确认', '待核')
REDACTED = '已屏蔽：无来源坐标，不输出数值'
CROSS = {'physicalCollectionInstitution': 'originalStoneCollection', 'rubbingPeriod': 'rubbingPeriod',
         'collectionNumber': 'collectionNumber'}


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def status_chain():
    """C-06: catalogue sourceVerification vs evidence-file review fields."""
    rows = []
    for record in load(CATALOG / 'steles28.json'):
        sv = record.get('sourceVerification') or {}
        evidence_path = ROOT / (sv.get('evidenceFile') or f'data/catalog/evidence/{record["id"]}.json')
        evidence = load(evidence_path) if evidence_path.is_file() else {}
        processing = evidence.get('processing') or {}
        meta = evidence.get('reviewedMetadata') or {}
        row = {'id': record['id'], 'catalogueStatus': sv.get('status'),
               'evidenceHumanReviewStatus': processing.get('human_review_status'),
               'evidenceQualityStatus': processing.get('quality_status') or meta.get('quality_status'),
               'evidenceCandidateStatus': meta.get('candidate_status'),
               'sha256Match': bool(sv.get('sourceSha256')) and sv.get('sourceSha256') == meta.get('source_sha256'),
               'evidenceFile': str(evidence_path.relative_to(ROOT)) if evidence_path.is_file() else None}
        row['inconsistent'] = (row['catalogueStatus'] == 'approved_by_user' and
                               str(row['evidenceHumanReviewStatus'] or '').startswith('pending')) or not row['sha256Match']
        rows.append(row)
    manifest = load(CATALOG / 'review_manifest.json')
    return {'records': rows, 'inconsistentCount': sum(r['inconsistent'] for r in rows),
            'manifestApproval': manifest.get('approval'), 'manifestCount': manifest.get('count'),
            'manifestHasReviewerOrDate': any(k in manifest for k in ('reviewer', 'reviewedBy', 'approvedAt', 'date'))}


def sqlite_diff(db_path):
    """C-08: compare the steles table with the reviewed catalogue, read-only."""
    if not Path(db_path).is_file():
        return {'db': str(db_path), 'available': False}
    uri = Path(db_path).resolve().as_uri() + '?mode=ro'
    catalogue = {r['id']: r for r in load(CATALOG / 'steles28.json')}
    retired = {r['oldId']: r['newId'] for r in load(CATALOG / 'replacement_mapping.json')}
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        rows = {r['id']: dict(r) for r in conn.execute('SELECT * FROM steles')}
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        status_rows = ({r['id']: dict(r) for r in conn.execute('SELECT * FROM museum_catalog_status')}
                       if 'museum_catalog_status' in tables else {})
    field_diffs = []
    for sid in sorted(set(rows) & set(catalogue)):
        for column, field in COLUMN_MAP.items():
            db_value, cat_value = rows[sid].get(column), catalogue[sid].get(field)
            if column in rows[sid] and (db_value or '') != (cat_value or ''):
                field_diffs.append({'id': sid, 'column': column, 'sqlite': db_value, 'catalogue': cat_value,
                                    'catalogueVerification': catalogue[sid].get(field + 'Verification')})
        if rows[sid].get('gis_lng') is not None or rows[sid].get('gis_lat') is not None:
            field_diffs.append({'id': sid, 'column': 'gis_lng/gis_lat', 'sqlite': REDACTED,
                                'catalogue': 'catalog.py 不输出坐标（gis_coords=[]），目录无坐标来源字段'})
    extra = []
    for sid in sorted(set(rows) - set(catalogue)):
        extra.append({'id': sid, 'title': rows[sid].get('title'), 'retired': sid in retired, 'recommendedId': retired.get(sid),
                      'catalogStatus': status_rows.get(sid, {}).get('status'),
                      'coordinates': REDACTED if rows[sid].get('gis_lng') is not None or rows[sid].get('gis_lat') is not None else None,
                      'coordinatesUnsourced': rows[sid].get('gis_lng') is not None or rows[sid].get('gis_lat') is not None})
    return {'db': str(db_path), 'available': True, 'sqliteRows': len(rows), 'catalogueRecords': len(catalogue),
            'missingInSqlite': sorted(set(catalogue) - set(rows)), 'extraInSqlite': extra, 'fieldDiffs': field_diffs,
            'statusTableRows': len(status_rows)}


def cross_source():
    """Catalogue vs curated history documents for the two works that have both (see C-05)."""
    catalogue = {r['id']: r for r in load(CATALOG / 'steles28.json')}
    out = []
    for rubbing, key in (('tang_01_duobao', 'tang-duobao'), ('han_01_caoquan', 'han-caoquan')):
        history = load(ROOT / 'data' / 'history' / f'{key}.json')
        for field, hfield in CROSS.items():
            a, b = catalogue[rubbing].get(field), history.get(hfield)
            def norm(v):
                text = str(v or '').replace('購', '购').replace('贈', '赠').replace('（拓本）', '').strip()
                return '未核定' if not text or text.startswith(UNKNOWN) else text
            if norm(a) != norm(b):
                out.append({'id': rubbing, 'field': field, 'catalogue': a, 'history': b, 'historyFile': f'data/history/{key}.json'})
    return out


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sync_diff(sql):
    """C-08 option A: operations the backend sync script should preview, back up and (after user confirmation) apply."""
    ops = []
    for diff in sql['fieldDiffs']:
        if diff['column'] == 'gis_lng/gis_lat':
            ops.append({'op': 'set_null', 'table': 'steles', 'id': diff['id'], 'columns': ['gis_lng', 'gis_lat'],
                        'from': REDACTED, 'to': None, 'rule': 'R4'})
        else:
            verification = diff.get('catalogueVerification')
            if verification not in (None, 'verified'):
                # R2: never write a catalogue value whose own verification is not "verified" over SQLite.
                ops.append({'op': 'hold', 'table': 'steles', 'id': diff['id'], 'column': diff['column'], 'from': diff['sqlite'],
                            'catalogue': diff['catalogue'], 'catalogueVerification': verification, 'rule': 'R2'})
                continue
            ops.append({'op': 'update', 'table': 'steles', 'id': diff['id'], 'column': diff['column'],
                        'from': diff['sqlite'], 'to': diff['catalogue'], 'catalogueVerification': verification, 'rule': 'R1'})
    for extra in sql['extraInSqlite']:
        if extra['retired']:
            ops.append({'op': 'keep_row', 'table': 'steles', 'id': extra['id'], 'reason': 'museum_catalog_status=retired；保留历史行，不删除',
                        'rule': 'R3'})
            if extra['coordinatesUnsourced']:
                ops.append({'op': 'set_null', 'table': 'steles', 'id': extra['id'], 'columns': ['gis_lng', 'gis_lat'],
                            'from': REDACTED, 'to': None, 'rule': 'R3'})
        else:
            ops.append({'op': 'keep_row', 'table': 'steles', 'id': extra['id'], 'reason': '不在目录且未下架（如用户记录）；不同步', 'rule': 'R5'})
    for sid in sql['missingInSqlite']:
        ops.append({'op': 'insert_from_catalogue', 'table': 'steles', 'id': sid, 'rule': 'R6'})
    return {
        'schemaVersion': 1,
        'item': 'C-08', 'option': 'A', 'decidedBy': '用户（经 Green 传达）', 'spec': 'docs/product-upgrade/C08_SYNC_SPEC.md',
        'generator': 'scripts/check_catalog_governance.py --emit-sync-diff（SQLite mode=ro）',
        'basis': {'sqliteSha256': sha256_file(sql['db']), 'catalogueFile': 'data/catalog/steles28.json',
                  'catalogueSha256': sha256_file(CATALOG / 'steles28.json'), 'sqliteRows': sql['sqliteRows'],
                  'catalogueRecords': sql['catalogueRecords']},
        'precondition': '执行前必须重新计算 basis 中两个 SHA-256；任一不一致则中止，并重新生成本文件',
        'operations': ops,
        'counts': {op: sum(o['op'] == op for o in ops) for op in ('update', 'hold', 'set_null', 'keep_row', 'insert_from_catalogue')},
    }


def render(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--db', default=str(ROOT / 'data' / 'rubbingmind.sqlite'))
    parser.add_argument('--summary', action='store_true')
    parser.add_argument('--strict', action='store_true')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--emit-sync-diff', metavar='PATH')
    group.add_argument('--check-sync-diff', metavar='PATH')
    args = parser.parse_args()
    report = {'readOnly': True, 'C06_statusChain': status_chain(), 'C08_sqlite': sqlite_diff(args.db), 'C05_crossSource': cross_source()}
    sql = report['C08_sqlite']
    summary = {'C06_inconsistentRecords': report['C06_statusChain']['inconsistentCount'],
               'C06_manifestHasReviewerOrDate': report['C06_statusChain']['manifestHasReviewerOrDate'],
               'C08_sqliteAvailable': sql['available'],
               'C08_missingInSqlite': len(sql.get('missingInSqlite', [])), 'C08_extraInSqlite': len(sql.get('extraInSqlite', [])),
               'C08_extraWithCoordinates': sum(e['coordinatesUnsourced'] for e in sql.get('extraInSqlite', [])),
               'C08_fieldDiffs': len(sql.get('fieldDiffs', [])), 'C05_crossSourceDiffs': len(report['C05_crossSource'])}
    report['summary'] = summary
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')  # stable UTF-8 JSON on Windows consoles (cp936) too
    if args.emit_sync_diff or args.check_sync_diff:
        if not sql['available']:
            print(json.dumps({'error': 'SQLite 不存在，无法生成同步差异', 'db': sql['db']}, ensure_ascii=False))
            return 2
        text = render(sync_diff(sql))
        if args.emit_sync_diff:
            Path(args.emit_sync_diff).write_text(text, encoding='utf-8', newline='\n')
            print(json.dumps({'wrote': args.emit_sync_diff, **json.loads(text)['counts']}, ensure_ascii=False))
            return 0
        current = Path(args.check_sync_diff)
        same = current.is_file() and current.read_text(encoding='utf-8') == text
        print(json.dumps({'syncDiffUpToDate': same, 'file': args.check_sync_diff}, ensure_ascii=False))
        return 0 if same else 1
    print(json.dumps(summary if args.summary else report, ensure_ascii=False, indent=2))
    differences = summary['C06_inconsistentRecords'] + summary['C08_missingInSqlite'] + summary['C08_extraInSqlite'] + summary['C08_fieldDiffs'] + summary['C05_crossSourceDiffs']
    return 1 if args.strict and differences else 0


if __name__ == '__main__':
    sys.exit(main())
