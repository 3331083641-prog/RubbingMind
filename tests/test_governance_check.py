"""C-06 / C-08: the governance check is read-only and reports differences without changing anything."""
import hashlib
import json
import sqlite3
import subprocess
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
    assert {'id': 'tang_02_jiucheng', 'column': 'author', 'sqlite': '未核定', 'catalogue': '魏徵'} in sql['fieldDiffs']
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
