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
    monkeypatch.setattr(glyph_annotations, 'RUNTIME_DIR', tmp_path / 'runtime')
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


def test_recorded_annotation_cannot_become_accuracy(tmp_path, monkeypatch):
    monkeypatch.setattr(glyph_annotations, 'ANNOTATION_DIR', tmp_path / 'catalog')
    monkeypatch.setattr(glyph_annotations, 'RUNTIME_DIR', tmp_path / 'runtime')
    saved = glyph_annotations.save_human_annotation({
        'steleId': 'han_01_caoquan', 'bbox': {'x': 1, 'y': 2, 'width': 8, 'height': 9},
        'glyph': '曹', 'sourceCitation': '测试出处，不是评测真值', 'annotator': '测试',
        'imageSha256': 'a' * 64, 'reviewStatus': 'human_verified', 'labelOrigin': 'human',
    })
    assert saved['reviewStatus'] == 'human_recorded'
    assert saved['countsAsAccuracy'] is False
    measured = glyph_annotations.evaluate()
    assert measured['evaluationStatus'] == 'unassessed'
    assert measured['top1'] is None
    assert measured['recordedLabels'] == 1
    try:
        glyph_annotations.save_human_annotation({
            'labelOrigin': 'model_prediction', 'reviewStatus': 'human_recorded', 'glyph': '曹',
            'steleId': 'han_01_caoquan', 'sourceCitation': 'x', 'annotator': 'x', 'imageSha256': 'b' * 64,
            'bbox': {'x': 0, 'y': 0, 'width': 1, 'height': 1},
        })
    except ValueError as exc:
        assert '模型预测' in str(exc)
    else:
        raise AssertionError('model prediction was stored')


def test_independent_stele_split_can_be_scored(tmp_path, monkeypatch):
    monkeypatch.setattr(glyph_annotations, 'ANNOTATION_DIR', tmp_path)
    monkeypatch.setattr(glyph_annotations, 'RUNTIME_DIR', tmp_path / 'runtime')
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
