"""Measure rubbing-image condition and run a recorded partial restoration for all 28 works.

The grade is an image diagnostic. It is not a stone-weathering score. PSNR and SSIM
stay unassessed because the readable image is not a paired ground truth.
"""
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import time
from pathlib import Path

import cv2
import numpy as np

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalog import museum_records
from degradation_analysis import AdaptiveRubbingRestorer, VERSION, missing_information_mask

CATALOG_PATH = ROOT / 'data/catalog/steles28.json'


def results_root() -> Path:
    """RUBBINGMIND_RESULTS_DIR when set, else the historical <repo>/static/results."""
    from runtime_paths import results_override
    return results_override() or ROOT / 'static/results'

ASSESS_DIR = ROOT / 'data/catalog/assessments'
REVIEW_CSV = ROOT / 'docs/audit/28-steles-authorship-condition-review.csv'
REVIEW_MD = ROOT / 'docs/audit/28-steles-authorship-condition-review.md'
RULE = 'rubbing-image-condition-v1'
BATCH = 'assess28-20261018'


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    path.write_bytes(text.replace('\n', '\r\n').encode('utf-8'))


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def read_gray(path):
    raw = path.read_bytes()
    image = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f'cannot decode {path}')
    return raw, image


def write_png(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode('.png', image)
    if not ok:
        raise ValueError(f'cannot encode {path}')
    path.write_bytes(encoded.tobytes())
    return sha_bytes(path.read_bytes())


def scaled(image, long_side=1400):
    height, width = image.shape
    longest = max(height, width)
    if longest <= long_side:
        return image, 1.0
    ratio = long_side / longest
    resized = cv2.resize(image, (max(1, int(round(width * ratio))), max(1, int(round(height * ratio)))), interpolation=cv2.INTER_AREA)
    return resized, ratio


def component_fragmentation(image):
    small = image
    border = max(2, int(round(min(small.shape) * 0.04)))
    edge = np.concatenate([
        small[:border, :].ravel(), small[-border:, :].ravel(),
        small[:, :border].ravel(), small[:, -border:].ravel(),
    ])
    dark_ground = float(np.median(edge)) < 96
    if dark_ground:
        work = cv2.threshold(small, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    else:
        work = cv2.threshold(255 - small, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    count, _, stats, _ = cv2.connectedComponentsWithStats(work, 8)
    areas = [int(stats[index, cv2.CC_STAT_AREA]) for index in range(1, count)]
    useful = [area for area in areas if area >= 6]
    tiny = [area for area in useful if area < 80]
    return {
        'darkGround': dark_ground,
        'componentCount': len(useful),
        'smallComponentFraction': (len(tiny) / len(useful)) if useful else None,
    }


def measure(image):
    view, ratio = scaled(image)
    loss = missing_information_mask(view)
    fragments = component_fragmentation(view)
    return {
        'analysisLongSide': int(max(view.shape)),
        'analysisScale': ratio,
        'mean': float(view.mean()),
        'contrastStd': float(view.std()),
        'laplacianVariance': float(cv2.Laplacian(view, cv2.CV_64F).var()),
        'suspectedUniformLossFraction': float(np.count_nonzero(loss) / loss.size),
        **fragments,
    }


def grade_from(metrics):
    """Global scan diagnostic. Small connected components are recorded but not graded.

    Character strokes split into many components on a sharp rubbing, so that
    fraction is not evidence of damage.
    """
    lap = metrics['laplacianVariance']
    contrast = metrics['contrastStd']
    loss = metrics['suspectedUniformLossFraction']
    if lap < 12 and contrast < 22:
        return '严重漫漶', [f'拉普拉斯方差 {lap:.0f}，对比度标准差 {contrast:.1f}，清晰度和对比度同时很低']
    if loss >= 0.05:
        return '重度影像损伤', [f'与页面底色明显不同的内部均匀区域占比 {loss:.1%}']
    if lap < 80 or contrast < 28 or loss >= 0.02:
        return '中度影像损伤', [f'拉普拉斯方差 {lap:.0f}，对比度标准差 {contrast:.1f}，疑似均匀缺损 {loss:.1%}']
    if contrast < 45 or 0.015 <= loss < 0.05:
        return '中度影像损伤', [f'全幅对比度标准差 {contrast:.1f}，拉普拉斯方差 {lap:.0f}，疑似均匀缺损 {loss:.1%}']
    if lap >= 400 and loss < 0.015:
        return '轻度影像损伤', [f'全幅对比度标准差 {contrast:.1f}，拉普拉斯方差 {lap:.0f}，疑似均匀缺损 {loss:.1%}。这是扫描影像指标，不是逐字残泐判读']
    return '待人工复核', [f'拉普拉斯方差 {lap:.0f}，对比度标准差 {contrast:.1f}，疑似均匀缺损 {loss:.1%}，未落入已写明区间']


def crop_box(image):
    height, width = image.shape
    if height * width <= 1_600_000 and max(height, width) <= 512:
        return [0, 0, width, height], 'full_readable_frame'
    side = 512
    x = max(0, width // 2 - side // 2)
    y = max(0, height // 2 - side // 2)
    return [x, y, min(width, x + side), min(height, y + side)], 'partial_center_roi'


def public_path(url):
    return ROOT / 'apps/web/public' / url.split('?', 1)[0].lstrip('/')


def sync_derived():
    rows = museum_records()
    for relative in (
        'apps/web/src/data/steles28.json',
        'data/museum_database.json',
        'data/museum-import/merged_28_steles.json',
    ):
        write_json(ROOT / relative, rows)


def observed(metrics, grade):
    items = [f"对比度标准差 {metrics['contrastStd']:.1f}", f"拉普拉斯方差 {metrics['laplacianVariance']:.1f}"]
    if metrics['suspectedUniformLossFraction'] >= 0.01:
        items.append(f"疑似内部均匀缺损占比 {metrics['suspectedUniformLossFraction']:.1%}")
    if metrics['smallComponentFraction'] is not None and metrics['smallComponentFraction'] >= 0.45:
        items.append(f"细碎连通域占比 {metrics['smallComponentFraction']:.1%}")
    items.append('原石风化无照片，不评定')
    items.append(grade)
    return items


def main():
    catalog = read_json(CATALOG_PATH)
    authorship = {path.stem: read_json(path) for path in (ROOT / 'data/catalog/authorship-verification').glob('*.json')}
    if len(authorship) != 28:
        raise SystemExit('authorship records must exist before assessment')
    restorer = AdaptiveRubbingRestorer()
    summaries = []
    for item in catalog:
        readable_url = item['imageAssets']['readable']
        archive_url = item['imageAssets']['archive']
        readable_path = public_path(readable_url)
        archive_path = public_path(archive_url)
        readable_bytes, readable = read_gray(readable_path)
        archive_bytes, archive = read_gray(archive_path)
        readable_metrics = measure(readable)
        archive_metrics = measure(archive)
        readable_grade, reasons = grade_from(readable_metrics)
        archive_grade, _archive_reasons = grade_from(archive_metrics)
        # The archive frame often includes mounting and page margins. Those uniform
        # regions are not the text leaf's damage, so the published grade follows
        # the readable leaf and the archive difference stays visible.
        grade = readable_grade
        if archive_metrics['suspectedUniformLossFraction'] >= 0.05:
            reasons.append(f"档案图疑似均匀区域占比 {archive_metrics['suspectedUniformLossFraction']:.1%}，可能来自裱边或扫描背景，不升为阅读图缺损")
        box, scope = crop_box(readable)
        x, y, x1, y1 = box
        crop = readable[y:y1, x:x1]
        run_id = f'{BATCH}-{item["id"]}'
        out_dir = results_root() / item['id'] / run_id
        started = time.time()
        error = None
        diagnostics = None
        output_sha = None
        try:
            output, diagnostics = restorer.restore(crop)
            elapsed_ms = (time.time() - started) * 1000
            output_sha = write_png(out_dir / 'restored.png', output)
            write_png(out_dir / 'input-crop.png', crop)
            archived = ASSESS_DIR / 'outputs' / f'{item["id"]}.png'
            archived.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(out_dir / 'restored.png', archived)
        except Exception as exc:
            elapsed_ms = (time.time() - started) * 1000
            error = f'{type(exc).__name__}: {exc}'
        gate = None if not diagnostics else diagnostics['fidelityGate']
        assessment = {
            'steleId': item['id'],
            'title': item['title'],
            'runId': run_id,
            'sourceImage': readable_path.relative_to(ROOT).as_posix(),
            'sourceImageSha256': sha_bytes(readable_bytes),
            'archiveImageSha256': sha_bytes(archive_bytes),
            'algorithmVersion': VERSION,
            'parameters': {'strength': 1.0, 'notchWidth': 0.8},
            'imageDimensions': {'readable': [int(readable.shape[1]), int(readable.shape[0])], 'archive': [int(archive.shape[1]), int(archive.shape[0])]},
            'coverage': '阅读图和档案图各一幅。册页若有多开，其余开页不在本次评级内。',
            'analysisScope': '阅读图全幅经等比例缩小后计算诊断；缩小只用于指标，不代替原图。',
            'restorationScope': scope,
            'cropBox': {'x': x, 'y': y, 'width': x1 - x, 'height': y1 - y, 'space': 'readable native pixels, right/bottom exclusive'},
            'partialResultIsNotFullFrame': scope != 'full_readable_frame',
            'processingTimeMs': elapsed_ms,
            # Same string as before for the default location; stays a /static/results-style path when relocated.
            'outputImage': None if output_sha is None else f"static/results/{item['id']}/{run_id}/restored.png",
            'archivedOutput': None if output_sha is None else f'data/catalog/assessments/outputs/{item["id"]}.png',
            'outputImageSha256': output_sha,
            'adaptiveDecisions': None if not diagnostics else diagnostics['decisions'],
            'fidelityGate': gate,
            'assessmentStatus': 'failed' if error else 'processed',
            'error': error,
            'imageCondition': grade,
            'readableGrade': readable_grade,
            'archiveGrade': archive_grade,
            'gradeRule': RULE,
            'gradeReasons': reasons,
            'readableMetrics': readable_metrics,
            'archiveMetrics': archive_metrics,
            'stoneWeathering': '无原石影像，不评定',
            'stoneWeatheringEvidence': [],
            'pairedGroundTruth': False,
            'psnr': None,
            'ssim': None,
            'evaluationStatus': '未评测',
            'humanReview': True,
            'humanReviewReason': '自动评级只使用全幅对比度、清晰度和均匀缺损比例。逐字残泐未人工判读。修复记录是中心 512 局部，不是全幅。',
            'observedIssues': observed(readable_metrics, grade),
            'limit': '诊断指标不能称为原石风化程度。无配对真值，不计算 PSNR 或 SSIM。',
        }
        write_json(ASSESS_DIR / f'{item["id"]}.json', assessment)
        item['imageCondition'] = grade
        item['stoneWeathering'] = '无原石影像，不评定'
        item['assessmentRunId'] = run_id
        item['assessmentScope'] = scope
        summaries.append(assessment)
        print(item['id'], grade, scope, 'gate', None if not gate else gate.get('accepted'), f'{elapsed_ms:.0f}ms', flush=True)
    write_json(CATALOG_PATH, catalog)
    sync_derived()
    write_review(catalog, authorship, summaries)
    print(json.dumps({'items': len(summaries), 'failed': sum(a['assessmentStatus'] != 'processed' for a in summaries)}, ensure_ascii=False))


def label(status):
    return {'verified': '已核定', 'pending_review': '有依据但待复核', 'disputed': '存在争议', 'unknown': '未核定', 'partial': '部分核定'}.get(status, status)


def person(record, key):
    value = record.get(key)
    status = record.get(key + 'Verification', 'unknown')
    name = '未核定' if not value or str(value).startswith('未核定') else value
    return f'{name}（{label(status)}）'


def write_review(catalog, authorship, summaries):
    by_assess = {row['steleId']: row for row in summaries}
    header = ['文物ID', '名称', '朝代', '撰文者与核验状态', '书丹者与核验状态', '核验来源', '图像损伤等级', '原石风化是否有证据', '可观察问题', '算法运行ID', '处理耗时毫秒', '输入SHA256', '输出SHA256', '算法门控', '是否有配对真值', 'PSNR', 'SSIM', '人工复核']
    REVIEW_CSV.parent.mkdir(parents=True, exist_ok=True)
    with REVIEW_CSV.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        lines = ['# 28件馆藏署名与拓本影像损伤复核', '', f'评级规则 `{RULE}`。原石风化没有原石照片时保持不评定。PSNR 与 SSIM 在没有配对真值时为未评测。', '']
        for item in catalog:
            auth = authorship[item['id']]
            assess = by_assess[item['id']]
            sources = '；'.join(sorted({entry['location'] for entry in auth['evidence']})) or '无新升级引文'
            gate = assess['fidelityGate'] or {}
            gate_text = '失败' if assess['error'] else ('通过' if gate.get('accepted') else '回退原图')
            issues = '；'.join(assess['observedIssues'])
            writer.writerow([
                item['id'], item['title'], item['dynasty'], person(item, 'author'), person(item, 'calligrapher'), sources,
                assess['imageCondition'], '否', issues, assess['runId'], f"{assess['processingTimeMs']:.1f}",
                assess['sourceImageSha256'], assess['outputImageSha256'] or '', gate_text, '否', '未评测', '未评测',
                '是' if assess['humanReview'] else '否',
            ])
            lines += [
                f"## {item['title']}（{item['id']}）",
                f"- 朝代与原刻：{item['dynasty']}，{item['originalYear']}。拓本：{item['rubbingPeriod']}。",
                f"- 撰文：{person(item, 'author')}。书丹：{person(item, 'calligrapher')}。篆额：{person(item, 'titleCalligrapher')}。刻工：{person(item, 'engraver')}。碑主或墓主：{person(item, 'steleSubject')}。",
                f"- 核定状态：{label(auth['verificationStatus'])}。来源：{sources}。",
                f"- 争议或限制：{'；'.join(row['detail'] for row in auth['conflicts']) or '无新增争议记录'}。",
                f"- 拓本影像损伤：{assess['imageCondition']}。依据：{'；'.join(assess['gradeReasons'])}。",
                f"- 覆盖范围：{assess['coverage']}尺寸 {assess['imageDimensions']['readable'][0]}×{assess['imageDimensions']['readable'][1]}。",
                f"- 原石风化：无原石影像，不评定。",
                f"- 算法：{assess['runId']}，{assess['restorationScope']}，耗时 {assess['processingTimeMs']:.1f} ms，门控 {gate_text}。",
                f"- 输入 SHA-256：`{assess['sourceImageSha256']}`。输出 SHA-256：`{assess['outputImageSha256'] or '无'}`。",
                '- 配对真值：无。PSNR、SSIM：未评测。',
                '',
            ]
        REVIEW_MD.write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
