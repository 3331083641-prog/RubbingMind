"""Run RapidOCR once on a real archived crop and on a clean printed glyph.

The JSON is a failure or mismatch record. It is not an accuracy evaluation.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from glyph_ocr import recognize

OUT = ROOT / 'experiments/results/2026-10-18-rapidocr-probe'
CROP = ROOT / 'data/catalog/assessments/inputs/han_01_caoquan.png'


def printed_ten():
    image = np.full((96, 96, 3), 255, np.uint8)
    cv2.putText(image, '十', (18, 72), cv2.FONT_HERSHEY_SIMPLEX, 2.2, (0, 0, 0), 3, cv2.LINE_AA)
    return image


def main():
    crop = cv2.imdecode(np.frombuffer(CROP.read_bytes(), np.uint8), cv2.IMREAD_COLOR)
    rubbing = recognize(crop)
    printed = recognize(printed_ten())
    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        'engine': 'rapidocr_onnxruntime',
        'license': 'Apache-2.0',
        'countsAsAccuracy': False,
        'verifiedLabels': 0,
        'evaluationStatus': 'not_evaluated',
        'rubbingCrop': {
            'steleId': 'han_01_caoquan',
            'file': CROP.relative_to(ROOT).as_posix(),
            'status': rubbing['status'],
            'texts': rubbing['texts'],
            'elapsedMs': rubbing['elapsedMs'],
            'limitation': rubbing['limitation'],
            'readingStatus': '未与曹全碑释文核对。这些字符串只是模型输出，不能当作碑文释文。',
        },
        'printedTen': {
            'status': printed['status'],
            'texts': printed['texts'],
            'elapsedMs': printed['elapsedMs'],
            'readAsTen': any(item['text'] == '十' for item in printed['texts']),
        },
    }
    (OUT / 'result.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()