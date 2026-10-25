"""Evidence-only historical graphs. No inferred people, coordinates or journeys."""
import json
import re
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

HISTORY = Path(__file__).parent / 'data' / 'history'
ID_MAPPING = Path(__file__).parent / 'data' / 'catalog' / 'id_mapping.json'
CORE_IDS = ('tang-duobao', 'han-caoquan', 'wei-yuanhuai', 'wei-jianyi')
# Legacy compatibility export: collection rubbing id -> history file key.
# History files are named after demo ids, but tang/han files describe the work and
# its collection rubbing, not the demo image. resolve_id() makes that explicit (C-01).
ALIASES = {'tang_01_duobao': 'tang-duobao', 'han_01_caoquan': 'han-caoquan'}

@lru_cache(maxsize=4)
def _read(stele_id):
    return json.loads((HISTORY / f'{stele_id}.json').read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def _mapping():
    if not ID_MAPPING.is_file():
        return {}
    return {e['legacyId']: e for e in json.loads(ID_MAPPING.read_text(encoding='utf-8'))['entries']}


def resolve_id(stele_id):
    """Classify a legacy id without merging identities.

    Returns kind (rubbing / demo_sample / review_alias / retired / unknown), the
    namespaced id, which history file (if any) documents it, and the collection
    rubbing id that evidence should be filed under. Without id_mapping.json the
    legacy ALIASES behaviour is kept (rollback path).
    """
    if isinstance(stele_id, str) and stele_id.startswith('rm:'):
        # Namespaced ids (rm:demo:/rm:rubbing:/rm:retired:) resolve to their legacy entry, never across kinds.
        legacy = next((e['legacyId'] for e in _mapping().values() if e['newId'] == stele_id), None)
        if legacy is not None:
            return {**resolve_id(legacy), 'requestedId': stele_id}
    entry = _mapping().get(stele_id)
    if entry is None:
        history = ALIASES.get(stele_id, stele_id if stele_id in CORE_IDS else None)
        rubbing = {v: k for k, v in ALIASES.items()}.get(stele_id, stele_id)
        return {'requestedId': stele_id, 'kind': 'unknown', 'newId': None, 'historyKey': history,
                'evidenceId': rubbing, 'depictsSameWorkAs': None}
    kind = entry['kind']
    if kind == 'review_alias':
        target = resolve_id(entry['aliasOf'])
        return {**target, 'requestedId': stele_id, 'kind': 'review_alias', 'aliasOf': entry['aliasOf']}
    link = entry.get('depictsSameWorkAs')
    if kind == 'demo_sample':
        # RV-AI06: demo ids stay demo entities; depictsSameWorkAs is metadata only.
        history = stele_id
        evidence = stele_id
    else:
        history = ALIASES.get(stele_id)
        evidence = stele_id
    return {'requestedId': stele_id, 'kind': kind, 'newId': entry['newId'], 'historyKey': history,
            'evidenceId': evidence, 'depictsSameWorkAs': link}


def _demo_ids_for(rubbing_id):
    return [e['newId'] for e in _mapping().values()
            if e['kind'] == 'demo_sample' and (e.get('depictsSameWorkAs') or {}).get('rubbingId') == rubbing_id]



def _core_sample(demo_id):
    path = Path(__file__).parent / 'data' / 'catalog' / 'core_samples.json'
    if not path.is_file():
        return None
    return next((r for r in json.loads(path.read_text(encoding='utf-8')) if r.get('id') == demo_id), None)


def get_history_graph(stele_id, records):
    resolution = resolve_id(stele_id)
    canonical = resolution['historyKey']
    if canonical in CORE_IDS:
        data = deepcopy(_read(canonical))
        data['entity'] = resolution
        if resolution['kind'] == 'demo_sample':
            # RV-AI06: keep demo identity; never surface museum rubbing image paths from shared history.
            data['steleId'] = resolution['evidenceId']
            for event in data.get('events', []):
                event['steleId'] = resolution['evidenceId']
            core = _core_sample(resolution['evidenceId'])
            if core and core.get('raw_image'):
                data['image'] = core['raw_image']
                data['imageStatus'] = '演示样本图（非馆藏拓本影像）'
            if resolution['depictsSameWorkAs']:
                link = resolution['depictsSameWorkAs']
                data['identity'] = (f"演示样本 {resolution['newId']}（概念演示图）：本图谱史料描述对应作品及馆藏拓本 "
                                    f"{link['rubbingId']}，不描述演示图本身；同作品关系{link['evidenceGrade']}。" + data['identity'])
            else:
                data['identity'] = (f"演示样本 {resolution['newId']}（概念演示图或合成测试图，不是馆藏实物）。" + data['identity'])
        elif resolution['kind'] in ('rubbing', 'review_alias'):
            # Same history document, filed under the collection rubbing's own id.
            # Shared history JSON may carry demo artwork; museum entities must use reviewed rubbing assets.
            data['steleId'] = stele_id
            for event in data.get('events', []):
                event['steleId'] = stele_id
            data['demoSamples'] = _demo_ids_for(resolution['evidenceId'])
            record = next((s for s in (records or []) if s.get('id') == resolution['evidenceId']), None)
            if record:
                readable = (record.get('imageAssets') or {}).get('readable') or record.get('raw_image')
                if readable:
                    data['image'] = readable
                    data['imageStatus'] = record.get('imageStatus') or '真实馆藏拓本'
                if record.get('collectionNumber'):
                    data['collectionNumber'] = record['collectionNumber']
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
    roles=(('author','authorVerification','撰文'),('calligrapher','calligrapherVerification','书丹'),
           ('titleCalligrapher','titleCalligrapherVerification','篆额'),('engraver','engraverVerification','刻工'),
           ('steleSubject','steleSubjectVerification','碑主或墓主'))
    authors=[];nodes=[dict(id=stele_id,name=record['title'],category='stele',desc='已核定身份来自馆藏著录。待复核和未核定不生成人物节点，也不生成坐标。',
                            value=100,symbolSize=72,locationIds=[],sourceIds=[],verification='confirmed')];links=[]
    for field,status_field,relation in roles:
        value=record.get(field)
        if record.get(status_field)=='verified' and value and not str(value).startswith('未核定'):
            person=stele_id+':'+field
            authors.append(f'{value} · {relation}')
            nodes.append(dict(id=person,name=value,category='person',desc=relation,value=70,symbolSize=46,locationIds=[],sourceIds=[],verification='confirmed'))
            links.append(dict(source=stele_id,target=person,relation=relation,sourceUrl=record.get('sourceUrl'),verification='confirmed'))
    return dict(steleId=stele_id, formalName=record['title'], yearCE=record.get('originalYearCE'), eraName=record.get('originalYear') or record.get('year') or '未核定',
                image=record.get('raw_image', ''), imageStatus=record.get('imageStatus') or '馆藏目录图像', identity='馆藏著录中的已核定关系；没有坐标证据时不画迁移路线。',
                script=record.get('script_type','未核定'), rubbingPeriod=record.get('rubbingPeriod') or '未核定', collectionNumber=record.get('collectionNumber','未核定'),
                originalStoneCollection=record.get('physicalCollectionInstitution') or record.get('currentLocation') or '未核定',
                digitalRubbingCollection=record.get('collectionInstitution') or '未核定',
                authors=authors, sourceIds=[], sources=[], locations=[], events=[], routes=[],
                nodes=nodes,links=links,gis_route=[])

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
