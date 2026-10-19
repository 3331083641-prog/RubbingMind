"""Namespaced IDs and the optional reviewed ID mapping (ARCHITECTURE_DECISIONS R1-5 / R2).

* `data/catalog/id_mapping.json` is authored by RM-金石史料 on agent/jinshi. This
  module only reads it; when it is absent the mapping is empty and nothing fails.
* Namespaces: rm:rubbing:<collection id>, rm:demo:<core sample id>,
  rm:retired:<old id>, rm:work:<work id> (works are not addressable as steles).
* Identities are never merged and runs/inferences are never aggregated here
  (Green decision 1; no relation is human-reviewed yet). Every record keeps
  its own sourceSteleId.
"""
from __future__ import annotations

import json
from functools import lru_cache

from catalog import BASE, load

MAPPING_PATH = BASE / 'data' / 'catalog' / 'id_mapping.json'
PREFIXES = {'rm:rubbing:': 'rubbing', 'rm:demo:': 'demo_sample', 'rm:retired:': 'retired', 'rm:work:': 'work'}
REVIEWED = 'human_reviewed'


@lru_cache(maxsize=1)
def _catalog_ids():
    museum = {r['id'] for r in load('steles28.json')}
    core = {r['id'] for r in load('core_samples.json')}
    retired = {r['oldId'] for r in load('replacement_mapping.json')}
    aliases = dict(load('review_aliases.json'))
    return museum, core, retired, aliases


def load_mapping() -> dict:
    """Read on every call (small file) so tests and a newly merged file need no restart."""
    path = MAPPING_PATH
    if not path.is_file():
        return {'available': False, 'source': None, 'version': None, 'status': None, 'namespaces': {},
                'entries': [], 'mappingError': None}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        entries = [e for e in data.get('entries') or [] if isinstance(e, dict) and e.get('legacyId')]
        return {'available': True, 'source': 'data/catalog/id_mapping.json', 'version': data.get('version'),
                'status': data.get('status'), 'namespaces': data.get('namespaces') or {}, 'entries': entries,
                'mappingError': None}
    except (OSError, ValueError, AttributeError) as exc:
        return {'available': False, 'source': 'data/catalog/id_mapping.json', 'version': None, 'status': None,
                'namespaces': {}, 'entries': [], 'mappingError': f'id_mapping.json 无法解析：{type(exc).__name__}'}


def split_namespace(raw: str):
    for prefix, kind in PREFIXES.items():
        if raw.startswith(prefix):
            return prefix, kind, raw[len(prefix):]
    return None, None, raw


def _derived_kind(local: str) -> str:
    museum, core, retired, aliases = _catalog_ids()
    if local in core:
        return 'demo_sample'
    if local in museum:
        return 'rubbing'
    if local in aliases:
        return 'review_alias'
    if local in retired:
        return 'retired'
    if local.startswith('upload-'):
        return 'upload'
    return 'unknown'


def namespace_mismatch(raw: str) -> str | None:
    """Error text when a namespaced id names the wrong kind of record; None when acceptable."""
    prefix, kind, local = split_namespace(raw)
    if prefix is None:
        return None
    actual = _derived_kind(local)
    if kind == 'work':
        return 'rm:work: 是作品标识，不对应单件拓本或演示样本'
    if kind == 'rubbing' and actual not in ('rubbing', 'review_alias'):
        return f'{raw} 不是馆藏拓本'
    if kind == 'demo_sample' and actual != 'demo_sample':
        return f'{raw} 不是演示样本'
    if kind == 'retired' and actual != 'retired':
        return f'{raw} 不是已下架记录'
    return None


def local_id(raw: str) -> str:
    return split_namespace(raw)[2]


def resolve(raw: str, mapping: dict | None = None) -> dict:
    """Classify an id without merging identities (BR-03 `entity`)."""
    mapping = mapping if mapping is not None else load_mapping()
    prefix, _, local = split_namespace(raw)
    entry = next((e for e in mapping['entries'] if e.get('legacyId') == local), None)
    kind = (entry or {}).get('kind') or _derived_kind(local)
    derived_prefix = {'rubbing': 'rm:rubbing:', 'demo_sample': 'rm:demo:', 'retired': 'rm:retired:'}.get(kind)
    link = (entry or {}).get('depictsSameWorkAs')
    result = {
        'requestedId': raw, 'localId': local, 'kind': kind,
        'newId': (entry or {}).get('newId') or (derived_prefix + local if derived_prefix else None),
        'namespaceGiven': prefix,
        'depictsSameWorkAs': link,
        'relationReviewed': bool(link and (link.get('reviewStatus') == REVIEWED)),
        'mappingSource': mapping['source'] if entry else None,
    }
    if kind == 'review_alias':
        result['aliasOf'] = (entry or {}).get('aliasOf') or _catalog_ids()[3].get(local)
    if kind == 'demo_sample':
        result['demoNote'] = '演示样本（概念演示图或合成测试图），不是馆藏实物'
    return result


def mapping_overview() -> dict:
    mapping = load_mapping()
    return {
        **mapping,
        'prefixes': PREFIXES,
        'aggregation': {'enabled': False, 'reason': '没有经人工复核（reviewStatus=human_reviewed）的关系；运行与推演按来源 ID 分开。'},
        'unreviewedLegacyLinks': {'source': 'data/catalog/core_sample_links.json', 'reviewStatus': 'unreviewed',
                                  'usedForAggregation': False, 'links': load('core_sample_links.json')},
    }


class NamespacedSteleIdMiddleware:
    """Accept /api/steles/rm:<ns>:<id>/... by rewriting to the legacy id, so every endpoint
    (and its storage) keeps using the unchanged legacy id. Bare ids pass through untouched."""
    PREFIX = '/api/steles/'

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http' and scope['path'].startswith(self.PREFIX + 'rm:'):
            rest = scope['path'][len(self.PREFIX):]
            raw, sep, tail = rest.partition('/')
            error = namespace_mismatch(raw)
            if error:
                from starlette.responses import JSONResponse
                return await JSONResponse({'detail': error}, status_code=404)(scope, receive, send)
            path = self.PREFIX + local_id(raw) + sep + tail
            scope = dict(scope, path=path, raw_path=path.encode('utf-8'))
        return await self.app(scope, receive, send)
