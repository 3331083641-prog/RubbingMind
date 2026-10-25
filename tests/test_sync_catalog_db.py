"""C-08 sync script: dry-run never writes; apply needs the token; rollback restores the exact bytes."""
import hashlib
import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

from catalog import load

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_catalog_db', ROOT / 'scripts' / 'sync_catalog_db.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def _sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture
def db(tmp_path):
    path = tmp_path / 'copy.sqlite'
    with sqlite3.connect(path) as conn:
        conn.execute('CREATE TABLE steles (id TEXT PRIMARY KEY, title TEXT NOT NULL, dynasty TEXT NOT NULL, dynasty_value TEXT NOT NULL, author TEXT, script_type TEXT, museum TEXT, source_url TEXT, license TEXT, attribution TEXT, gis_lng REAL, gis_lat REAL)')
        conn.execute('CREATE TABLE museum_catalog_status (id TEXT PRIMARY KEY, status TEXT NOT NULL, recommended_id TEXT)')
        records = load('steles28.json')
        for r in records:
            conn.execute('INSERT INTO steles VALUES (?,?,?,?,?,?,?,?,?,?,NULL,NULL)', (r['id'], r['title'], r['dynasty'], r['dynasty_value'], r.get('author'), r.get('scriptType'), r.get('rubbingCollectionInstitution'), r.get('sourceUrl'), r.get('license'), r.get('attribution')))
        verified = next(r for r in records if r.get('authorVerification') in (None, 'verified') and r.get('author') != '未核定')
        unverified = next(r for r in records if r.get('authorVerification') not in (None, 'verified'))
        conn.execute("UPDATE steles SET author='未核定' WHERE id=?", (verified['id'],))
        conn.execute("UPDATE steles SET author='某人' WHERE id=?", (unverified['id'],))
        old = load('replacement_mapping.json')[0]['oldId']
        conn.execute("INSERT INTO steles (id,title,dynasty,dynasty_value,gis_lng,gis_lat) VALUES (?,?,?,?,?,?)", (old, 't', 'd', 'v', 112.241, 30.335))
        conn.execute("INSERT INTO museum_catalog_status VALUES (?,'retired',NULL)", (old,))
    return path, verified['id'], unverified['id'], old


def _emit(path, out):
    """Stand-in for check_catalog_governance.py --emit-sync-diff: same format as agent/jinshi c08_sync_diff.json."""
    diff = sync.compute_diff(path)
    diff = {'schemaVersion': 1, 'item': 'C-08', 'option': 'A', 'decidedBy': '用户（经 Green 传达）', 'spec': 'docs/product-upgrade/C08_SYNC_SPEC.md',
            'generator': 'scripts/check_catalog_governance.py --emit-sync-diff（SQLite mode=ro）',
            'basis': {**diff['basis'], 'catalogueFile': 'data/catalog/steles28.json'},
            'precondition': '执行前必须重新计算 basis 中两个 SHA-256；任一不一致则中止，并重新生成本文件',
            'operations': diff['operations'], 'counts': diff['counts']}
    out.write_text(json.dumps(diff, ensure_ascii=False, indent=2), 'utf-8')
    return out


def _token(path, diff_file):
    return sync.confirmation_token(sync.load_diff(diff_file), _sha(path))


def test_acceptance_1_dry_run_only_previews(db, tmp_path, capsys):
    path, verified, unverified, old = db
    diff_file = _emit(path, tmp_path / 'c08_sync_diff.json')
    before = _sha(path)
    assert sync.main(['--db', str(path), '--diff', str(diff_file)]) == 0
    out = capsys.readouterr().out
    assert _sha(path) == before and not list(path.parent.glob('*.bak'))
    assert '112.241' not in out and '30.335' not in out  # unsourced coordinates never printed
    assert _token(path, diff_file) in out
    diff = sync.load_diff(diff_file)
    assert diff['counts'] == {'update': 1, 'hold': 1, 'set_null': 1, 'keep_row': 1, 'insert_from_catalogue': 0}
    assert {(o['op'], o['id']) for o in diff['operations']} >= {('update', verified), ('hold', unverified), ('set_null', old), ('keep_row', old)}


def test_acceptance_2_basis_sha_must_match(db, tmp_path):
    path = db[0]
    diff_file = _emit(path, tmp_path / 'd.json')
    data = json.loads(diff_file.read_text('utf-8'))
    data['basis']['catalogueSha256'] = '0' * 64
    diff_file.write_text(json.dumps(data, ensure_ascii=False), 'utf-8')
    with pytest.raises(SystemExit, match='basis'):
        sync.main(['--db', str(path), '--diff', str(diff_file)])


def test_diff_file_is_validated(db, tmp_path):
    path = db[0]
    diff_file = _emit(path, tmp_path / 'd.json')
    data = json.loads(diff_file.read_text('utf-8'))
    for bad in ({'op': 'delete', 'table': 'steles', 'id': 'x'}, {'op': 'update', 'table': 'steles', 'id': 'x', 'column': 'gis_lng', 'to': 1},
                {'op': 'set_null', 'table': 'steles', 'id': 'x', 'columns': ['title']}):
        broken = dict(data, operations=data['operations'] + [bad], counts=None)
        diff_file.write_text(json.dumps(broken, ensure_ascii=False), 'utf-8')
        with pytest.raises(SystemExit, match='差异清单校验失败'):
            sync.load_diff(diff_file)
    with pytest.raises(SystemExit, match='差异清单不存在'):
        sync.load_diff(tmp_path / 'missing.json')


