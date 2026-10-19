"""C-06 / C-08: the governance check is read-only and reports differences without changing anything."""
import hashlib
import json
import sqlite3
import subprocess

import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'check_catalog_governance.py'


def run(*args):
    result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert result.returncode in (0, 1), result.stderr
    return result.returncode, json.loads(result.stdout)


def make_db(path):
    catalogue = json.loads((ROOT / 'data/catalog/steles28.json').read_text(encoding='utf-8'))
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE steles (id TEXT PRIMARY KEY, title TEXT, author TEXT, gis_lng REAL, gis_lat REAL)')
        conn.execute('CREATE TABLE museum_catalog_status (id TEXT PRIMARY KEY, status TEXT NOT NULL, recommended_id TEXT)')
        for record in catalogue[1:]:
            conn.execute('INSERT INTO steles VALUES (?,?,?,?,?)', (record['id'], record['title'], record['author'], None, None))
        conn.execute("UPDATE steles SET author='未核定' WHERE id='tang_02_jiucheng'")
        conn.execute("INSERT INTO steles VALUES ('qing_01_shilang','旧记录','x',120.2,23.0)")
        conn.execute("INSERT INTO museum_catalog_status VALUES ('qing_01_shilang','retired','qing_01_qianlong_heart_sutra')")


def test_reports_differences_and_never_writes(tmp_path):
    db = tmp_path / 'fixture.sqlite'
    make_db(db)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    code, report = run('--db', str(db), '--strict')
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == ['fixture.sqlite']  # no -wal/-journal created
    assert code == 1 and report['readOnly'] is True
    sql = report['C08_sqlite']
    assert sql['missingInSqlite'] == ['han_01_caoquan']
    assert sql['extraInSqlite'][0]['id'] == 'qing_01_shilang' and sql['extraInSqlite'][0]['retired'] is True
    assert sql['extraInSqlite'][0]['coordinatesUnsourced'] is True
    assert {'id': 'tang_02_jiucheng', 'column': 'author', 'sqlite': '未核定', 'catalogue': '魏徵',
            'catalogueVerification': 'verified'} in sql['fieldDiffs']
    # Task 0: unsourced coordinates of retired rows are reported as present but never printed.
    assert sql['extraInSqlite'][0]['coordinates'] == '已屏蔽：无来源坐标，不输出数值'
    chain = report['C06_statusChain']
    assert len(chain['records']) == 28 and all(r['sha256Match'] for r in chain['records'])


def test_missing_database_is_reported_not_created(tmp_path):
    missing = tmp_path / 'absent.sqlite'
    code, report = run('--db', str(missing), '--summary')
    assert code == 0 and report['C08_sqliteAvailable'] is False and not missing.exists()


def test_cross_source_differences_match_retrieval_conflicts():
    _code, report = run('--db', str(ROOT / 'no-such.sqlite'))
    pairs = {(d['id'], d['field']) for d in report['C05_crossSource']}
    assert pairs == {('tang_01_duobao', 'physicalCollectionInstitution'), ('tang_01_duobao', 'rubbingPeriod'),
                     ('han_01_caoquan', 'physicalCollectionInstitution')}


def test_report_never_prints_unsourced_coordinates(tmp_path):
    db = tmp_path / 'fixture.sqlite'
    make_db(db)
    result = subprocess.run([sys.executable, str(SCRIPT), '--db', str(db)], cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    assert '120.2' not in result.stdout and '23.0' not in result.stdout


def test_sync_diff_operations_follow_spec_rules(tmp_path):
    db = tmp_path / 'fixture.sqlite'
    make_db(db)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    out = tmp_path / 'diff.json'
    code, written = run('--db', str(db), '--emit-sync-diff', str(out))
    assert code == 0 and hashlib.sha256(db.read_bytes()).hexdigest() == before
    diff = json.loads(out.read_text(encoding='utf-8'))
    assert diff['basis']['sqliteSha256'] == before
    ops = {(o['op'], o['id'], o.get('column')) for o in diff['operations']}
    assert ('update', 'tang_02_jiucheng', 'author') in ops
    assert ('set_null', 'qing_01_shilang', None) in ops and ('keep_row', 'qing_01_shilang', None) in ops
    assert ('insert_from_catalogue', 'han_01_caoquan', None) in ops
    assert not any(o['op'] == 'delete' for o in diff['operations'])
    assert '120.2' not in out.read_text(encoding='utf-8')
    code, check = run('--db', str(db), '--check-sync-diff', str(out))
    assert code == 0 and check['syncDiffUpToDate'] is True


def test_committed_sync_diff_is_well_formed_and_has_no_coordinates():
    path = ROOT / 'data/catalog/c08_sync_diff.json'
    text = path.read_text(encoding='utf-8')
    diff = json.loads(text)
    assert diff['item'] == 'C-08' and diff['option'] == 'A'
    assert {'sqliteSha256', 'catalogueSha256'} <= set(diff['basis'])
    assert diff['basis']['catalogueSha256'] == hashlib.sha256((ROOT / 'data/catalog/steles28.json').read_bytes()).hexdigest()
    rules = {'R1', 'R2', 'R3', 'R4', 'R5', 'R6'}
    for op in diff['operations']:
        assert op['rule'] in rules and op['op'] in ('update', 'hold', 'set_null', 'keep_row', 'insert_from_catalogue')
        if op['op'] == 'update':
            assert op['catalogueVerification'] in (None, 'verified')
    for value in ('120.202', '22.997', '117.939', '40.978', '120.161', '23.001', '120.203', '22.987', '112.241', '30.335'):
        assert value not in text


def _module():
    import importlib.util
    spec = importlib.util.spec_from_file_location('gov', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_diff_digest_is_recorded_and_recomputable():
    gov = _module()
    diff = json.loads((ROOT / 'data/catalog/c08_sync_diff.json').read_text(encoding='utf-8'))
    assert diff['diffDigestSha256'] == gov.diff_digest(diff['basis'], diff['operations'])
    assert diff['confirmation']['tokenStoredInFile'] is False
    assert 'confirmationToken' not in diff and gov.confirmation_token(diff['diffDigestSha256'], diff['basis']['sqliteSha256']) not in json.dumps(diff)


def test_confirmation_token_binds_digest_and_full_database_sha():
    gov = _module()
    diff = json.loads((ROOT / 'data/catalog/c08_sync_diff.json').read_text(encoding='utf-8'))
    digest, sqlite_sha = diff['diffDigestSha256'], diff['basis']['sqliteSha256']
    token = gov.confirmation_token(digest, sqlite_sha)
    assert len(token) == 64
    # Changing one hex digit anywhere in either input invalidates the token, including beyond the first 8/16 characters.
    for position in (0, 20, 63):
        flipped_db = sqlite_sha[:position] + ('0' if sqlite_sha[position] != '0' else '1') + sqlite_sha[position + 1:]
        assert gov.confirmation_token(digest, flipped_db) != token
    changed_ops = [dict(diff['operations'][0], to='其他值')] + diff['operations'][1:]
    assert gov.diff_digest(diff['basis'], changed_ops) != digest
    with pytest.raises(AssertionError):
        gov.confirmation_token(digest, sqlite_sha[:8])


def test_spec_uses_full_sha_token_rule():
    spec = (ROOT / 'docs/product-upgrade/C08_SYNC_SPEC.md').read_text(encoding='utf-8')
    assert '前 8 位' not in spec and '不截断' in spec and 'diffDigestSha256' in spec
