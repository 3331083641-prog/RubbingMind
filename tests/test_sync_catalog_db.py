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


def test_dry_run_is_read_only_and_follows_rules(db, capsys):
    path, verified, unverified, old = db
    before = _sha(path)
    assert sync.main(['--db', str(path)]) == 0
    out = capsys.readouterr().out
    assert _sha(path) == before and '112.241' not in out and '30.335' not in out
    diff = sync.compute_diff(path)
    assert diff['counts'] == {'update': 1, 'hold': 1, 'set_null': 1, 'keep_row': 1, 'insert_from_catalogue': 0}
    assert {(o['op'], o['id']) for o in diff['operations']} >= {('update', verified), ('hold', unverified), ('set_null', old), ('keep_row', old)}
    assert sync.confirmation_token(diff) in out


def test_apply_requires_matching_token_and_rollback_restores_bytes(db):
    path, verified, unverified, old = db
    original = _sha(path)
    with pytest.raises(SystemExit):
        sync.apply(path, 'wrong-token')
    with pytest.raises(SystemExit):
        sync.apply(path, None, interactive=False)
    assert _sha(path) == original and not list(path.parent.glob('*.bak'))
    token = sync.confirmation_token(sync.compute_diff(path))
    result = sync.apply(path, token)
    assert result['applied'] and result['backupSha256'] == original == result['beforeSha256']
    assert result['postCheck']['update'] == result['postCheck']['set_null'] == 0 and result['postCheck']['hold'] == 1
    with sqlite3.connect(path) as conn:
        catalogue_author = next(r['author'] for r in load('steles28.json') if r['id'] == verified)
        assert conn.execute('SELECT author FROM steles WHERE id=?', (verified,)).fetchone()[0] == catalogue_author
        assert conn.execute('SELECT author FROM steles WHERE id=?', (unverified,)).fetchone()[0] == '某人'  # hold never written
        assert conn.execute('SELECT gis_lng, gis_lat FROM steles WHERE id=?', (old,)).fetchone() == (None, None)
        assert conn.execute('SELECT COUNT(*) FROM steles WHERE id=?', (old,)).fetchone()[0] == 1  # retired row kept
    with pytest.raises(SystemExit):  # stale token after the DB changed
        sync.apply(path, token)
    restored = sync.rollback(path, Path(result['backup']))
    assert restored['sha256'] == original == _sha(path)


def test_external_diff_must_match(db, tmp_path):
    path = db[0]
    diff = sync.compute_diff(path)
    good = tmp_path / 'diff.json'; good.write_text(json.dumps(diff, ensure_ascii=False), 'utf-8')
    sync.check_external_diff(diff, good)
    bad = dict(diff, basis=dict(diff['basis'], sqliteSha256='0' * 64))
    good.write_text(json.dumps(bad), 'utf-8')
    with pytest.raises(SystemExit):
        sync.check_external_diff(diff, good)


def test_apply_and_rollback_need_explicit_db():
    with pytest.raises(SystemExit):
        sync.main(['--apply', '--confirm', 'x'])
