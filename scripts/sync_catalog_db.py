"""C-08 option A: sync the SQLite `steles` table to the reviewed catalogue (steles28.json).

Rules and the diff format follow docs/product-upgrade/C08_SYNC_SPEC.md and
JINSHI_GOVERNANCE_PLAN.md (RM-金石史料, agent/jinshi). Safety contract (Green 2026-10-19):

* Default is a DRY RUN: the database is opened with URI mode=ro and nothing is written.
  It prints the operations, the basis SHA-256s and a confirmation token
  (first 16 hex chars of SHA-256 over the canonical diff summary: basis + operations).
* Writing needs BOTH --apply and confirmation: --confirm <token> (must equal the token of
  the diff recomputed at apply time) or typing the token at an interactive prompt.
  --apply also requires an explicit --db (no default target).
* Before writing: the DB is copied to <db>.<YYYYMMDD-HHMMSS>.bak (Asia/Shanghai), the copy's
  SHA-256 is verified against the original and recorded in <bak>.json.
* Operations run in one transaction; `hold` is never executed; nothing outside the list.
* Post-check: the recomputed diff must have no update/set_null/insert left.
* --rollback <bak> restores a backup after verifying its recorded SHA-256.
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


def confirmation_token(diff: dict) -> str:
    canonical = json.dumps({'basis': diff['basis'], 'operations': diff['operations']}, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]


def check_external_diff(diff: dict, path: Path) -> None:
    """A diff list produced by check_catalog_governance.py must describe exactly the current state."""
    external = _load(path)
    if external.get('basis', {}).get('sqliteSha256') != diff['basis']['sqliteSha256'] or \
            external.get('basis', {}).get('catalogueSha256') != diff['basis']['catalogueSha256']:
        raise SystemExit('差异清单的 basis SHA-256 与当前 SQLite/目录不一致：请重新生成差异清单（中止，未写入）')
    if external.get('operations') != diff['operations']:
        raise SystemExit('差异清单的操作与本脚本按同一规则重算的结果不同（中止，未写入）')


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


def apply(db: Path, confirm: str | None, catalog_dir: Path = CATALOG, external: Path | None = None, interactive=None) -> dict:
    for suffix in ('-wal', '-journal'):
        if db.with_name(db.name + suffix).exists():
            raise SystemExit(f'检测到 {db.name}{suffix}：数据库可能正被使用，请先停止后端（中止，未写入）')
    diff = compute_diff(db, catalog_dir)
    if external:
        check_external_diff(diff, external)
    token = confirmation_token(diff)
    if confirm is None:
        interactive = sys.stdin.isatty() if interactive is None else interactive
        if not interactive:
            raise SystemExit('需要 --confirm <令牌> 或交互确认（中止，未写入）')
        print(render(diff, token))
        confirm = input(f'确认写入 {db}？请输入令牌 {token}：').strip()
    if confirm != token:
        raise SystemExit('确认令牌与当前差异不一致：差异可能已变化，请重新 dry-run（中止，未写入）')
    if not any(op['op'] in WRITE_OPS for op in diff['operations']):
        return {'applied': False, 'reason': '没有需要写入的操作', 'token': token}
    bak = _backup(db)
    _execute(db, diff, catalog_dir)
    after = compute_diff(db, catalog_dir)
    leftover = {op: after['counts'][op] for op in WRITE_OPS if after['counts'].get(op)}
    if leftover:
        raise SystemExit(f'写后复核失败，仍有 {leftover}；请用 --rollback {bak} 恢复')
    return {'applied': True, 'backup': str(bak), 'backupSha256': _load(bak.with_name(bak.name + '.json'))['sha256'],
            'beforeSha256': diff['basis']['sqliteSha256'], 'afterSha256': sha256_file(db), 'executed': diff['counts'],
            'postCheck': after['counts'], 'rollback': f'python scripts/sync_catalog_db.py --db "{db}" --rollback "{bak}"'}


def rollback(db: Path, bak: Path) -> dict:
    meta_path = bak.with_name(bak.name + '.json')
    if not bak.is_file() or not meta_path.is_file():
        raise SystemExit('备份或其记录文件不存在（中止）')
    meta = _load(meta_path)
    if sha256_file(bak) != meta['sha256']:
        raise SystemExit('备份文件 SHA-256 与记录不符，拒绝恢复')
    if Path(meta['database']).resolve() != db.resolve():
        raise SystemExit('该备份不属于指定的数据库，拒绝恢复')
    shutil.copy2(bak, db)
    restored = sha256_file(db)
    if restored != meta['sha256']:
        raise SystemExit('恢复后 SHA-256 与备份不一致')
    return {'restored': str(db), 'sha256': restored, 'from': str(bak)}


def render(diff: dict, token: str) -> str:
    lines = [f"C-08 同步预览（dry-run，SQLite 只读）", f"basis: sqlite={diff['basis']['sqliteSha256']} catalogue={diff['basis']['catalogueSha256']}",
             f"rows: sqlite={diff['basis']['sqliteRows']} catalogue={diff['basis']['catalogueRecords']}", f"counts: {diff['counts']}"]
    for op in diff['operations']:
        if op['op'] == 'update':
            lines.append(f"  [R1 update] {op['id']}.{op['column']}: {op['from']!r} -> {op['to']!r}")
        elif op['op'] == 'hold':
            lines.append(f"  [R2 hold]   {op['id']}.{op['column']}: 目录值核验状态 {op['catalogueVerification']}，不写入")
        elif op['op'] == 'set_null':
            lines.append(f"  [{op['rule']} set_null] {op['id']}.gis_lng/gis_lat: {REDACTED} -> NULL")
        elif op['op'] == 'insert_from_catalogue':
            lines.append(f"  [R6 insert] {op['id']}")
        else:
            lines.append(f"  [{op['rule']} keep_row] {op['id']}")
    lines.append(f'确认令牌: {token}   （写入需: --db <库> --apply --confirm {token}）')
    return '\n'.join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--db')
    parser.add_argument('--diff', help='可选：check_catalog_governance.py --emit-sync-diff 生成的差异清单，必须与重算结果一致')
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
    if args.apply:
        print(json.dumps(apply(db, args.confirm, external=Path(args.diff) if args.diff else None), ensure_ascii=False, indent=2))
        return 0
    diff = compute_diff(db)
    if args.diff:
        check_external_diff(diff, Path(args.diff))
    token = confirmation_token(diff)
    print(json.dumps({**diff, 'confirmationToken': token, 'dryRun': True}, ensure_ascii=False, indent=2) if args.json else render(diff, token))
    return 0


if __name__ == '__main__':
    sys.exit(main())
