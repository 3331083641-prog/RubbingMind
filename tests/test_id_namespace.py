"""C-01: demo samples and collection rubbings never share one id; mapping is additive and reversible."""
import json
import subprocess
import sys
from pathlib import Path
import pytest
import history_graph as hg
import evidence_retrieval as er
from catalog import load

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_index(tmp_path, monkeypatch):
    monkeypatch.setattr(er, 'INDEX', tmp_path / 'evidence.sqlite')


def mapping():
    return json.loads((ROOT / 'data/catalog/id_mapping.json').read_text(encoding='utf-8'))


def test_mapping_file_is_up_to_date_and_lossless():
    result = subprocess.run([sys.executable, 'scripts/build_id_mapping.py', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    entries = mapping()['entries']
    legacy = [e['legacyId'] for e in entries]
    assert len(legacy) == len(set(legacy))
    rubbings = {e['legacyId'] for e in entries if e['kind'] == 'rubbing'}
    assert rubbings == {r['id'] for r in load('steles28.json')}
    assert all(e['newId'] == 'rm:rubbing:' + e['legacyId'] for e in entries if e['kind'] == 'rubbing')
    demos = {e['legacyId']: e for e in entries if e['kind'] == 'demo_sample'}
    assert set(demos) == set(hg.CORE_IDS)
    assert all(e['newId'].startswith('rm:demo:') for e in demos.values())
    assert not set(demos) & rubbings
    assert demos['wei-jianyi']['depictsSameWorkAs'] is None and demos['wei-yuanhuai']['depictsSameWorkAs'] is None
    for core in ('tang-duobao', 'han-caoquan'):
        assert demos[core]['depictsSameWorkAs']['evidenceGrade'] == '待人工复核'


@pytest.mark.parametrize('demo,rubbing', [('tang-duobao', 'tang_01_duobao'), ('han-caoquan', 'han_01_caoquan')])
def test_demo_and_rubbing_ids_resolve_to_different_entities(demo, rubbing):
    d, r = hg.resolve_id(demo), hg.resolve_id(rubbing)
    assert d['kind'] == 'demo_sample' and r['kind'] == 'rubbing'
    assert d['newId'] == 'rm:demo:' + demo and r['newId'] == 'rm:rubbing:' + rubbing
    demo_graph = hg.get_history_graph(demo, [])
    rubbing_graph = hg.get_history_graph(rubbing, [])
    assert demo_graph['steleId'] == demo and rubbing_graph['steleId'] == rubbing
    assert demo_graph['entity']['kind'] == 'demo_sample' and rubbing_graph['entity']['kind'] == 'rubbing'
    assert demo_graph['identity'].startswith('演示样本 rm:demo:' + demo) and rubbing in demo_graph['identity']
    assert rubbing_graph['demoSamples'] == ['rm:demo:' + demo]
    assert all(e['steleId'] == rubbing for e in rubbing_graph['events'])


def test_review_alias_and_retired_ids():
    alias = hg.resolve_id('qing_02_chongli_wushi')
    assert alias['kind'] == 'review_alias' and alias['evidenceId'] == 'qing_02_wushi_reerection'
    retired = hg.resolve_id('qing_01_shilang')
    assert retired['kind'] == 'retired' and retired['evidenceId'] == 'qing_01_shilang'


def test_retrieval_reports_scope_resolution():
    result = er.query('多宝塔感应碑的书丹者是谁？', 'tang-duobao')
    assert result['scopeSteleId'] == 'tang_01_duobao'
    assert result['scopeResolution']['kind'] == 'demo_sample'
    assert result['scopeResolution']['depictsSameWorkAs']['evidenceGrade'] == '待人工复核'


def test_rollback_without_mapping_restores_legacy_behaviour(monkeypatch, tmp_path):
    monkeypatch.setattr(hg, 'ID_MAPPING', tmp_path / 'missing.json')
    hg._mapping.cache_clear()
    try:
        assert hg.resolve_id('tang-duobao')['evidenceId'] == 'tang_01_duobao'
        assert hg.resolve_id('tang_01_duobao')['historyKey'] == 'tang-duobao'
        assert hg.get_history_graph('tang-duobao', [])['steleId'] == 'tang-duobao'
    finally:
        hg._mapping.cache_clear()
