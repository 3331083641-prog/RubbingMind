"""Phase 3 deepening, batch 1: per-work claims (data/catalog/claims/).

Checks the schema, that every claim has sources and a legal evidence level, that quotes appear verbatim
in the files they cite, that unverified catalogue fields are never raised to 已验证, that no coordinates
are present, and that the era/ganzhi/CE cross-checks are recomputed consistently.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / 'data/catalog/claims'
SCHEMA = json.loads((CLAIMS / 'schema.json').read_text(encoding='utf-8'))
INDEX = json.loads((CLAIMS / 'index.json').read_text(encoding='utf-8'))
CATALOGUE = {r['id']: r for r in json.loads((ROOT / 'data/catalog/steles28.json').read_text(encoding='utf-8'))}
LEVELS = SCHEMA['$defs']['claim']['properties']['evidenceLevel']['enum']
GZ = [a + b for a, b in zip('甲乙丙丁戊己庚辛壬癸' * 6, '子丑寅卯辰巳午未申酉戌亥' * 5)]
UNKNOWN = ('未核定', '未核实', '待考', '年代待考', '未确认', '待评估', '待核')
ROLE_FIELDS = {'author', 'calligrapher', 'titleCalligrapher', 'engraver', 'steleSubject'}
WORKS = [w['steleId'] for w in INDEX['works']]


def load_claims(stele_id):
    return json.loads((CLAIMS / f'{stele_id}.json').read_text(encoding='utf-8'))


def validate(value, schema, path='$'):
    """Minimal JSON Schema subset used by schema.json (no third-party dependency)."""
    if '$ref' in schema:
        return validate(value, SCHEMA['$defs'][schema['$ref'].split('/')[-1]], path)
    if 'oneOf' in schema:
        matches = 0
        for option in schema['oneOf']:
            try:
                validate(value, {**{k: v for k, v in schema.items() if k != 'oneOf'}, **option}, path)
                matches += 1
            except AssertionError:
                pass
        assert matches == 1, f'{path}: matches {matches} oneOf branches'
        return
    if 'const' in schema:
        assert value == schema['const'], f'{path}: {value!r} != {schema["const"]!r}'
    if 'enum' in schema:
        assert value in schema['enum'], f'{path}: {value!r} not in enum'
    kind = schema.get('type')
    if kind == 'object':
        assert isinstance(value, dict), path
        for key in schema.get('required', []):
            assert key in value, f'{path}: missing {key}'
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            assert not set(value) - set(props), f'{path}: unexpected {set(value) - set(props)}'
        for key, sub in props.items():
            if key in value:
                validate(value[key], sub, f'{path}.{key}')
    elif kind == 'array':
        assert isinstance(value, list), path
        assert len(value) >= schema.get('minItems', 0), f'{path}: too few items'
        for n, item in enumerate(value):
            validate(item, schema.get('items', {}), f'{path}[{n}]')
    elif kind == 'string':
        assert isinstance(value, str), path
        assert len(value) >= schema.get('minLength', 0), path
        if 'pattern' in schema:
            assert re.search(schema['pattern'], value), path


def norm(text):
    return re.sub(r'\s+', '', text)


def field_text(path, field, record_id=None):
    data = json.loads((ROOT / path).read_text(encoding='utf-8'))
    if record_id is not None:
        data = next(r for r in data if r['id'] == record_id)
    for part in field.split('.'):
        data = data[part]
    return data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)


def all_sources(claim):
    yield from claim['sources']
    for alternative in claim.get('alternatives', []):
        yield from alternative['sources']


def test_batch_is_six_and_includes_required_works():
    assert len(WORKS) == 18 and {'tang_01_duobao', 'han_01_caoquan'} <= set(WORKS)
    assert INDEX['remaining'] == 10 and all(w['selectionBasis'] for w in INDEX['works'])
    assert sorted(p.stem for p in CLAIMS.glob('*.json') if p.stem not in ('schema', 'index')) == sorted(WORKS)


@pytest.mark.parametrize('stele_id', WORKS)
def test_schema_and_index_counts(stele_id):
    doc = load_claims(stele_id)
    validate(doc, SCHEMA)
    entry = next(w for w in INDEX['works'] if w['steleId'] == stele_id)
    assert entry['claimCount'] == len(doc['claims'])
    assert len({c['claimId'] for c in doc['claims']}) == len(doc['claims'])
    assert all(c['claimId'].startswith(stele_id + ':') for c in doc['claims'])


@pytest.mark.parametrize('stele_id', WORKS)
def test_sources_levels_and_missing_reasons(stele_id):
    for claim in load_claims(stele_id)['claims']:
        assert claim['evidenceLevel'] in LEVELS
        if claim['status'] == 'missing':
            assert claim['value'] is None and claim['missingReason'] and claim['evidenceLevel'] == '未评测'
        else:
            assert claim['sources'], claim['claimId']
        if claim['status'] == 'conflict':
            values = [a['value'] for a in claim['alternatives']]
            assert len(values) >= 2 and len(set(map(str, values))) == len(values) and claim['note']
            assert claim['evidenceLevel'] != '已验证'


@pytest.mark.parametrize('stele_id', WORKS)
def test_quotes_and_catalogue_values_are_verbatim(stele_id):
    opened = {u['url'] for u in INDEX['openedUrls']}
    for claim in load_claims(stele_id)['claims']:
        for source in all_sources(claim):
            if source['type'] == 'catalogue':
                record = CATALOGUE[source['id']]
                value = record
                for part in source['field'].split('.'):
                    value = value[part]
                assert value == source['value'], (claim['claimId'], source['field'])
            elif source['type'] == 'file':
                text = field_text(source['path'], source['field'], source.get('id'))
                assert norm(source['quote']) in norm(text), (claim['claimId'], source['quote'])
            else:
                assert source['url'] in opened, (claim['claimId'], source['url'])


@pytest.mark.parametrize('stele_id', WORKS)
def test_unverified_catalogue_fields_are_not_raised_to_verified(stele_id):
    record = CATALOGUE[stele_id]
    for claim in load_claims(stele_id)['claims']:
        field = claim.get('catalogueField')
        if not field:
            continue
        value = record.get(field)
        unverified = value is None or str(value).startswith(UNKNOWN)
        if field in ROLE_FIELDS:
            unverified = unverified or record.get(field + 'Verification') != 'verified'
        if unverified:
            assert claim['evidenceLevel'] != '已验证', claim['claimId']
        if 'catalogueValue' in claim:
            assert claim['catalogueValue'] == value, claim['claimId']


@pytest.mark.parametrize('stele_id', WORKS)
def test_no_coordinates_and_region_level_places(stele_id):
    text = (CLAIMS / f'{stele_id}.json').read_text(encoding='utf-8')
    for key in ('longitude', 'latitude', '"coords"', 'gis_lng', 'gis_lat', '"lng"', '"lat"'):
        assert key not in text
    assert not re.search(r'\d{2,3}\.\d{2,}\s*,\s*\d{1,2}\.\d{2,}', text)
    for claim in load_claims(stele_id)['claims']:
        if claim['entity'] == 'place' or 'region' in claim:
            if claim['status'] != 'missing':
                assert claim['region']['precision'] == 'region'


@pytest.mark.parametrize('stele_id', WORKS)
def test_required_coverage(stele_id):
    present = {(c['entity'], c['property']) for c in load_claims(stele_id)['claims']}
    for entity, properties in SCHEMA['x-requiredCoverage'].items():
        assert any(e == entity for e, _p in present), (stele_id, entity)
        for prop in properties:
            assert (entity, prop) in present, (stele_id, entity, prop)


@pytest.mark.parametrize('stele_id', WORKS)
def test_era_ganzhi_ce_cross_checks_recompute(stele_id):
    for claim in load_claims(stele_id)['claims']:
        derivation = claim.get('derivation') or {}
        if 'ce' in derivation:
            computed = GZ[(derivation['ce'] - 4) % 60]
            assert derivation['computedGanzhi'] == computed
            inscription = derivation['inscriptionGanzhi']
            expected = 'partial' if inscription is None else ('consistent' if inscription == computed else 'inconsistent')
            assert derivation['result'] == expected, claim['claimId']
            if expected == 'inconsistent':
                assert claim['status'] == 'conflict'
        if 'newMoonGanzhi' in derivation:
            day = GZ[(GZ.index(derivation['newMoonGanzhi']) + derivation['day'] - 1) % 60]
            assert derivation['computedDayGanzhi'] == day
            assert (derivation['result'] == 'inconsistent') == (day != derivation['inscriptionDayGanzhi'])
            assert derivation['result'] != 'inconsistent' or claim['status'] == 'conflict'


def test_known_conflicts_are_kept_side_by_side():
    by_id = {c['claimId']: c for w in WORKS for c in load_claims(w)['claims']}
    assert by_id['tang_02_jiucheng:stone:currentLocation']['status'] == 'conflict'
    assert by_id['tang_04_xuanmita:stone:transfer']['status'] == 'conflict'
    assert by_id['ming_02_luxianzhi:work:objectNature']['status'] == 'conflict'
    assert by_id['tang_01_duobao:date:dayCrossCheck']['status'] == 'conflict'
    # C-05 cross-source items stay below 已验证 while the catalogue field is unverified.
    for cid in ('tang_01_duobao:stone:currentLocation', 'tang_01_duobao:rubbing:period', 'han_01_caoquan:stone:currentLocation'):
        assert by_id[cid]['evidenceLevel'] == '有限支持'


def test_catalogue_is_not_modified_by_claims():
    import hashlib
    diff = json.loads((ROOT / 'data/catalog/c08_sync_diff.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT / 'data/catalog/steles28.json').read_bytes()).hexdigest() == diff['basis']['catalogueSha256']
