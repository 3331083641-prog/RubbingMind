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


def test_review_opinion_does_not_rewrite_the_automatic_grade(tmp_path, monkeypatch):
    import catalog_assessment
    monkeypatch.setattr(catalog_assessment, 'REVIEWS', tmp_path)
    response = client.post('/api/catalog/han_01_caoquan/assessment/review', json={
        'reviewer': '测试复核', 'damageTypes': ['无法判断'], 'note': '只看了局部，不能改等级。',
        'suggestedCondition': '中度影像损伤',
    })
    assert response.status_code == 200
    body = client.get('/api/catalog/han_01_caoquan/assessment').json()
    assert body['imageCondition'] == '轻度影像损伤'
    assert body['humanReview']['suggestedCondition'] == '中度影像损伤'
    assert '专家' not in body['imageConditionReviewStatus']
    rejected = client.post('/api/catalog/han_01_caoquan/assessment/review', json={
        'reviewer': '测试复核', 'damageTypes': ['伪造类型'], 'note': '不允许',
    })
    assert rejected.status_code == 400
