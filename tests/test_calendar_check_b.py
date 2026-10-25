"""Item B: calendar check against 中研院兩千年中西曆轉換 — recorded, no claim field changed."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECK = json.loads((ROOT / 'data/catalog/calendar_check_B.json').read_text(encoding='utf-8'))
GZ = [a + b for a, b in zip('甲乙丙丁戊己庚辛壬癸' * 6, '子丑寅卯辰巳午未申酉戌亥' * 5)]


def _claim(stele, claim_id):
    def walk(o):
        if isinstance(o, dict):
            if o.get('claimId') == claim_id:
                yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    return next(walk(json.loads((ROOT / f'data/catalog/claims/{stele}.json').read_text(encoding='utf-8'))))


def test_every_query_records_parameters_and_what_was_read():
    assert CHECK['source']['endpoint'].startswith('https://sinocal.sinica.edu.tw/')
    for q in CHECK['queries']:
        assert {'dyna', 'king', 'reign', 'yy', 'mm', 'dd', 'swDate', 'lstype'} <= set(q['params'])
        assert q['resultRead'] and q['http']


def test_tang_01_stays_pending_and_unchanged():
    finding = next(f for f in CHECK['findings'] if f['claimId'] == 'tang_01_duobao:date:dayCrossCheck')
    assert finding['conclusion'] == '待复核' and finding['fieldChanged'] is False
    assert set(finding['threeWayClassification']) == {'ourCalculation', 'inscriptionVsCalendar', 'inscriptionOrTranscription'}
    claim = _claim('tang_01_duobao', 'tang_01_duobao:date:dayCrossCheck')
    assert claim['status'] == 'conflict' and claim['derivation']['newMoonGanzhi'] == '乙丑'
    # Arithmetic on both readings: 乙丑朔 → 22日 丙戌 (ours); 丁丑朔 (中研院) → 22日 戊戌 (inscription).
    assert GZ[(GZ.index('乙丑') + 21) % 60] == '丙戌' == claim['derivation']['computedDayGanzhi']
    assert GZ[(GZ.index('丁丑') + 21) % 60] == '戊戌' == claim['derivation']['inscriptionDayGanzhi']
    row = next(q for q in CHECK['queries'] if q['tag'] == 'tianbao11_4_22')
    assert any(r.startswith('4 丁丑') for r in row['monthRowRead'])


def test_no_claim_field_changed_and_failed_pages_are_marked():
    assert CHECK['claimFieldsChanged'] == 0 and all(f['fieldChanged'] is False for f in CHECK['findings'])
    failed = next(q for q in CHECK['queries'] if q['tag'] == 'tianbao01_1_1')
    assert failed['http'] != 200 and '未返回结果' in failed['resultRead'][0]
    zhongping = next(q for q in CHECK['queries'] if q['tag'] == 'zhongping02_10_1')
    assert GZ[(GZ.index('丙申') + 20) % 60] == '丙辰' and '丙辰' in zhongping['monthRowRead'][0]
