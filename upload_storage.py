"""Local user image records, kept outside the authoritative 28-item catalogue."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from database import BASE_DIR, get_db_connection

from runtime_paths import upload_dir

UPLOAD_DIR = upload_dir()  # default <repo>/data/uploads; RUBBINGMIND_UPLOAD_DIR


def _connection():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS user_uploads (
        id TEXT PRIMARY KEY, record_json TEXT NOT NULL, sha256 TEXT NOT NULL,
        image_format TEXT NOT NULL, created_at TEXT NOT NULL
    )''')
    conn.commit()
    return conn


def image_path(upload_id: str) -> Path | None:
    if not upload_id.startswith('upload-'):
        return None
    record = get_upload(upload_id)
    if record is None:
        return None
    return UPLOAD_DIR / upload_id / ('original.' + record['uploadFormat'])


def get_upload(upload_id: str):
    with closing(_connection()) as conn:
        row = conn.execute('SELECT record_json FROM user_uploads WHERE id=?', (upload_id,)).fetchone()
    return json.loads(row['record_json']) if row else None


def list_uploads():
    with closing(_connection()) as conn:
        rows = conn.execute('SELECT record_json FROM user_uploads ORDER BY created_at DESC').fetchall()
    return [json.loads(row['record_json']) for row in rows]


def create_upload(content: bytes, image_format: str, width: int, height: int, metadata: dict):
    upload_id = 'upload-' + uuid.uuid4().hex
    digest = hashlib.sha256(content).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    relative_url = f'/api/uploads/{upload_id}/image'
    record = {
        'id': upload_id,
        'title': metadata['title'],
        'dynasty': metadata['dynasty'],
        'dynasty_value': 'user_upload',
        'author': metadata['author'] or '未核实',
        'script_type': metadata['script_type'],
        'weathering_level': metadata['weathering_level'],
        'year': '未考证',
        'ganzhi': '未考证',
        'location': '未核实',
        'museum': '用户本地上传',
        'dimensions': f'数字图像 {width}×{height} 像素',
        'summary': '用户上传的图像；名称、时代和书体由用户填写，尚未经馆藏核验。',
        'historical_context': '未取得可核实史料，不生成历史人物或考据结论。',
        'badges': ['用户上传', '资料未核实'],
        'raw_image': relative_url,
        'clean_image': '',
        'damaged_image': '',
        'restored_image': '',
        'metrics': {key: None for key in ('psnr', 'ssim', 'snr_gain', 'glyph_completeness', 'character_accuracy')},
        'translation': '',
        'source_kind': 'user_upload',
        'imageStatus': '用户上传 · 未核验',
        'evaluationStatus': 'unassessed',
        'originalFileSha256': digest,
        'uploadFormat': image_format,
        'imageWidth': width,
        'imageHeight': height,
        'createdAt': now,
    }
    folder = UPLOAD_DIR / upload_id
    folder.mkdir(parents=True, exist_ok=False)
    try:
        destination = folder / f'original.{image_format}'
        temporary = folder / 'original.part'
        temporary.write_bytes(content)
        os.replace(temporary, destination)
        with closing(_connection()) as conn:
            with conn:
                conn.execute('INSERT INTO user_uploads VALUES (?,?,?,?,?)',
                             (upload_id, json.dumps(record, ensure_ascii=False), digest, image_format, now))
        return record
    except Exception:
        shutil.rmtree(folder)
        raise
