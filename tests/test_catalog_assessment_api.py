"""Archived assessment images stay readable without the gitignored results directory."""
import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from main import app

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)


def test_every_archived_assessment_image_matches_its_hash():
    catalog = client.get('/api/steles').json()
    museum = [row for row in catalog if row.get('source_kind') == 'verified_review_v3']
    assert len(museum) == 28
    for row in museum:
        assert row['imageConditionReviewStatus'] == '自动初筛，待人工复核'
        assert row['physicalStoneWeathering'] == '无可靠原石证据，不评定'
        assert row['weatheringLevel'] == '待评估'
        record = client.get(f'/api/catalog/{row["id"]}/assessment')
        assert record.status_code == 200, row['id']
        body = record.json()
        assert body['psnr'] is None and body['ssim'] is None
        assert body['imageConditionReviewStatus'] == '自动初筛，待人工复核'
        assert body['regionAnalysis']['publishedGradeUnchanged'] is True
        assert body['regionAnalysis']['publishedImageCondition'] == body['imageCondition']
        for kind, field in (('output', 'outputImageSha256'), ('input-roi', 'inputImageSha256')):
            asset = client.get(f'/api/catalog/{row["id"]}/assessment/assets/{kind}')
            assert asset.status_code == 200, (row['id'], kind)
            assert hashlib.sha256(asset.content).hexdigest() == body[field]
    missing = client.get('/api/catalog/not_a_stele/assessment')
    assert missing.status_code == 404
    escaped = client.get('/api/catalog/han_01_caoquan/assessment/assets/..%2F..%2Fmain.py')
    assert escaped.status_code == 404
    assert client.get('/api/glyph-evaluation').json()['top1'] is None


def test_region_boxes_stay_on_their_own_image_and_unchanged_pixels_match():
    from PIL import Image
    from catalog_assessment import asset_path, known_ids, public_record, region_crop
    unchanged = []
    for stele_id in sorted(known_ids()):
        record = public_record(stele_id)
        assert record['partialResultIsNotFullFrame'] is True
        assert record['restorationScope'] == 'partial_center_roi'
        assert len(record['regionOverlays']) == 9
        frame = record['imageDimensions']['readable']
        for item in record['regionOverlays']:
            box = item['box']
            assert item['confirmed'] is False
            assert box['x'] + box['width'] <= frame[0]
            assert box['y'] + box['height'] <= frame[1]
        before = Image.open(asset_path(stele_id, 'input-roi'))
        after = Image.open(asset_path(stele_id, 'output'))
        assert before.size == after.size == (record['cropBox']['width'], record['cropBox']['height'])
        if record['unchanged']:
            unchanged.append(stele_id)
            assert before.tobytes() == after.tobytes()
    assert unchanged == [
        'han_01_caoquan', 'han_04_shichen', 'ming_02_luxianzhi', 'qing_03_sanxitang_preface',
        'tang_01_duobao', 'tang_02_jiucheng', 'tang_03_yanjiamiao',
    ]
    sample = public_record('han_01_caoquan')['regionOverlays'][0]['box']
    crop = region_crop('han_01_caoquan', sample['x'], sample['y'], sample['width'], sample['height'])
    assert crop[:8] == b'\x89PNG\r\n\x1a\n'
    assert Image.open(__import__('io').BytesIO(crop)).size == (sample['width'], sample['height'])


def test_review_opinion_does_not_rewrite_the_automatic_grade(tmp_path, monkeypatch):
    import catalog_assessment
    monkeypatch.setattr(catalog_assessment, 'REVIEWS', tmp_path)
    response = client.post('/api/catalog/han_01_caoquan/assessment/review', json={
        'reviewer': '测试复核', 'damageTypes': ['无法判断'], 'note': '只看了局部，不能改等级。',
        'suggestedCondition': '中度影像损伤',
    })
    assert response.status_code == 200
    second = client.post('/api/catalog/han_01_caoquan/assessment/review', json={
        'reviewer': '第二次复核', 'damageTypes': ['无法判断'], 'note': '第二条意见，不能覆盖第一条。',
    })
    assert second.status_code == 200
    assert [item['note'] for item in second.json()['history']] == ['只看了局部，不能改等级。', '第二条意见，不能覆盖第一条。']
    assert second.json()['expertReview'] is False
    body = client.get('/api/catalog/han_01_caoquan/assessment').json()
    assert body['imageCondition'] == '轻度影像损伤'
    assert body['humanReview']['note'] == '第二条意见，不能覆盖第一条。'
    assert body['reviewHistory'][0]['note'] == '只看了局部，不能改等级。'
    assert '专家' not in body['imageConditionReviewStatus']
    assert catalog_assessment.review_allowed('203.0.113.8', None) is False
    assert catalog_assessment.review_allowed('127.0.0.1', None) is True
    rejected = client.post('/api/catalog/han_01_caoquan/assessment/review', json={
        'reviewer': '测试复核', 'damageTypes': ['伪造类型'], 'note': '不允许',
    })
    assert rejected.status_code == 400
