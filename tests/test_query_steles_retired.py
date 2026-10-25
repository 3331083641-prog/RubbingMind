"""BR-07: query_steles(include_retired=True) blanks coordinates of retired rows; DB bytes unchanged."""
import sqlite3
from pathlib import Path

import database


def test_retired_coordinates_blanked_without_writing(tmp_path, monkeypatch):
    db = tmp_path / 't.sqlite'
    with sqlite3.connect(db) as conn:
        conn.execute('CREATE TABLE steles (id TEXT PRIMARY KEY, title TEXT, dynasty TEXT, dynasty_value TEXT, author TEXT, script_type TEXT, museum TEXT, source_url TEXT, license TEXT, attribution TEXT, gis_lng REAL, gis_lat REAL)')
        conn.execute('CREATE TABLE museum_catalog_status (id TEXT PRIMARY KEY, status TEXT, recommended_id TEXT)')
        conn.execute("INSERT INTO steles VALUES ('active','a','d','v',NULL,NULL,NULL,NULL,NULL,NULL,1.0,2.0)")
        conn.execute("INSERT INTO steles VALUES ('qing_01_shilang','r','d','v',NULL,NULL,NULL,NULL,NULL,NULL,112.241,30.335)")
        conn.execute("INSERT INTO museum_catalog_status VALUES ('qing_01_shilang','retired',NULL)")
    monkeypatch.setattr(database, 'get_db_connection', lambda: sqlite3.connect(db))
    # sqlite3.Row-like: make connection return Row
    def connect():
        conn = sqlite3.connect(db); conn.row_factory = sqlite3.Row; return conn
    monkeypatch.setattr(database, 'get_db_connection', connect)
    before = db.read_bytes()
    rows = {r['id']: dict(r) for r in database.query_steles(include_retired=True)}
    assert rows['qing_01_shilang']['gis_lng'] is None and rows['qing_01_shilang']['gis_lat'] is None
    assert rows['active']['gis_lng'] == 1.0  # active unchanged
    assert db.read_bytes() == before  # nothing written
    # default exclude retired
    assert all(r['id'] != 'qing_01_shilang' for r in database.query_steles())
