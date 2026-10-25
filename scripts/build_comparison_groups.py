"""Build data/catalog/comparison_groups.json from steles28.json + comparison_dimensions.json.

Only catalogue values that pass each dimension's verification rule are grouped; every work appears in
every dimension either as a group member or in `excluded` with the reason. `--check` fails if the file is stale.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data' / 'catalog'
DIMENSIONS = CATALOG / 'comparison_dimensions.json'
OUTPUT = CATALOG / 'comparison_groups.json'


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    config = json.loads(DIMENSIONS.read_text(encoding='utf-8'))
    catalogue_path = ROOT / config['catalogueFile']
    records = json.loads(catalogue_path.read_text(encoding='utf-8'))
    out_dims = []
    for dim in config['dimensions']:
        groups, excluded = {}, []
        for r in records:
            raw = r.get(dim['field'])
            verification = r.get(dim['verificationField']) if dim['verificationField'] else None
            if raw in (None, '') or raw in dim['rejectValues']:
                excluded.append({'id': r['id'], 'title': r['title'], 'reason': f"{dim['field']} 为空或未核定"})
                continue
            if dim['acceptVerification'] and verification not in dim['acceptVerification']:
                excluded.append({'id': r['id'], 'title': r['title'], 'reason': f"{dim['verificationField']}={verification}，未达 verified"})
                continue
            value = dim['normalize'].get(raw, raw)
            member = {'id': r['id'], 'title': r['title'], 'dynasty': r['dynasty'], 'originalYearCE': r.get('originalYearCE')}
            if value != raw:
                member['rawValue'] = raw
            groups.setdefault(value, []).append(member)
        group_list = []
        for value, members in groups.items():
            members.sort(key=lambda m: (m['originalYearCE'] is None, m['originalYearCE'] or 0, m['id']))
            group_list.append({'value': value, 'size': len(members), 'comparable': len(members) >= 2, 'members': members})
        group_list.sort(key=lambda g: (-g['size'], g['value']))
        out_dims.append({
            'id': dim['id'], 'label': dim['label'], 'objectLevel': dim['objectLevel'], 'field': dim['field'],
            'basis': dim['basis'], 'groups': group_list, 'excluded': excluded,
            'coverage': {'grouped': sum(g['size'] for g in group_list), 'excluded': len(excluded), 'total': len(records)},
        })
    return {
        'schemaVersion': 1,
        'generator': 'scripts/build_comparison_groups.py',
        'dimensionsFile': 'data/catalog/comparison_dimensions.json',
        'dimensionsSha256': _sha(DIMENSIONS),
        'catalogueFile': config['catalogueFile'],
        'catalogueSha256': _sha(catalogue_path),
        'objectLevelNote': config['objectLevelNote'],
        'dimensions': out_dims,
    }


def render():
    return json.dumps(build(), ensure_ascii=False, indent=2) + '\n'


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail if comparison_groups.json is stale')
    args = parser.parse_args(argv)
    text = render()
    if args.check:
        current = OUTPUT.read_text(encoding='utf-8') if OUTPUT.exists() else ''
        ok = current == text
        print(json.dumps({'comparisonGroupsUpToDate': ok, 'file': 'data/catalog/comparison_groups.json'}, ensure_ascii=False))
        return 0 if ok else 1
    OUTPUT.write_text(text, encoding='utf-8', newline='\n')
    summary = {d['id']: {'groups': len(d['groups']), 'comparable': sum(g['comparable'] for g in d['groups']), **d['coverage']} for d in json.loads(text)['dimensions']}
    print(json.dumps({'wrote': 'data/catalog/comparison_groups.json', **summary}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
