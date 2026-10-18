import json

import glyph_annotations


def _label(annotation_id, stele_id, split, origin='human_fixture'):
    return {
        'annotationId': annotation_id, 'steleId': stele_id, 'bbox': {'x': 0, 'y': 0, 'w': 16, 'h': 16},
        'glyph': '十', 'sourceCitation': 'fixture citation, not a historical label', 'annotator': 'fixture',
        'reviewStatus': 'human_verified', 'damageLevel': 'synthetic', 'split': split, 'labelOrigin': origin,
    }


def test_unverified_or_overlapping_labels_stay_unassessed(tmp_path, monkeypatch):
    monkeypatch.setattr(glyph_annotations, 'ANNOTATION_DIR', tmp_path)
    assert glyph_annotations.evaluate()['evaluationStatus'] == 'unassessed'
    assert glyph_annotations.evaluate()['top1'] is None
    (tmp_path / 'labels.json').write_text(json.dumps([
        _label('train', 'stele-a', 'train'),
        _label('test', 'stele-a', 'test'),
        {**_label('model', 'stele-b', 'test', 'model_prediction'), 'glyph': '口'},
    ]), encoding='utf-8')
    refused = glyph_annotations.evaluate([{'annotationId': 'test', 'candidates': [{'glyph': '十'}], 'status': 'pending_review'}])
    assert refused['evaluationStatus'] == 'unassessed'
    assert refused['top1'] is None
    assert refused['excludedBecauseSteleOverlap'] == 1


def test_independent_stele_split_can_be_scored(tmp_path, monkeypatch):
    monkeypatch.setattr(glyph_annotations, 'ANNOTATION_DIR', tmp_path)
    (tmp_path / 'labels.json').write_text(json.dumps([
        _label('train', 'stele-a', 'train'),
        _label('test', 'stele-b', 'test'),
    ]), encoding='utf-8')
    measured = glyph_annotations.evaluate([
        {'annotationId': 'test', 'candidates': [{'glyph': '十'}, {'glyph': '口'}], 'status': 'pending_review'}
    ])
    assert measured['evaluationStatus'] == 'measured'
    assert measured['top1'] == 1 and measured['top3'] == 1 and measured['rejectionRate'] == 0
    assert measured['independentTestLabels'] == 1
