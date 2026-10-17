"""Actual image-crop inference and durable human decisions."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

import cv2
import httpx

from algorithm_engine import safe_read_image
from catalog import BASE
from database import get_db_connection
from upload_storage import image_path as uploaded_image_path
from glyph_vision import analyze_crop, shape_similarity

INFERENCE_DIR = BASE / 'data' / 'runtime' / 'glyph-inferences'
RULES = {
    '慶歸法': [('胤', '上下文可组成「慶歸法胤」；尚未据图像确认笔画。')],
    '尚書都官': [('檢', '上下文可能涉及「檢校尚書都官」；尚未据图像确认笔画。')],
    '敦煌郡': [('效', '上下文可能涉及地名「效谷」；尚未据图像确认笔画。')],
    '岸谷更': [('遷', '上下文可能组成「岸谷更遷」；尚未据图像确认笔画。')],
    '假黃': [('鉞', '上下文可能组成「假黃鉞」；尚未据图像确认笔画。')],
}


def _connection():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS glyph_inferences (
        id TEXT PRIMARY KEY, stele_id TEXT NOT NULL, record_json TEXT NOT NULL, created_at TEXT NOT NULL
    )''')
    conn.execute('CREATE TABLE IF NOT EXISTS glyph_templates (id TEXT PRIMARY KEY, record_json TEXT NOT NULL)')
    conn.commit()
    return conn


def get_inference(inference_id: str):
    with closing(_connection()) as conn:
        row = conn.execute('SELECT record_json FROM glyph_inferences WHERE id=?', (inference_id,)).fetchone()
    return json.loads(row['record_json']) if row else None


def list_inferences(stele_id: str):
    with closing(_connection()) as conn:
        rows = conn.execute('SELECT record_json FROM glyph_inferences WHERE stele_id=? ORDER BY created_at DESC', (stele_id,)).fetchall()
    return [json.loads(row['record_json']) for row in rows]


def _source_path(record):
    if record.get('source_kind') == 'user_upload':
        return uploaded_image_path(record['id'])
    url = (record.get('imageAssets') or {}).get('readable') or record.get('raw_image', '')
    path = (BASE / 'apps/web/public' / url.split('?')[0].lstrip('/')).resolve()
    public = (BASE / 'apps/web/public').resolve()
    if not path.is_relative_to(public):
        return None
    return path


async def _suggest(image_bytes: bytes, context: str):
    key = os.getenv('RUBBINGMIND_VISION_API_KEY', '').strip()
    if key:
        base_url = os.getenv('RUBBINGMIND_VISION_BASE_URL', 'https://api.openai.com/v1').rstrip('/')
        model = os.getenv('RUBBINGMIND_VISION_MODEL', 'gpt-4o-mini')
        # Only local administrator configuration controls the endpoint and credentials.
        if not base_url.startswith('https://'):
            return {'source': 'model_unavailable', 'model': model, 'candidates': [], 'note': '模型地址须使用 HTTPS。'}
        encoded = base64.b64encode(image_bytes).decode('ascii')
        prompt = ('请观察此真实拓片局部并结合上下文给出最多三个单字候选。'
                  '只返回 JSON 数组，每项含 glyph、visualEvidence、contextEvidence、sourceUrls。'
                  '看不清则返回空数组。不要编造笔画、文献、概率或来源。'
                  f'上下文：{context}')
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(base_url + '/chat/completions',
                    headers={'Authorization': 'Bearer ' + key},
                    json={'model': model, 'messages': [{'role': 'user', 'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': 'data:image/png;base64,' + encoded}}
                    ]}], 'temperature': 0})
            response.raise_for_status()
            text = response.json()['choices'][0]['message']['content']
            parsed = json.loads(re.search(r'\[.*\]', text, re.S).group())
            candidates = []
            for entry in parsed[:3]:
                glyph = entry.get('glyph', '')
                if len(glyph) == 1 and '\u3400' <= glyph <= '\u9fff':
                    candidates.append({'glyph': glyph, 'visualEvidence': str(entry.get('visualEvidence', ''))[:300],
                                       'contextEvidence': str(entry.get('contextEvidence', ''))[:300],
                                       'sourceUrls': [url for url in entry.get('sourceUrls', []) if isinstance(url, str) and url.startswith('https://')][:3],
                                       'scoreBasis': '模型排序，未经概率校准'})
            return {'source': 'vision_model', 'model': model, 'candidates': candidates,
                    'note': '模型输出需人工审核；来源链接为模型建议，尚未单独核实。'}
        except (httpx.HTTPError, KeyError, TypeError, ValueError, AttributeError):
            # Never log the API key, prompt image, or provider response.
            return {'source': 'model_unavailable', 'model': model, 'candidates': [], 'note': '模型请求失败；没有生成图像推演结论。'}
    candidates = []
    for phrase, suggestions in RULES.items():
        if phrase in context:
            candidates = [{'glyph': char, 'visualEvidence': '规则未分析图像笔画',
                           'contextEvidence': explanation, 'sourceUrls': [],
                           'scoreBasis': '上下文规则排序，非概率'} for char, explanation in suggestions]
            break
    return {'source': 'context_rule' if candidates else 'unavailable', 'model': None, 'candidates': candidates,
            'note': '仅基于上下文给出待核建议，未运行图像模型。' if candidates else '无可核实候选；请提供更充分的上下文或配置可选视觉模型。'}


async def infer(record, bbox: dict, context: str, character_id: str | None = None, original_glyph: str | None = None, original_status: str | None = None, run_id: str | None = None):
    source_path = _source_path(record)
    if source_path is None or not source_path.is_file():
        raise ValueError('当前文物原始图像不可用')
    source_bytes = source_path.read_bytes()
    image = safe_read_image(source_bytes)
    if image is None:
        raise ValueError('源图像无法解码')
    height, width = image.shape[:2]
    x, y, w, h = (bbox[key] for key in ('x', 'y', 'w', 'h'))
    if w < 16 or h < 16 or x < 0 or y < 0 or x + w > width or y + h > height or w > 1024 or h > 1024:
        raise ValueError('残字选区越界或尺寸不在 16–1024 像素内')
    crop = image[y:y+h, x:x+w]
    ok, encoded = cv2.imencode('.png', crop)
    if not ok:
        raise ValueError('残字选区无法编码')
    crop_bytes = encoded.tobytes()
    analysis, analysis_images = analyze_crop(crop)
    suggestion = await _suggest(crop_bytes, context[:1000])
    retrieved = retrieve_templates(analysis_images['foreground'])
    if not suggestion['candidates'] and retrieved:
        suggestion.update(source='local_shape_retrieval',model='glyph-shape-v2.0',candidates=retrieved,
                          note='仅与用户确认的参考字形比较；相似评分未经识字概率校准，需人工核验。')
    inference_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    record_json = {
        'inferenceId': inference_id, 'steleId': record['id'], 'runId': run_id, 'characterId': character_id,
        'originalGlyph': original_glyph, 'originalStatus': original_status,
        'bbox': bbox, 'context': context[:1000], 'inputImageSha256': hashlib.sha256(source_bytes).hexdigest(),
        'cropSha256': hashlib.sha256(crop_bytes).hexdigest(), 'cropUrl': f'/api/inferences/{inference_id}/crop',
        'source': suggestion['source'], 'model': suggestion['model'], 'candidates': suggestion['candidates'],
        'note': suggestion['note'], 'sourceUrl': record.get('sourceUrl'),
        'status': 'pending_review' if suggestion['candidates'] else 'no_candidate',
        'adoptedGlyph': None, 'decisions': [], 'createdAt': now,
        'visualAnalysis':analysis,'analysisImages':{role:f'/api/inferences/{inference_id}/analysis/{role}' for role in analysis_images},
        'retrievalCandidates':retrieved,
    }
    INFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    crop_path = INFERENCE_DIR / (inference_id + '.png')
    try:
        crop_path.write_bytes(crop_bytes)
        for role,pixels in analysis_images.items():
            ok, encoded_image=cv2.imencode('.png',pixels)
            if not ok:raise ValueError('分析图无法编码')
            (INFERENCE_DIR/(inference_id+'_'+role+'.png')).write_bytes(encoded_image.tobytes())
        with closing(_connection()) as conn:
            with conn:
                conn.execute('INSERT INTO glyph_inferences VALUES (?,?,?,?)',
                             (inference_id, record['id'], json.dumps(record_json, ensure_ascii=False), now))
    except Exception:
        crop_path.unlink(missing_ok=True)
        for role in analysis_images:(INFERENCE_DIR/(inference_id+'_'+role+'.png')).unlink(missing_ok=True)
        raise
    return record_json


def retrieve_templates(foreground):
    with closing(_connection()) as conn:
        rows=conn.execute('SELECT record_json FROM glyph_templates ORDER BY id').fetchall()
    matches=[]
    for row in rows:
        template=json.loads(row['record_json'])
        path=INFERENCE_DIR/(template['inferenceId']+'_foreground.png')
        if not path.is_file():continue
        pixels=safe_read_image(str(path),is_gray=True)
        score=shape_similarity(foreground,pixels)
        if score<.45:continue
        matches.append({'glyph':template['glyph'],'visualEvidence':f"与人工参考 {template['templateId']} 归一化轮廓距离/投影相似评分 {score:.3f}",
            'shapeScore':score,'contextEvidence':'模板标签由本地用户确认，未自动核验古文字身份',
            'sourceUrls':[template['sourceUrl']] if template.get('sourceUrl') else [],
            'scoreBasis':'对称距离变换与投影距离的启发式相似评分，非统计概率',
            'templateId':template['templateId'],'templateSteleId':template['steleId']})
    best={}
    for match in sorted(matches,key=lambda r:-r['shapeScore']):best.setdefault(match['glyph'],match)
    return list(best.values())[:3]


def register_template(inference_id,glyph,basis,annotator):
    record=get_inference(inference_id)
    if record is None:raise LookupError('推演记录不存在')
    if len(glyph)!=1 or not '\u3400'<=glyph<='\u9fff' or not basis.strip() or not annotator.strip():
        raise ValueError('参考字必须是单字，且填写人工标注者和依据')
    # No inferred candidate is silently promoted into a trusted reference.
    template_id=uuid.uuid4().hex
    template={'templateId':template_id,'inferenceId':inference_id,'steleId':record['steleId'],'glyph':glyph,
        'bbox':record['bbox'],'cropSha256':record['cropSha256'],'inputImageSha256':record['inputImageSha256'],
        'sourceUrl':record.get('sourceUrl'),'annotationBasis':basis[:500],'annotator':annotator[:80],
        'verification':'local_human_label_not_independent_ground_truth','createdAt':datetime.now(timezone.utc).isoformat()}
    with closing(_connection()) as conn:
        with conn:conn.execute('INSERT INTO glyph_templates VALUES (?,?)',(template_id,json.dumps(template,ensure_ascii=False)))
    return template


def analysis_path(inference_id,role):
    if role not in ('gray','foreground','skeleton','noise') or not get_inference(inference_id):return None
    path=INFERENCE_DIR/(inference_id+'_'+role+'.png')
    return path if path.is_file() else None


def decide(inference_id: str, action: str, glyph: str | None = None):
    record = get_inference(inference_id)
    if record is None:
        raise LookupError('推演记录不存在')
    if action == 'accept':
        if glyph not in [item['glyph'] for item in record['candidates']]:
            raise ValueError('只能采纳本次实际候选')
        record['adoptedGlyph'] = glyph
        record['status'] = 'human_accepted'
    elif action == 'revoke':
        record['adoptedGlyph'] = None
        record['status'] = 'pending_review'
    elif action == 'reject':
        record['adoptedGlyph'] = None
        record['status'] = 'human_rejected'
    else:
        raise ValueError('未知采纳操作')
    record['decisions'].append({'action': action, 'glyph': glyph if action == 'accept' else None,
                                'at': datetime.now(timezone.utc).isoformat(), 'actor': 'local_user'})
    with closing(_connection()) as conn:
        with conn:
            conn.execute('UPDATE glyph_inferences SET record_json=? WHERE id=?', (json.dumps(record, ensure_ascii=False), inference_id))
    return record


def crop_path(inference_id: str):
    return INFERENCE_DIR / (inference_id + '.png') if get_inference(inference_id) else None
