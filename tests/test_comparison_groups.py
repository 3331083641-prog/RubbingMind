"""Cross-work comparison groups: data-driven dimensions, verified catalogue values only, all 28 works covered."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'build_comparison_groups.py'
GROUPS = json.loads((ROOT / 'data/catalog/comparison_groups.json').read_text(encoding='utf-8'))
DIMS = json.loads((ROOT / 'data/catalog/comparison_dimensions.json').read_text(encoding='utf-8'))
CATALOGUE = {r['id']: r for r in json.loads((ROOT / 'data/catalog/steles28.json').read_text(encoding='utf-8'))}


def test_file_is_up_to_date():
    result = subprocess.run([sys.executable, str(SCRIPT), '--check'], capture_output=True, text=True, encoding='utf-8')
    assert result.returncode == 0, result.stdout + result.stderr


def test_dimensions_come_from_data_file():
    assert [d['id'] for d in GROUPS['dimensions']] == [d['id'] for d in DIMS['dimensions']]
    assert {d['id'] for d in DIMS['dimensions']} == {'calligrapher', 'dynasty', 'scriptType', 'rubbingCollectionInstitution'}
    spec = importlib.util.spec_from_file_location('cg', SCRIPT)
    source = SCRIPT.read_text(encoding='utf-8')
    for label in ('同书家', '同朝代', '同书体', '同收藏机构'):
        assert label not in source  # labels live only in comparison_dimensions.json
    assert spec is not None


def test_every_work_is_covered_in_every_dimension():
    for dim in GROUPS['dimensions']:
        grouped = [m['id'] for g in dim['groups'] for m in g['members']]
        excluded = [e['id'] for e in dim['excluded']]
        assert len(grouped) == len(set(grouped))
        assert sorted(grouped + excluded) == sorted(CATALOGUE), dim['id']
        assert dim['coverage'] == {'grouped': len(grouped), 'excluded': len(excluded), 'total': 28}


def test_only_verified_calligraphers_are_grouped():
    dim = next(d for d in GROUPS['dimensions'] if d['id'] == 'calligrapher')
    for group in dim['groups']:
        assert group['value'] != '未核定'
        for m in group['members']:
            record = CATALOGUE[m['id']]
            assert record['calligrapherVerification'] == 'verified' and record['calligrapher'] == group['value']
    for e in dim['excluded']:
        record = CATALOGUE[e['id']]
        assert record['calligrapherVerification'] != 'verified' or record['calligrapher'] == '未核定'


def test_member_values_match_catalogue_after_declared_normalisation():
    by_id = {d['id']: d for d in DIMS['dimensions']}
    for dim in GROUPS['dimensions']:
        rule = by_id[dim['id']]
        for group in dim['groups']:
            assert group['comparable'] == (group['size'] >= 2) and group['size'] == len(group['members'])
            for m in group['members']:
                raw = CATALOGUE[m['id']][rule['field']]
                assert rule['normalize'].get(raw, raw) == group['value']
                assert m.get('rawValue', raw) == raw


def test_institution_dimension_is_rubbing_not_stone():
    dim = next(d for d in GROUPS['dimensions'] if d['id'] == 'rubbingCollectionInstitution')
    assert dim['field'] == 'rubbingCollectionInstitution' and '拓本' in dim['objectLevel'] and '原石' in dim['objectLevel']
