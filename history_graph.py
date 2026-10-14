"""Evidence-only historical graphs. No inferred people, coordinates or journeys."""
import json
import re
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

HISTORY = Path(__file__).parent / 'data' / 'history'
CORE_IDS = ('tang-duobao', 'han-caoquan', 'wei-yuanhuai', 'wei-jianyi')
ALIASES = {'tang_01_duobao': 'tang-duobao', 'han_01_caoquan': 'han-caoquan'}

@lru_cache(maxsize=4)
def _read(stele_id):
    return json.loads((HISTORY / f'{stele_id}.json').read_text(encoding='utf-8'))

def get_history_graph(stele_id, records):
    canonical = ALIASES.get(stele_id, stele_id)
    if canonical in CORE_IDS:
        data = deepcopy(_read(canonical))
        all_sources = json.loads((HISTORY / 'sources.json').read_text(encoding='utf-8'))
        used = set(data['sourceIds']) | {p['sourceId'] for p in data['locations']}
        data['sources'] = [s for s in all_sources if s['id'] in used or s['id'] in ('tdt', 'beilin-coordinate')]
        # Compatibility field; no fabricated migration line or null coordinate point.
        locations = {p['id']: p for p in data['locations']}
        data['gis_route'] = [dict(name=e['title'], year=e['eraName'], event=e['description'],
                                  coords=[locations[e['locationId']]['longitude'], locations[e['locationId']]['latitude']])
                             for e in data['events'] if e['locationId'] in locations
                             and locations[e['locationId']]['longitude'] is not None]
        return data
    # Other museum records remain accessible, but no generic pseudo-history is created.
    record = next((s for s in records if s['id'] == stele_id), None)
    if record is None:
        return None
    return dict(steleId=stele_id, formalName=record['title'], yearCE=None, eraName='待考',
                image=record.get('raw_image', ''), imageStatus='馆藏目录图像', identity='尚未建立专项史料图谱',
                script=record.get('script_type','待考'), rubbingPeriod='待考', collectionNumber=record.get('collectionNumber','待考'),
                originalStoneCollection='待考', digitalRubbingCollection=record.get('collectionInstitution','待考'),
                authors=[], sourceIds=[], sources=[], locations=[], events=[], routes=[],
                nodes=[dict(id=stele_id,name=record['title'],category='stele',desc='该记录尚未建立专项史料关系；请选择四件核心样本。',
                            value=100,symbolSize=72,locationIds=[],sourceIds=[],verification='unverified')],links=[],gis_route=[])

ERAS = {'天宝': (742,756), '中平': (184,189), '熙平': (516,518), '建义': (528,528)}
ERA_DYNASTIES = {'天宝':'唐', '中平':'东汉', '熙平':'北魏', '建义':'北魏'}
DIGITS = {'元':1, '一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
def _number(s):
    if s.isdigit(): return int(s)
    if s in DIGITS: return DIGITS[s]
    if re.fullmatch(r'[一二三四五六七八九]?十[一二三四五六七八九]?', s):
        a,b=s.split('十',1)
        return DIGITS.get(a,1)*10 + DIGITS.get(b,0)
    return None

def convert_historical_year(query):
    query = re.sub(r'\s+', '', query)
    year = None
    era_text = None
    if re.fullmatch(r'(?:公元|公历)?[0-9]{1,4}年?', query):
        year = int(re.search(r'[0-9]+',query).group())
        if not 1 <= year <= 9999: year = None
    else:
        match = re.fullmatch(r'(唐|东汉|北魏)?(天宝|中平|熙平|建义)([元一二三四五六七八九十0-9]+)(?:年|载)',query)
        if match:
            dynasty, era, number = match.groups()
            n = _number(number)
            first,last = ERAS[era]
            if (not dynasty or dynasty == ERA_DYNASTIES[era]) and n and first <= first+n-1 <= last:
                year = first+n-1
                era_text = query
    if year is None:
        return {'supported':False,'solar_year':None,'ganzhi':None,'message':'暂不支持或待考证；请输入公元年份或受支持年号的有效年次。'}
    stems='甲乙丙丁戊己庚辛壬癸'
    branches='子丑寅卯辰巳午未申酉戌亥'
    animals='鼠牛虎兔龙蛇马羊猴鸡狗猪'
    return {'supported':True,'solar_year':year,'ganzhi':stems[(year-4)%10]+branches[(year-4)%12],
            'zodiac':animals[(year-4)%12],'era':era_text,'message':'年度对应；不推算古代朔闰、公历月日。'}
