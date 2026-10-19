"""Item A: relevance threshold calibrated on the 25 audit probes and unrelated queries."""
import pytest
import evidence_retrieval as er
from test_retrieval_regression_25 import AUDIT_25, EXPLICIT_DEMO

UNRELATED = ['今天天气怎么样', '明天股票会涨吗', '红烧肉怎么做', '量子计算机的原理是什么', '世界杯冠军是谁', '如何学习编程',
             '北京到上海的高铁多久', '推荐一部电影', '猫为什么喜欢纸箱', '番茄炒蛋放糖吗', '火星上有水吗', '怎么修自行车',
             '什么是区块链', '篮球规则', '咖啡因的作用']


@pytest.fixture(autouse=True)
def isolated_index(tmp_path, monkeypatch):
    monkeypatch.setattr(er, 'INDEX', tmp_path / 'evidence.sqlite')


@pytest.mark.parametrize('question', UNRELATED)
def test_unrelated_queries_return_no_weak_entries(question):
    result = er.query(question)
    assert result['status'] == 'insufficient_evidence'
    assert result['evidence'] == [] and result['relevanceFilter']['droppedBelowThreshold'] >= 0
    assert result['answer'] == '现有资料不足以回答该问题。'


def test_threshold_sits_above_every_unrelated_bm25_score(monkeypatch):
    # Recompute the calibration with the filter disabled; fails if corpus drift pushes unrelated scores over the threshold.
    monkeypatch.setattr(er, 'WEAK_BM25_THRESHOLD', float('-inf'))
    unrelated_max = max((e['bm25Score'] for q in UNRELATED for e in er.query(q)['evidence']), default=0.0)
    assert 0 < unrelated_max < 10.0


@pytest.mark.parametrize('question,scope,status,judgment,phrases', AUDIT_25)
def test_audit_results_keep_matched_evidence_and_label_weak(question, scope, status, judgment, phrases):
    result = er.query(question, scope, include_demo=question in EXPLICIT_DEMO)
    threshold = result['relevanceFilter']['weakBm25Threshold']
    for e in result['evidence']:
        assert e['entityMatched'] or e['bm25Score'] >= threshold
        if not e['entityMatched']:
            assert e['relevance'] == 'weak_keyword' and e['relevanceLabel'] == '弱相关，仅供参考'
    if result['status'] != 'insufficient_evidence':
        assert result['evidence'] and all(e['entityMatched'] for e in result['evidence'])


def test_keyword_only_refusal_is_labelled_weak():
    result = er.query('建义元年墓志的墓主是谁？')
    assert result['status'] == 'insufficient_evidence'
    assert result['evidence'] and all(e['relevanceLabel'] == '弱相关，仅供参考' for e in result['evidence'])
    assert result['relevanceFilter']['droppedBelowThreshold'] > 0  # 4 entries below 10.0 were dropped
