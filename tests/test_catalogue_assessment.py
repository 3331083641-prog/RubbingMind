"""The 28-work authorship and image-assessment records stay traceable."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def test_twenty_eight_roles_match_quotes_and_are_not_invented():
    catalog = {row['id']: row for row in load('data/catalog/steles28.json')}
    assert len(catalog) == 28
    dynasties = {}
    for stele_id, row in catalog.items():
        dynasties[row['dynasty']] = dynasties.get(row['dynasty'], 0) + 1
        record = load(f'data/catalog/authorship-verification/{stele_id}.json')
        assert record['steleId'] == stele_id
        for evidence in record['evidence']:
            text = (ROOT / evidence['location'].split('#', 1)[0]).read_text(encoding='utf-8').replace('\x00', '')
            assert evidence['quote'] in text
        for field, key in (('inscriptionAuthor', 'author'), ('calligrapher', 'calligrapher')):
            status = record[field]['verificationStatus']
            catalogue_status = row[key + 'Verification']
            if status == 'unknown' and row.get(key) not in (None, '未核定'):
                assert catalogue_status == 'pending_review'
            elif status != 'unknown':
                assert catalogue_status == status
            if catalogue_status != 'verified':
                assert record[field]['name'] is None or catalogue_status == 'pending_review'
        assert row['calligrapher'] != '王羲之'
        if stele_id == 'yuan_04_jingyuanchang':
            assert row['author'] == '未核定' and row['authorVerification'] == 'unknown'
        if stele_id == 'tang_01_duobao':
            assert row['author'] == '岑勋' and row['titleCalligrapher'] == '徐浩' and row['engraver'] == '史华'
    assert dynasties == {'东汉': 4, '北魏': 4, '唐代': 4, '宋代': 4, '元代': 4, '明代': 4, '清代': 4}


def test_assessments_have_real_runs_and_no_fake_similarity():
    catalog = load('data/catalog/steles28.json')
    for row in catalog:
        assessment = load(f'data/catalog/assessments/{row["id"]}.json')
        assert assessment['steleId'] == row['id']
        assert assessment['psnr'] is None and assessment['ssim'] is None
        assert assessment['evaluationStatus'] == '未评测'
        assert assessment['pairedGroundTruth'] is False
        assert assessment['stoneWeathering'] == '无原石影像，不评定'
        assert assessment['restorationScope'] == 'partial_center_roi'
        assert row['imageCondition'] == assessment['imageCondition']
        assert row['weatheringLevel'] == '待评估'
        if assessment['assessmentStatus'] == 'processed':
            archive = ROOT / assessment['archivedOutput']
            assert archive.is_file()
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()
            assert digest == assessment['outputImageSha256']
            runtime = ROOT / assessment['outputImage']
            if runtime.is_file():
                assert hashlib.sha256(runtime.read_bytes()).hexdigest() == digest
        else:
            assert assessment['error']
