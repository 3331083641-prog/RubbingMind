"""Add a region diagnostic beside the published full-frame grade.

The published imageCondition is left unchanged. These notes are an automatic
screen, not a human identification of damaged characters or stone weathering.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('assess_museum_condition', ROOT / 'scripts' / 'assess_museum_condition.py')
_assess = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_assess)
read_gray = _assess.read_gray
scaled = _assess.scaled

ASSESS = ROOT / 'data/catalog/assessments'
OUT = ASSESS / 'regions'


def ink_fraction(cell):
    if cell.size == 0:
        return 0.0
    dark = float(np.median(cell[:2, :].ravel())) < 96 if cell.shape[0] > 2 else False
    work = cell if dark else 255 - cell
    mask = cv2.threshold(work, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return float(np.count_nonzero(mask) / mask.size)


def analyze(stele_id, assessment):
    raw, image = read_gray(ROOT / assessment['sourceImage'])
    del raw
    view, ratio = scaled(image, 900)
    height, width = view.shape
    margin = max(4, int(round(min(height, width) * 0.08)))
    border = np.concatenate([
        view[:margin, :].ravel(), view[-margin:, :].ravel(),
        view[:, :margin].ravel(), view[:, -margin:].ravel(),
    ])
    inner = view[margin:height - margin, margin:width - margin]
    cell_h, cell_w = inner.shape[0] // 3, inner.shape[1] // 3
    cells = []
    for row in range(3):
        for col in range(3):
            cell = inner[row * cell_h:(row + 1) * cell_h, col * cell_w:(col + 1) * cell_w]
            cells.append({
                'row': row,
                'col': col,
                'contrastStd': round(float(cell.std()), 2),
                'laplacianVariance': round(float(cv2.Laplacian(cell, cv2.CV_64F).var()), 1),
                'inkFraction': round(ink_fraction(cell), 4),
            })
    text_cells = [cell for cell in cells if 0.04 <= cell['inkFraction'] <= 0.55]
    contrasts = [cell['contrastStd'] for cell in text_cells] or [cell['contrastStd'] for cell in cells]
    median_contrast = float(np.median(contrasts))
    fading = [
        {'row': cell['row'], 'col': cell['col'], 'contrastStd': cell['contrastStd']}
        for cell in text_cells if cell['contrastStd'] < median_contrast * 0.55
    ]
    texture = [
        {'row': cell['row'], 'col': cell['col'], 'laplacianVariance': cell['laplacianVariance']}
        for cell in cells if cell['inkFraction'] < 0.04 and cell['laplacianVariance'] > 800
    ]
    return {
        'steleId': stele_id,
        'rule': 'region-condition-v1',
        'publishedImageCondition': assessment.get('imageCondition'),
        'publishedGradeUnchanged': True,
        'reviewStatus': '自动初筛，待人工复核',
        'capture': {
            'readablePixels': assessment.get('imageDimensions', {}).get('readable'),
            'analysisLongSide': int(max(view.shape)),
            'analysisScale': round(float(ratio), 4),
            'note': '拉普拉斯方差随分辨率、缩放和压缩变化，不能把绝对数值直接当成字迹残损程度。',
        },
        'polarity': 'blackGround' if assessment.get('readableMetrics', {}).get('darkGround') else 'lightGround',
        'mountingAndScan': {
            'borderFraction': 0.08,
            'borderContrastStd': round(float(border.std()), 2),
            'note': '外缘 8% 单独观察裱边、纸边和扫描背景，不并入正文初筛等级。',
        },
        'textCells': text_cells,
        'suspectedLocalFading': fading,
        'suspectedNonTextTexture': texture,
        'physicalStoneWeathering': '无可靠原石证据，不评定',
        'coverage': assessment.get('coverage'),
        'limitations': [
            '3×3 分区是自动抽样，不是逐字释读。',
            '疑似局部变淡和疑似非文字纹理都需要人工看图确认。',
            '黑底白字与白底黑字已分开估计墨迹比例，但仍可能受拓纸底色影响。',
            '原石剥蚀、裂隙和石面磨损没有原石照片时不评定。',
        ],
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted(ASSESS.glob('*.json')):
        assessment = json.loads(path.read_text(encoding='utf-8'))
        report = analyze(path.stem, assessment)
        destination = OUT / f'{path.stem}.json'
        text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
        destination.write_bytes(text.replace('\n', '\r\n').encode('utf-8'))
        count += 1
        assert report['publishedImageCondition'] == assessment['imageCondition']
    print(json.dumps({'regions': count}, ensure_ascii=False))


if __name__ == '__main__':
    main()
