"""Optional printed-Chinese OCR probe.

RapidOCR is a modern scene/print recognizer. Its output is never a verified
ancient-stele reading and never an accuracy number.
"""
from __future__ import annotations

import time

import cv2
import numpy as np

LIMITATION = 'RapidOCR 面向现代印刷体和自然场景文字，不是古碑残字识别模型。输出不能当作释文，也不能计算识别准确率。'


def _unavailable(reason):
    return {
        'engine': 'rapidocr_onnxruntime',
        'status': 'engine_unavailable',
        'candidates': [],
        'texts': [],
        'elapsedMs': None,
        'countsAsAccuracy': False,
        'limitation': LIMITATION + reason,
    }


def recognize(image, engine=None):
    """Run one image. `engine` is injectable so tests do not need the model weights."""
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError('OCR 输入不是有效图像')
    if engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            return _unavailable(' 当前环境没有安装 rapidocr_onnxruntime。')
        if not hasattr(recognize, '_engine'):
            recognize._engine = RapidOCR()
        engine = recognize._engine
    started = time.perf_counter()
    try:
        raw = engine(image)
    except Exception as exc:
        return {
            'engine': 'rapidocr_onnxruntime',
            'status': 'inference_failed',
            'candidates': [],
            'texts': [],
            'elapsedMs': round((time.perf_counter() - started) * 1000, 1),
            'error': type(exc).__name__,
            'countsAsAccuracy': False,
            'limitation': LIMITATION,
        }
    if isinstance(raw, tuple):
        raw = raw[0]
    texts = []
    for item in raw or []:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        text = str(item[1]).strip()
        score = None
        if len(item) > 2:
            try:
                score = float(item[2])
            except (TypeError, ValueError):
                score = None
        if text:
            texts.append({'text': text, 'score': score})
    glyphs = []
    for item in texts:
        for char in item['text']:
            if '\u3400' <= char <= '\u9fff' and char not in glyphs:
                glyphs.append(char)
    return {
        'engine': 'rapidocr_onnxruntime',
        'status': 'completed',
        'candidates': [{
            'glyph': glyph,
            'scoreBasis': 'RapidOCR 文本拆成单字，未经古碑标定',
        } for glyph in glyphs[:3]],
        'texts': texts[:8],
        'elapsedMs': round((time.perf_counter() - started) * 1000, 1),
        'countsAsAccuracy': False,
        'license': 'Apache-2.0',
        'limitation': LIMITATION,
    }


def recognize_png(png_bytes: bytes, engine=None):
    image = cv2.imdecode(np.frombuffer(png_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('选区图像无法解码')
    return recognize(image, engine=engine)