def test_acceptance_3_to_7_apply_backup_postcheck_rollback(db, tmp_path):
    path, verified, unverified, old = db
    diff_file = _emit(path, tmp_path / 'd.json')
    original = _sha(path)
    with pytest.raises(SystemExit):
        sync.apply(path, 'wrong-token', diff_path=diff_file)
    with pytest.raises(SystemExit):
        sync.apply(path, None, diff_path=diff_file, interactive=False)
    assert _sha(path) == original and not list(path.parent.glob('*.bak'))
    result = sync.apply(path, _token(path, diff_file), diff_path=diff_file)
    bak = Path(result['backup'])
    assert bak.name.startswith('copy.sqlite.') and bak.name.endswith('.bak')  # <db>.<YYYYMMDD-HHMMSS>.bak
    assert result['backupSha256'] == original == result['beforeSha256'] == _sha(bak)
    assert result['postCheck'] == {'C08_fieldDiffs': 1, 'C08_extraInSqlite': 1, 'C08_extraWithCoordinates': 0, 'C08_missingInSqlite': 0}
    assert result['postCheckExpected']['C08_fieldDiffs'] == 1  # the one hold stays a visible difference
    with sqlite3.connect(path) as conn:
        catalogue_author = next(r['author'] for r in load('steles28.json') if r['id'] == verified)
        assert conn.execute('SELECT author FROM steles WHERE id=?', (verified,)).fetchone()[0] == catalogue_author
        assert conn.execute('SELECT author FROM steles WHERE id=?', (unverified,)).fetchone()[0] == '某人'  # hold never written
        assert conn.execute('SELECT gis_lng, gis_lat FROM steles WHERE id=?', (old,)).fetchone() == (None, None)
        assert conn.execute('SELECT COUNT(*) FROM steles WHERE id=?', (old,)).fetchone()[0] == 1  # retired row kept
        assert conn.execute('SELECT COUNT(*) FROM steles').fetchone()[0] == 29  # 28 catalogue rows + 1 retired: none deleted or added
    restored = sync.rollback(path, bak)
    assert restored['sha256'] == original == _sha(path)


def test_token_void_when_diff_summary_changes(db, tmp_path):
    path = db[0]
    diff_file = _emit(path, tmp_path / 'd.json')
    token = _token(path, diff_file)
    data = json.loads(diff_file.read_text('utf-8'))
    data['operations'] = [o for o in data['operations'] if o['op'] != 'update']
    data['counts'] = None
    diff_file.write_text(json.dumps(data, ensure_ascii=False), 'utf-8')
    assert _token(path, diff_file) != token
    with pytest.raises(SystemExit, match='确认令牌无效'):
        sync.apply(path, token, diff_path=diff_file)
    assert not list(path.parent.glob('*.bak'))


def test_token_void_when_target_db_changes(db, tmp_path):
    path = db[0]
    diff_file = _emit(path, tmp_path / 'd.json')
    token = _token(path, diff_file)
    with sqlite3.connect(path) as conn:  # any byte change of the target DB, diff file untouched
        conn.execute("UPDATE steles SET attribution='x' WHERE id=(SELECT id FROM steles LIMIT 1)")
    assert sync.confirmation_token(sync.load_diff(diff_file), _sha(path)) != token
    with pytest.raises(SystemExit, match='确认令牌无效'):
        sync.apply(path, token, diff_path=diff_file)
    assert not list(path.parent.glob('*.bak'))


def test_failed_post_check_restores_backup(db, tmp_path, monkeypatch):
    path = db[0]
    diff_file = _emit(path, tmp_path / 'd.json')
    original = _sha(path)
    real = sync.governance_summary
    calls = {'n': 0}
    def fake(db_path, catalog_dir=sync.CATALOG):
        calls['n'] += 1
        summary = real(db_path, catalog_dir)
        return {**summary, 'C08_extraWithCoordinates': 9} if calls['n'] == 2 else summary
    monkeypatch.setattr(sync, 'governance_summary', fake)
    with pytest.raises(SystemExit, match='已从备份自动恢复'):
        sync.apply(path, _token(path, diff_file), diff_path=diff_file)
    assert _sha(path) == original


def test_apply_and_rollback_need_explicit_db():
    with pytest.raises(SystemExit):
        sync.main(['--apply', '--confirm', 'x'])


def test_rollback_backs_up_current_and_refuses_when_busy(db, tmp_path):
    path = db[0]
    diff_file = _emit(path, tmp_path / 'd.json')
    result = sync.apply(path, _token(path, diff_file), diff_path=diff_file)
    after = _sha(path)
    # simulate a -wal sidecar
    wal = path.with_name(path.name + '-wal'); wal.write_bytes(b'x')
    with pytest.raises(SystemExit, match='停止后端'):
        sync.rollback(path, Path(result['backup']))
    wal.unlink()
    rolled = sync.rollback(path, Path(result['backup']))
    assert rolled['sha256'] == result['beforeSha256'] == _sha(path)
    assert Path(rolled['preRollbackBackup']).is_file()
    assert rolled['preRollbackSha256'] == after
