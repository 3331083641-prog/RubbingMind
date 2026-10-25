"""C-08 option A: apply agent/jinshi's reviewed sync diff (data/catalog/c08_sync_diff.json) to SQLite.

Contract: docs/product-upgrade/C08_SYNC_SPEC.md (RM-金石史料, agent/jinshi@c358724) R1-R6 and the 7
acceptance conditions, plus Green 2026-10-19:

* INPUT is the diff file (`--diff`, default data/catalog/c08_sync_diff.json, generated read-only by
  check_catalog_governance.py --emit-sync-diff). Only its operations are executed. The file is validated
  (schema, op/table/column allowlist, counts) and must equal the operations recomputed by the same rules.
* Default is a DRY RUN (SQLite opened with URI mode=ro; nothing is written). It re-checks both basis
  SHA-256 (SPEC §3.2) and prints the operations and a confirmation token.
* TOKEN = first 16 hex of SHA-256("C-08|" + SHA-256(canonical {basis, operations} of the diff) + "|" +
  SHA-256(target DB file)). It is bound to BOTH the diff summary and the target DB bytes: if either
  changes, the token is void. (SPEC §3.4 proposed the first 8 hex of basis.sqliteSha256; Green's
  diff-summary rule is kept and extended with the DB SHA, see ARCHITECTURE_DECISIONS R2-5.)
* --apply needs an explicit --db and --confirm <token> or the token typed interactively. Refuses when a
  -wal/-journal file exists. Backs up to <db>.<YYYYMMDD-HHMMSS>.bak (Asia/Shanghai), verifies and records
  the backup SHA-256 in <bak>.json, then runs every operation in ONE transaction (any failure rolls back).
  `hold` and `keep_row` never write; nothing outside the list is touched; no delete, no schema change.
* Post-check (SPEC §3.6): C08_fieldDiffs == number of hold ops (0 now), C08_extraWithCoordinates == 0,
  C08_extraInSqlite unchanged (5 retired rows kept). If scripts/check_catalog_governance.py exists it is
  also run with --summary. A failed post-check restores the verified backup automatically.
* --rollback <bak> restores a backup after verifying its recorded SHA-256 (SPEC §3.7).
  RV-AI01: refuses when a -wal/-journal exists or an exclusive lock cannot be taken; backs up the
  CURRENT db bytes first (SHA recorded) before overwriting.
  RV-AI04: ALWAYS stop the backend before --apply or --rollback.
Coordinate values without a source are never printed.

Usage:
  python scripts/sync_catalog_db.py [--db PATH] [--diff c08_sync_diff.json] [--json]
  python scripts/sync_catalog_db.py --db PATH --apply [--confirm TOKEN] [--diff ...]
  python scripts/sync_catalog_db.py --db PATH --rollback PATH.bak
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data' / 'catalog'
COLUMN_MAP = {'title': 'title', 'dynasty': 'dynasty', 'dynasty_value': 'dynasty_value', 'author': 'author',
              'script_type': 'scriptType', 'museum': 'rubbingCollectionInstitution', 'source_url': 'sourceUrl',
              'license': 'license', 'attribution': 'attribution'}
REDACTED = '已屏蔽：无来源坐标，不输出数值'
SHANGHAI = timezone(timedelta(hours=8))
WRITE_OPS = ('update', 'set_null', 'insert_from_catalogue')
ALL_OPS = WRITE_OPS + ('hold', 'keep_row')
DEFAULT_DIFF = CATALOG / 'c08_sync_diff.json'
COORD_COLUMNS = ['gis_lng', 'gis_lat']
GOVERNANCE_SCRIPT = ROOT / 'scripts' / 'check_catalog_governance.py'


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _ro(db: Path):
    return closing(sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True))


def compute_diff(db: Path, catalog_dir: Path = CATALOG) -> dict:
    catalogue = {r['id']: r for r in _load(catalog_dir / 'steles28.json')}
    retired = {r['oldId'] for r in _load(catalog_dir / 'replacement_mapping.json')}
    with _ro(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = {r['id']: dict(r) for r in conn.execute('SELECT * FROM steles')}
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        status = ({r['id']: r['status'] for r in conn.execute('SELECT id, status FROM museum_catalog_status')}
                  if 'museum_catalog_status' in tables else {})
    ops = []
    for sid in sorted(set(rows) & set(catalogue)):
        for column, field in COLUMN_MAP.items():
            if column not in rows[sid]:
                continue
            db_value, cat_value = rows[sid].get(column), catalogue[sid].get(field)
            if (db_value or '') == (cat_value or ''):
                continue
            verification = catalogue[sid].get(field + 'Verification')
            if verification not in (None, 'verified'):  # R2: never promote unverified catalogue values
                ops.append({'op': 'hold', 'table': 'steles', 'id': sid, 'column': column, 'from': db_value,
                            'catalogue': cat_value, 'catalogueVerification': verification, 'rule': 'R2'})
            else:  # R1
                ops.append({'op': 'update', 'table': 'steles', 'id': sid, 'column': column, 'from': db_value,
                            'to': cat_value, 'catalogueVerification': verification, 'rule': 'R1'})
        if rows[sid].get('gis_lng') is not None or rows[sid].get('gis_lat') is not None:  # R4
            ops.append({'op': 'set_null', 'table': 'steles', 'id': sid, 'columns': ['gis_lng', 'gis_lat'],
                        'from': REDACTED, 'to': None, 'rule': 'R4'})
    for sid in sorted(set(rows) - set(catalogue)):
        is_retired = sid in retired or status.get(sid) == 'retired'
        if is_retired:  # R3
            ops.append({'op': 'keep_row', 'table': 'steles', 'id': sid, 'reason': 'museum_catalog_status=retired；保留历史行，不删除', 'rule': 'R3'})
            if rows[sid].get('gis_lng') is not None or rows[sid].get('gis_lat') is not None:
                ops.append({'op': 'set_null', 'table': 'steles', 'id': sid, 'columns': ['gis_lng', 'gis_lat'],
                            'from': REDACTED, 'to': None, 'rule': 'R3'})
        else:  # R5
            ops.append({'op': 'keep_row', 'table': 'steles', 'id': sid, 'reason': '不在目录且未下架（如用户记录）；不同步', 'rule': 'R5'})
    for sid in sorted(set(catalogue) - set(rows)):  # R6
        ops.append({'op': 'insert_from_catalogue', 'table': 'steles', 'id': sid, 'rule': 'R6'})
    basis = {'sqliteSha256': sha256_file(db), 'catalogueSha256': sha256_file(catalog_dir / 'steles28.json'),
             'sqliteRows': len(rows), 'catalogueRecords': len(catalogue)}
    counts = {op: sum(o['op'] == op for o in ops) for op in ('update', 'hold', 'set_null', 'keep_row', 'insert_from_catalogue')}
    return {'schemaVersion': 1, 'item': 'C-08', 'option': 'A', 'basis': basis, 'operations': ops, 'counts': counts}


def diff_digest(diff: dict) -> str:
    canonical = json.dumps({'basis': diff['basis'], 'operations': diff['operations']}, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


def confirmation_token(diff: dict, db_sha256: str) -> str:
    """Bound to the diff summary AND the target DB bytes; either change voids the token."""
    return hashlib.sha256(f'C-08|{diff_digest(diff)}|{db_sha256}'.encode('utf-8')).hexdigest()[:16]


def load_diff(path: Path) -> dict:
    """Read and validate the reviewed diff list (format of agent/jinshi data/catalog/c08_sync_diff.json)."""
    if not Path(path).is_file():
        raise SystemExit(f'差异清单不存在：{path}（请用 check_catalog_governance.py --emit-sync-diff 只读生成；中止，未写入）')
    diff = _load(path)
    problems = []
    if diff.get('schemaVersion') != 1 or diff.get('item') != 'C-08':
        problems.append('schemaVersion/item 不是 1 / C-08')
    basis = diff.get('basis') or {}
    if not basis.get('sqliteSha256') or not basis.get('catalogueSha256'):
        problems.append('basis 缺少 sqliteSha256 或 catalogueSha256')
    operations = diff.get('operations')
    if not isinstance(operations, list):
        problems.append('operations 不是列表')
        operations = []
    for index, op in enumerate(operations):
        kind = op.get('op')
        if kind not in ALL_OPS:
            problems.append(f'第 {index} 项操作 {kind!r} 不在允许范围（不删行、不改 schema）')
        elif op.get('table') != 'steles' or not op.get('id'):
            problems.append(f'第 {index} 项操作的表或 id 不合法')
        elif kind == 'update' and op.get('column') not in COLUMN_MAP:
            problems.append(f"第 {index} 项 update 的列 {op.get('column')!r} 不在 COLUMN_MAP")
        elif kind == 'set_null' and op.get('columns') != COORD_COLUMNS:
            problems.append(f'第 {index} 项 set_null 只能置空 gis_lng/gis_lat')
    counts = {kind: sum(o.get('op') == kind for o in operations) for kind in ('update', 'hold', 'set_null', 'keep_row', 'insert_from_catalogue')}
    if diff.get('counts') is not None and diff['counts'] != counts:
        problems.append(f"counts {diff.get('counts')} 与操作清单 {counts} 不符")
    if problems:
        raise SystemExit('差异清单校验失败：' + '；'.join(problems) + '（中止，未写入）')
    return diff


def check_preconditions(db: Path, diff: dict, catalog_dir: Path = CATALOG) -> dict:
    """SPEC §3.2: both basis SHA-256 must match; the listed operations must equal a fresh recompute."""
    current = compute_diff(db, catalog_dir)
    basis, now = diff['basis'], current['basis']
    if basis['sqliteSha256'] != now['sqliteSha256'] or basis['catalogueSha256'] != now['catalogueSha256']:
        raise SystemExit('差异清单的 basis SHA-256 与当前 SQLite/目录不一致：请重新生成差异清单（中止，未写入）')
    if diff['operations'] != current['operations']:
        raise SystemExit('差异清单的操作与按同一规则重算的结果不同（中止，未写入）')
    return current


def check_external_diff(diff: dict, path: Path) -> None:
    """Back-compat helper: the external list must describe exactly the recomputed state."""
    external = load_diff(path)
    if external['basis'].get('sqliteSha256') != diff['basis']['sqliteSha256'] or \
            external['basis'].get('catalogueSha256') != diff['basis']['catalogueSha256']:
        raise SystemExit('差异清单的 basis SHA-256 与当前 SQLite/目录不一致：请重新生成差异清单（中止，未写入）')
    if external['operations'] != diff['operations']:
        raise SystemExit('差异清单的操作与本脚本按同一规则重算的结果不同（中止，未写入）')


def governance_summary(db: Path, catalog_dir: Path = CATALOG) -> dict:
    """Same counts as check_catalog_governance.py --summary (C08_*), computed read-only."""
    catalogue = {r['id']: r for r in _load(catalog_dir / 'steles28.json')}
    with _ro(db) as conn:
        conn.row_factory = sqlite3.Row
        rows = {r['id']: dict(r) for r in conn.execute('SELECT * FROM steles')}
    field_diffs = 0
    for sid in set(rows) & set(catalogue):
        for column, field in COLUMN_MAP.items():
            if column in rows[sid] and (rows[sid].get(column) or '') != (catalogue[sid].get(field) or ''):
                field_diffs += 1
        if rows[sid].get('gis_lng') is not None or rows[sid].get('gis_lat') is not None:
            field_diffs += 1
    extra = [sid for sid in rows if sid not in catalogue]
    return {'C08_fieldDiffs': field_diffs, 'C08_extraInSqlite': len(extra),
            'C08_extraWithCoordinates': sum(rows[s].get('gis_lng') is not None or rows[s].get('gis_lat') is not None for s in extra),
            'C08_missingInSqlite': len(set(catalogue) - set(rows))}


def _external_governance_summary(db: Path):
    if not GOVERNANCE_SCRIPT.is_file():
        return None
    import subprocess
    done = subprocess.run([sys.executable, str(GOVERNANCE_SCRIPT), '--db', str(db), '--summary'], capture_output=True, text=True,
                          encoding='utf-8', cwd=str(ROOT))
    try:
        return json.loads(done.stdout)
    except ValueError:
        return {'error': f'check_catalog_governance.py 输出无法解析（exit {done.returncode}）'}


def _backup(db: Path) -> Path:
    stamp = datetime.now(SHANGHAI).strftime('%Y%m%d-%H%M%S')
    bak = db.with_name(f'{db.name}.{stamp}.bak')
    if bak.exists():
        raise SystemExit(f'备份文件已存在：{bak}（中止，未写入）')
    original = sha256_file(db)
    shutil.copy2(db, bak)
    copied = sha256_file(bak)
    if copied != original:
        bak.unlink()
        raise SystemExit('备份 SHA-256 与原库不一致（中止，未写入）')
    meta = {'database': str(db), 'backup': str(bak), 'sha256': copied, 'createdAt': datetime.now(SHANGHAI).isoformat()}
    bak.with_name(bak.name + '.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return bak


def _execute(db: Path, diff: dict, catalog_dir: Path) -> None:
    catalogue = {r['id']: r for r in _load(catalog_dir / 'steles28.json')}
    conn = sqlite3.connect(db, isolation_level=None)
    try:
        conn.execute('BEGIN IMMEDIATE')
        for op in diff['operations']:
            if op['op'] == 'update':
                if op['column'] not in COLUMN_MAP:
                    raise ValueError(f"非法列 {op['column']}")
                cur = conn.execute(f"UPDATE steles SET {op['column']}=? WHERE id=?", (op['to'], op['id']))
            elif op['op'] == 'set_null':
                cur = conn.execute('UPDATE steles SET gis_lng=NULL, gis_lat=NULL WHERE id=?', (op['id'],))
            elif op['op'] == 'insert_from_catalogue':
                record = catalogue[op['id']]
                columns = ['id'] + list(COLUMN_MAP)
                values = [record['id']] + [record.get(field) for field in COLUMN_MAP.values()]
                cur = conn.execute(f"INSERT INTO steles ({','.join(columns)}) VALUES ({','.join('?' * len(columns))})", values)
            else:
                continue  # keep_row and hold never write
            if cur.rowcount != 1:
                raise RuntimeError(f"操作影响 {cur.rowcount} 行，预期 1 行：{op['op']} {op['id']}")
        conn.execute('COMMIT')
    except Exception:
        conn.execute('ROLLBACK')
        raise
    finally:
        conn.close()


def _restore(db: Path, bak: Path) -> None:
    shutil.copy2(bak, db)
    if sha256_file(db) != _load(bak.with_name(bak.name + '.json'))['sha256']:
        raise SystemExit(f'自动恢复后 SHA-256 与备份不一致，请人工处理：{bak}')


def apply(db: Path, confirm: str | None, catalog_dir: Path = CATALOG, diff_path: Path | None = None, interactive=None) -> dict:
    _assert_db_idle(db)  # RV-AI01 / RV-AI04: stop the backend before apply
    diff = load_diff(diff_path or DEFAULT_DIFF)
    token = confirmation_token(diff, sha256_file(db))
    if confirm is None:
        interactive = sys.stdin.isatty() if interactive is None else interactive
        if not interactive:
            raise SystemExit('需要 --confirm <令牌> 或交互确认（中止，未写入）')
        check_preconditions(db, diff, catalog_dir)
        print(render(diff, token, governance_summary(db, catalog_dir)))
        confirm = input(f'确认写入 {db}？请输入令牌 {token}：').strip()
    if confirm != token:
        raise SystemExit('确认令牌无效：差异清单或目标库已变化（令牌同时绑定差异摘要哈希与目标库 SHA-256），请重新 dry-run（中止，未写入）')
    check_preconditions(db, diff, catalog_dir)
    if not any(op['op'] in WRITE_OPS for op in diff['operations']):
        return {'applied': False, 'reason': '没有需要写入的操作', 'token': token}
    before = governance_summary(db, catalog_dir)
    bak = _backup(db)
    _execute(db, diff, catalog_dir)
    after = governance_summary(db, catalog_dir)
    expected = {'C08_fieldDiffs': diff['counts']['hold'] if diff.get('counts') else sum(o['op'] == 'hold' for o in diff['operations']),
                'C08_extraWithCoordinates': 0, 'C08_extraInSqlite': before['C08_extraInSqlite']}
    external = _external_governance_summary(db)
    failures = {key: after[key] for key, value in expected.items() if after[key] != value}
    if external is not None:
        failures.update({f'external:{key}': external.get(key) for key, value in expected.items() if external.get(key) != value})
    if failures:
        _restore(db, bak)
        raise SystemExit(f'写后复核失败 {failures}（预期 {expected}）；已从备份自动恢复：{bak}')
    return {'applied': True, 'backup': str(bak), 'backupSha256': _load(bak.with_name(bak.name + '.json'))['sha256'],
            'beforeSha256': diff['basis']['sqliteSha256'], 'afterSha256': sha256_file(db), 'executed': diff['counts'],
            'postCheck': after, 'postCheckExpected': expected, 'externalGovernanceSummary': external,
            'rollback': f'python scripts/sync_catalog_db.py --db "{db}" --rollback "{bak}"'}


def _assert_db_idle(db: Path) -> None:
    """RV-AI01: refuse to write/restore when the DB looks in use."""
    for suffix in ('-wal', '-journal'):
        if db.with_name(db.name + suffix).exists():
            raise SystemExit(f'检测到 {db.name}{suffix}：数据库可能正被使用，请先停止后端（中止，未写入）')
    # Try an exclusive lock via BEGIN EXCLUSIVE; fails if another connection holds a lock.
    try:
        conn = sqlite3.connect(db, timeout=0.1, isolation_level=None)
        try:
            conn.execute('BEGIN EXCLUSIVE')
            conn.execute('ROLLBACK')
        finally:
            conn.close()
    except sqlite3.OperationalError as exc:
        raise SystemExit(f'无法取得数据库排他锁（{exc}）：请先停止后端（中止，未写入）')


def rollback(db: Path, bak: Path) -> dict:
    """Restore a verified backup. RV-AI01: idle check + pre-rollback backup of current bytes."""
    meta_path = bak.with_name(bak.name + '.json')
    if not bak.is_file() or not meta_path.is_file():
        raise SystemExit('备份或其记录文件不存在（中止）')
    meta = _load(meta_path)
    if sha256_file(bak) != meta['sha256']:
        raise SystemExit('备份文件 SHA-256 与记录不符，拒绝恢复')
    if Path(meta['database']).resolve() != db.resolve():
        raise SystemExit('该备份不属于指定的数据库，拒绝恢复')
    _assert_db_idle(db)
    pre = _backup(db)  # backup of CURRENT state before overwrite
    shutil.copy2(bak, db)
    restored = sha256_file(db)
    if restored != meta['sha256']:
        raise SystemExit('恢复后 SHA-256 与备份不一致')
    return {'restored': str(db), 'sha256': restored, 'from': str(bak),
            'preRollbackBackup': str(pre), 'preRollbackSha256': _load(pre.with_name(pre.name + '.json'))['sha256']}


def render(diff: dict, token: str, summary: dict | None = None) -> str:
    lines = ['C-08 同步预览（dry-run，SQLite 只读 mode=ro）', f"差异清单 basis: sqlite={diff['basis']['sqliteSha256']} catalogue={diff['basis']['catalogueSha256']}",
             f"前置校验：basis 两个 SHA-256 与当前一致；操作清单与重算一致", f"counts: {diff.get('counts')}"]
    if summary:
        lines.append(f'当前治理计数: {summary}')
    for op in diff['operations']:
        if op['op'] == 'update':
            lines.append(f"  [R1 update] {op['id']}.{op['column']}: {op['from']!r} -> {op['to']!r}")
        elif op['op'] == 'hold':
            lines.append(f"  [R2 hold]   {op['id']}.{op['column']}: 目录值核验状态 {op.get('catalogueVerification')}，不写入")
        elif op['op'] == 'set_null':
            lines.append(f"  [{op['rule']} set_null] {op['id']}.gis_lng/gis_lat: {REDACTED} -> NULL")
        elif op['op'] == 'insert_from_catalogue':
            lines.append(f"  [R6 insert] {op['id']}")
        else:
            lines.append(f"  [{op['rule']} keep_row] {op['id']}")
    lines.append(f'差异摘要哈希: {diff_digest(diff)}')
    lines.append(f'确认令牌: {token}   （绑定差异摘要与目标库 SHA-256；写入需: --db <库> --apply --confirm {token}）')
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0],
        epilog='RV-AI04: 执行 --apply 或 --rollback 之前必须先停止后端（释放 SQLite 连接）。', formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--db')
    parser.add_argument('--diff', help='差异清单（默认 data/catalog/c08_sync_diff.json，由 check_catalog_governance.py --emit-sync-diff 生成）')
    parser.add_argument('--json', action='store_true', help='dry-run 以 JSON 输出')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--rollback', metavar='BAK')
    parser.add_argument('--confirm')
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if (args.apply or args.rollback) and not args.db:
        raise SystemExit('--apply/--rollback 必须显式给出 --db')
    db = Path(args.db) if args.db else ROOT / 'data' / 'rubbingmind.sqlite'
    if not db.is_file():
        raise SystemExit(f'数据库不存在：{db}')
    if args.rollback:
        print(json.dumps(rollback(db, Path(args.rollback)), ensure_ascii=False, indent=2))
        return 0
    diff_path = Path(args.diff) if args.diff else DEFAULT_DIFF
    if args.apply:
        print(json.dumps(apply(db, args.confirm, diff_path=diff_path), ensure_ascii=False, indent=2))
        return 0
    diff = load_diff(diff_path)
    check_preconditions(db, diff)
    token = confirmation_token(diff, sha256_file(db))
    summary = governance_summary(db)
    if args.json:
        print(json.dumps({**diff, 'diffFile': str(diff_path), 'diffDigest': diff_digest(diff), 'targetSha256': sha256_file(db),
                          'confirmationToken': token, 'governanceSummary': summary, 'dryRun': True}, ensure_ascii=False, indent=2))
    else:
        print(render(diff, token, summary))
    return 0


if __name__ == '__main__':
    sys.exit(main())
