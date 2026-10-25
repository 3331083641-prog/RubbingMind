"""Build data/catalog/id_mapping.json (draft, additive, reversible).

Legacy ids stay valid; every legacy id gets exactly one namespaced id. Demo samples
live in rm:demo: and never share an id with a collection rubbing (audit C-01).
Rollback: delete data/catalog/id_mapping.json; history_graph falls back to the
legacy ALIASES behaviour.

Usage: python scripts/build_id_mapping.py [--check]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data' / 'catalog'
OUT = CATALOG / 'id_mapping.json'

# Demo sample -> collection rubbing describing the same work. Human review pending.
DEMO_WORKS = {
    'tang-duobao': ('tang_01_duobao', 'rm:work:duobao-ta-ganying-bei'),
    'han-caoquan': ('han_01_caoquan', 'rm:work:caoquan-bei'),
}


def load(name):
    return json.loads((CATALOG / name).read_text(encoding='utf-8'))


def build():
    entries = []
    for record in load('steles28.json'):
        entries.append({'legacyId': record['id'], 'kind': 'rubbing', 'newId': 'rm:rubbing:' + record['id'],
                        'title': record['title'], 'collectionNumber': record['collectionNumber']})
    links = {item['coreSampleId']: item for item in load('core_sample_links.json')}
    for record in load('core_samples.json'):
        demo_id = record['id']
        entry = {'legacyId': demo_id, 'kind': 'demo_sample', 'newId': 'rm:demo:' + demo_id, 'title': record['title'],
                 'imageSubject': 'concept_demo', 'historyFile': f'data/history/{demo_id}.json'}
        if (record.get('textProvenance') or {}).get('kind') == 'synthetic_test_text':
            entry['textProvenance'] = 'synthetic_test_text'
        if demo_id in DEMO_WORKS:
            rubbing_id, work_id = DEMO_WORKS[demo_id]
            assert links[demo_id]['museumSteleId'] == rubbing_id
            entry['depictsSameWorkAs'] = {
                'rubbingId': rubbing_id, 'rubbingNewId': 'rm:rubbing:' + rubbing_id, 'workId': work_id,
                'relation': 'depicts_same_work_as', 'evidenceGrade': '待人工复核',
                'basis': 'core_sample_links.json: ' + links[demo_id]['note'],
                'historySubject': f'data/history/{demo_id}.json 的史料描述作品及馆藏拓本 {rubbing_id}，不描述演示图本身',
            }
        else:
            entry['depictsSameWorkAs'] = None
            entry['note'] = links[demo_id]['note']
        entries.append(entry)
    for alias, target in load('review_aliases.json').items():
        entries.append({'legacyId': alias, 'kind': 'review_alias', 'newId': 'rm:rubbing:' + target, 'aliasOf': target})
    for item in load('replacement_mapping.json'):
        entries.append({'legacyId': item['oldId'], 'kind': 'retired', 'newId': 'rm:retired:' + item['oldId'],
                        'recommendedId': item['newId'], 'note': '已下架；推荐记录为不同文物，不继承旧记录的任何史实'})
    legacy = [e['legacyId'] for e in entries]
    assert len(legacy) == len(set(legacy)), 'legacy ids must be unique'
    canonical = [e['newId'] for e in entries if e['kind'] != 'review_alias']
    assert len(canonical) == len(set(canonical)), 'namespaced ids must be unique'
    return {
        'version': 'draft-2026-10-19',
        'status': '草案：增量文件，现有 id 全部保留；删除本文件即回退到旧行为',
        'author': 'RM-金石史料',
        'namespaces': {
            'rm:rubbing:': '馆藏拓本记录，后缀等于现行 steles28.json id（无损）',
            'rm:demo:': '核心演示样本（概念演示图或合成测试图），不是馆藏实物',
            'rm:work:': '作品（碑文/志文本身）；与原石、拓本分开',
            'rm:retired:': '已下架记录；槽位编号不复用为同一文物',
        },
        'entries': entries,
    }


def render():
    return json.dumps(build(), ensure_ascii=False, indent=2) + '\n'


if __name__ == '__main__':
    text = render()
    if '--check' in sys.argv:
        current = OUT.read_text(encoding='utf-8') if OUT.exists() else ''
        print('id_mapping.json up to date' if current == text else 'id_mapping.json is stale')
        sys.exit(0 if current == text else 1)
    OUT.write_text(text, encoding='utf-8')
    print(f'wrote {OUT.relative_to(ROOT)} with {len(build()["entries"])} entries')
