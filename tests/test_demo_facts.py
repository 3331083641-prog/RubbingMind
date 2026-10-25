"""C-02: demo sample facts are sourced, marked unverified, or list conflicting sources side by side."""
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
UNSOURCED = ['第一室', '第三室', '752 年 5 月', '4 月 27 日', '御用书家', '洛阳古墓博物馆', '汉代书吏', '洛阳邙山出土']
CORE_FILES = ['data/catalog/core_samples.json', 'apps/web/src/data/coreSamples.json']


def records(path):
    return {r['id']: r for r in json.loads((ROOT / path).read_text(encoding='utf-8'))}


@pytest.mark.parametrize('path', CORE_FILES)
def test_no_unsourced_demo_fact_is_presented_as_fact(path):
    for record in records(path).values():
        shown = ' '.join(str(record.get(k, '')) for k in ('author', 'calligrapher', 'year', 'originalYear', 'location', 'dynasty'))
        for phrase in UNSOURCED:
            if phrase in shown:
                # Only allowed when explicitly flagged as the old unsourced value.
                assert '无来源' in shown, (record['id'], phrase)


@pytest.mark.parametrize('path', CORE_FILES)
def test_fact_sources_have_real_urls_or_are_unevaluated(path):
    for record in records(path).values():
        assert record['factSources'], record['id']
        for item in record['factSources']:
            assert item['grade'] in {'已验证', '有限支持', '未评测', '待人工复核'}
            if item['grade'] in {'已验证', '有限支持'}:
                assert str(item['sourceUrl']).startswith('https://'), (record['id'], item)
            else:
                assert item['sourceUrl'] is None and item['note']


def test_yuanhuai_conflicting_holdings_are_listed_side_by_side():
    record = records('data/catalog/core_samples.json')['wei-yuanhuai']
    assert record['location'].startswith('未核实')
    for phrase in ('开封市博物馆', '河南博物院', '张阳村', '张羊村'):
        assert phrase in record['location']
    urls = {i['sourceUrl'] for i in record['factSources'] if i['field'] == 'location'}
    assert len(urls) >= 2
    history = json.loads((ROOT / 'data/history/wei-yuanhuai.json').read_text(encoding='utf-8'))
    assert '开封市博物馆' in history['originalStoneCollection'] and '河南博物院' in history['originalStoneCollection']
    tomb = next(p for p in history['locations'] if p['id'] == 'yuan-tomb')
    assert tomb['longitude'] is None and '张阳村' in tomb['note'] and '张羊村' in tomb['note']


def test_caoquan_excerpt_matches_museum_transcription():
    demo = records('data/catalog/core_samples.json')['han-caoquan']['translation']
    catalog = next(r for r in json.loads((ROOT / 'data/catalog/steles28.json').read_text(encoding='utf-8')) if r['id'] == 'han_01_caoquan')
    assert '轉拜郃陽令' in demo and '轉拜郃陽令' in catalog['transcription'].replace('\n', '')
    assert '遷郃陽令' not in demo
