"""C-03: wei-jianyi generator text must be labelled wherever it is shown or retrieved."""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from main import app
import evidence_retrieval as er
from history_graph import get_history_graph

ROOT = Path(__file__).resolve().parents[1]
LABEL = '合成测试文本（sample_generator 生成，非真实释文）'
client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_index(tmp_path, monkeypatch):
    monkeypatch.setattr(er, 'INDEX', tmp_path / 'evidence.sqlite')


@pytest.mark.parametrize('path', ['data/catalog/core_samples.json', 'apps/web/src/data/coreSamples.json'])
def test_core_sample_data_labels_synthetic_text(path):
    record = next(r for r in json.loads((ROOT / path).read_text(encoding='utf-8')) if r['id'] == 'wei-jianyi')
    assert record['textProvenance']['kind'] == 'synthetic_test_text'
    assert record['textProvenance']['label'] == LABEL and record['textProvenance']['isAuthenticInscription'] is False
    assert record['translation'].startswith('【' + LABEL + '】')
    demo = record['inferenceDemo']
    assert demo['transcript'].startswith('【' + LABEL + '】') and demo['damaged_summary'].startswith(LABEL)
    assert all(c['textKind'] == 'synthetic_test_text' for c in demo['characters'])


def test_frontend_and_backend_copies_are_identical():
    assert (ROOT / 'data/catalog/core_samples.json').read_bytes() == (ROOT / 'apps/web/src/data/coreSamples.json').read_bytes()


def test_other_core_samples_are_not_marked_synthetic():
    for record in json.loads((ROOT / 'data/catalog/core_samples.json').read_text(encoding='utf-8')):
        if record['id'] != 'wei-jianyi':
            assert 'textProvenance' not in record and LABEL not in record['translation']


def test_api_record_and_inference_carry_label():
    record = client.get('/api/steles/wei-jianyi').json()
    assert record['textProvenance']['label'] == LABEL and LABEL in record['translation']
    inference = client.get('/api/steles/wei-jianyi/infer').json()
    assert LABEL in inference['transcript'] and inference['textProvenance']['kind'] == 'synthetic_test_text'


def test_history_graph_carries_label():
    graph = get_history_graph('wei-jianyi', [])
    assert graph['textProvenance']['label'] == LABEL and graph['identity'].startswith(LABEL)
    assert LABEL in next(n for n in graph['nodes'] if n['id'] == 'wei-jianyi')['desc']


def test_retrieval_results_carry_label():
    # C-16: explicit demo selection is required for the synthetic sample to appear at all.
    result = er.query('北魏建义元年演示样本是否已经确认真实文物身份？', include_demo=True)
    assert result['evidence'] and all(e['steleId'] == 'wei-jianyi' for e in result['evidence'])
    assert all(e['text'].startswith('【' + LABEL + '】') for e in result['evidence'])
    assert all(e['textProvenance']['kind'] == 'synthetic_test_text' for e in result['evidence'])
    assert result['contentWarnings'] == [LABEL] and LABEL in result['answer']
    real = er.query('《多宝塔碑》的撰文者与书丹者是谁？')
    assert real['contentWarnings'] == [] and LABEL not in real['answer']


def test_legacy_sample_packs_carry_label():
    from knowledge_agent import AUTHENTIC_RUBBING_DATABASE
    from sample_generator import SYNTHETIC_TEXT_LABEL
    assert SYNTHETIC_TEXT_LABEL == LABEL
    assert AUTHENTIC_RUBBING_DATABASE['sample_4.png']['text_provenance'] == LABEL
