# -*- coding: utf-8 -*-
"""
墨韵智考 - 数据库连接与 ORM / SQLite 模型层
支持金石碑刻档案、修复历史日志、残字推演记录与消融实验持久化
"""
import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
from runtime_paths import db_path as _db_path

# Default unchanged (<repo>/data/rubbingmind.sqlite); RUBBINGMIND_DB_PATH relocates it.
DB_PATH = _db_path()


def get_db_connection() -> sqlite3.Connection:
    """获取 SQLite 数据库连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database(schema_only: bool = False, json_seed_path: Optional[str] = None):
    """
    初始化数据库表结构与预置馆藏种子数据
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 碑拓数字档案表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS steles (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        dynasty TEXT NOT NULL,
        dynasty_value TEXT NOT NULL,
        author TEXT,
        script_type TEXT,
        weathering_level TEXT,
        year TEXT,
        ganzhi TEXT,
        location TEXT,
        museum TEXT,
        dimensions TEXT,
        summary TEXT,
        historical_context TEXT,
        raw_image TEXT,
        clean_image TEXT,
        damaged_image TEXT,
        restored_image TEXT,
        source_url TEXT,
        license TEXT,
        attribution TEXT,
        image_status TEXT,
        gis_lng REAL,
        gis_lat REAL,
        metrics_json TEXT,
        translation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. 图像修复与去噪实验日志表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restoration_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stele_id TEXT,
        d0 REAL,
        nlm_h REAL,
        clahe_clip REAL,
        morph_kernel INTEGER,
        psnr REAL,
        ssim REAL,
        snr_gain REAL,
        processing_time_ms INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stele_id) REFERENCES steles (id)
    );
    """)

    # 3. 残字多模态推演与释读记录表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inference_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stele_id TEXT,
        char_index INTEGER,
        target_char TEXT,
        inferred_char TEXT,
        confidence REAL,
        evidence TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stele_id) REFERENCES steles (id)
    );
    """)

    conn.commit()

    if schema_only:
        conn.close()
        return

    # 注入种子数据（默认取 data/museum_database.json）
    seed_file = json_seed_path or os.path.join(BASE_DIR, "data", "museum_database.json")
    if os.path.exists(seed_file):
        try:
            with open(seed_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            
            for item in data:
                coords = item.get("gis_coords") or []
                lng = coords[0] if len(coords) > 0 else None
                lat = coords[1] if len(coords) > 1 else None
                cursor.execute("""
                INSERT INTO steles (
                    id, title, dynasty, dynasty_value, author, script_type, weathering_level,
                    year, ganzhi, location, museum, dimensions, summary, historical_context,
                    raw_image, clean_image, damaged_image, restored_image, source_url,
                    license, attribution, image_status, gis_lng, gis_lat, metrics_json, translation
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                ) ON CONFLICT(id) DO NOTHING;
                """, (
                    item.get("id"),
                    item.get("title"),
                    item.get("dynasty"),
                    item.get("dynasty_value"),
                    item.get("author"),
                    item.get("script_type"),
                    item.get("weathering_level"),
                    item.get("year"),
                    item.get("ganzhi"),
                    item.get("location"),
                    item.get("museum"),
                    item.get("dimensions"),
                    item.get("summary"),
                    item.get("historical_context"),
                    item.get("raw_image"),
                    item.get("clean_image"),
                    item.get("damaged_image"),
                    item.get("restored_image"),
                    item.get("sourceUrl"),
                    item.get("license"),
                    item.get("attribution"),
                    item.get("imageStatus"),
                    lng,
                    lat,
                    json.dumps(item.get("metrics", {}), ensure_ascii=False),
                    item.get("translation", "")
                ))
            conn.commit()
        except Exception as e:
            print(f"[!] 导入种子数据异常: {e}")

    conn.close()


def query_steles(dynasty: Optional[str] = None, include_retired: bool = False) -> List[Dict[str, Any]]:
    """查询碑刻列表"""
    conn = get_db_connection()
    cursor = conn.cursor()
    conditions=[];params=[]
    if dynasty and dynasty != "all":
        conditions.append('dynasty_value = ?');params.append(dynasty)
    if not include_retired and cursor.execute("SELECT name FROM sqlite_master WHERE name='museum_catalog_status'").fetchone():
        conditions.append("id NOT IN (SELECT id FROM museum_catalog_status WHERE status='retired')")
    query='SELECT * FROM steles'+(' WHERE '+' AND '.join(conditions) if conditions else '')+' ORDER BY id'
    cursor.execute(query,params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
