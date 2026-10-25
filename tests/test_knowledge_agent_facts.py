"""C-17: legacy knowledge_agent data no longer carries contradicted facts, unsourced coordinates or a fake year fallback."""
import json
from pathlib import Path
import pytest
from knowledge_agent import AUTHENTIC_RUBBING_DATABASE as DB, knowledge_agent

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('query,year,gz', [
    ('天宝十一载', 752, '岁次壬辰年'), ('天宝十四载', 755, '岁次乙未年'), ('天宝十五载', 756, '岁次丙申年'),
    ('天宝元载', 742, '岁次壬午年'), ('唐天宝十一载', 752, '岁次壬辰年'), ('中平二年', 185, '岁次乙丑年'),
    ('熙平二年', 517, '岁次丁酉年'), ('建义元年', 528, '岁次戊申年'),
])
def test_era_conversion(query, year, gz):
    result = knowledge_agent.convert_ganzhi(query)
    assert result['supported'] is True and result['solar_year'] == year and result['ganzhi'] == gz


@pytest.mark.parametrize('query', ['天宝二十载', '天宝十六载', '天宝廿载', '天宝十十载', '天宝0载', '建义二年', 'xyz', '大概唐朝'])
def test_invalid_or_unknown_input_is_unsupported_not_752(query):
    result = knowledge_agent.convert_ganzhi(query)
    assert result['supported'] is False and result['solar_year'] is None and result['ganzhi'] is None


def test_matches_api_calendar_converter():
    from history_graph import convert_historical_year
    for query in ('天宝十一载', '天宝十四载', '天宝十五载', '中平二年', '熙平二年', '建义元年'):
        assert knowledge_agent.convert_ganzhi(query)['solar_year'] == convert_historical_year(query)['solar_year']


def test_no_unsourced_coordinates_remain():
    for sample in DB.values():
        for entry in sample.get('gis_timeline', []):
            assert entry['coord'] is None
            if entry.get('verification') == 'confirmed':
                assert entry['sourceUrl'].startswith('https://')


def test_caoquan_timeline_matches_museum_transcription():
    timeline = DB['sample_2.png']['gis_timeline']
    text = ' '.join(e['time'] + e['event'] for e in timeline)
    assert '熹平五年' not in text and '光和六年 (183)' in text
    assert next(e for e in timeline if '郃陽令' in e['event'])['time'].startswith('张角起兵后')
    assert any('酒泉祿福長' in e['event'] and e['time'].startswith('光和七年') for e in timeline)
    catalog = next(r for r in json.loads((ROOT / 'data/catalog/steles28.json').read_text(encoding='utf-8')) if r['id'] == 'han_01_caoquan')
    plain = catalog['transcription'].replace('\n', '')
    for quote in ('建寧二年。舉孝廉。除郎中。拜西域戊部司馬', '光和六年。復舉孝廉', '七年三月。除郎中。拜酒泉祿福長', '轉拜郃陽令'):
        assert quote in plain


def test_unsourced_locations_and_dates_are_marked():
    shown = json.dumps(DB, ensure_ascii=False)
    for phrase in ('第一室', '第三室', '752 年 5 月', '4 月 27 日', '御用书家', '洛阳古墓博物馆', '平阳王时期所生', '邙山之巅'):
        assert phrase not in shown, phrase
    yuan = DB['sample_3.png']
    assert '开封市博物馆' in yuan['location_now'] and '河南博物院' in yuan['location_now']
    assert '第四子' in yuan['host'] and '第五子' in yuan['host']
