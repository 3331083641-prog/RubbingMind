"""Read-only access to eval-sci derived files (REPORT_DATA_SPEC §0.1 DER / CI rows).

applied_status: per-row label written by eval-sci `experiments/derive_applied_status.py` into
`experiments/results/<batch>/derived/applied_status.json` (appliedStatus ∈ processed / passthrough /
passthrough_not_applicable / processed_not_applicable_label / undetermined; criterion pixel-equal-v1).
ci_by_artifact: artifact-clustered bootstrap CIs written by `experiments/ci_by_artifact.py`.

The backend computes no statistic here: it serves the files as written, after checking that they
belong to the requested batch and still match the result files they were derived from. A missing,
mismatched or stale file gives an explicit status, never another batch's data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import experiment_registry

APPLIED_STATUS = 'applied_status.json'
CI_BY_ARTIFACT = 'ci_by_artifact.json'
APPLIED_KEYS = ('criterion', 'imagesAvailable', 'note', 'derivedAt', 'derivedBy', 'sourceResultsSha256',
                'summaryByMethod', 'summaryBySplitMethod', 'summaryByMethodDegradation')
CI_KEYS = ('derivedAt', 'derivedBy', 'seed', 'bootstrap', 'percentiles', 'minReliableArtifacts', 'rngRule', 'gainDefinition',
           'scopeSource', 'sourceResultsSha256', 'appliedStatusSha256', 'rowN', 'artifactN', 'comparisonWithGroupedSummary')
CI_FILTERS = ('split', 'method', 'degradation', 'scope')
SERVED_BY = '后端只读转发评测科学家生成的派生文件，不重算任何统计量'


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry_entry(experiment_id: str):
    return next((entry for entry in experiment_registry.batches() if entry['id'] == experiment_id), None)


def batch_index() -> dict:
    """One-to-one experimentId <-> batch (results directory) mapping, from the registry itself."""
    entries = experiment_registry.batches()
    by_batch = {entry['directory']: entry['id'] for entry in entries}
    if len(by_batch) != len(entries):  # cannot happen with one results.json per directory; fail loudly if it does
        raise RuntimeError('实验登记中 batch（目录名）与 experimentId 不是一一对应')
    return {'items': [{'experimentId': entry['id'], 'batch': entry['directory']} for entry in entries],
            'basis': 'batch = experiments/results 下的目录名；experimentId 为权威参数，batch 仅作可读别名'}


def resolve_batch(batch: str):
    return next((item for item in batch_index()['items'] if item['batch'] == batch), None)


def _derived(entry: dict, name: str):
    path = experiment_registry.RESULTS / entry['directory'] / 'derived' / name
    return path if path.is_file() else None


def _base(entry: dict, name: str, path):
    return {'experimentId': entry['id'], 'batch': entry['directory'],
            'file': f"experiments/results/{entry['directory']}/derived/{name}", 'servedBy': SERVED_BY,
            'fileSha256': _sha(path) if path else None}


def _check_identity(entry: dict, data: dict, results_sha: str) -> list[str]:
    problems = []
    if data.get('experimentId') not in (None, entry['id']):
        problems.append(f"文件声明的 experimentId={data.get('experimentId')} 与请求的批次不一致")
    if data.get('batch') not in (None, entry['directory']):
        problems.append(f"文件声明的 batch={data.get('batch')} 与请求的批次目录不一致")
    if data.get('sourceResultsSha256') and data['sourceResultsSha256'] != results_sha:
        problems.append('派生文件的 sourceResultsSha256 与当前 results.json 不一致（结果已变化，派生文件过期）')
    if not data.get('sourceResultsSha256'):
        problems.append('派生文件没有记录 sourceResultsSha256，无法核对来源')
    return problems


def applied_status(experiment_id: str, include_rows: bool = False):
    entry = registry_entry(experiment_id)
    if entry is None:
        return None
    path = _derived(entry, APPLIED_STATUS)
    out = _base(entry, APPLIED_STATUS, path)
    if path is None:
        return {**out, 'available': False, 'status': 'missing',
                'reason': '本批次没有 derived/applied_status.json（由评测科学家 experiments/derive_applied_status.py 生成）'}
    data = json.loads(path.read_text('utf-8'))
    problems = _check_identity(entry, data, _sha(experiment_registry.RESULTS / entry['directory'] / 'results.json'))
    if problems:
        return {**out, 'available': False, 'status': 'stale', 'reason': '；'.join(problems)}
    body = {key: data.get(key) for key in APPLIED_KEYS}
    if include_rows:
        body['rows'] = data.get('rows') or []
    else:
        body['rowCount'] = len(data.get('rows') or [])
    return {**out, 'available': True, 'status': 'ok', **body}


def ci_by_artifact(experiment_id: str, filters: dict | None = None):
    entry = registry_entry(experiment_id)
    if entry is None:
        return None
    path = _derived(entry, CI_BY_ARTIFACT)
    out = _base(entry, CI_BY_ARTIFACT, path)
    if path is None:
        return {**out, 'available': False, 'status': 'missing',
                'reason': '本批次没有按文物聚类的 CI 文件（REPORT_DATA_SPEC §0.1 只为 2026-10-17-v2 与 2026-10-17-v2-text 计算）'}
    data = json.loads(path.read_text('utf-8'))
    problems = _check_identity(entry, data, _sha(experiment_registry.RESULTS / entry['directory'] / 'results.json'))
    status_path = _derived(entry, APPLIED_STATUS)
    if data.get('appliedStatusSha256') and (status_path is None or _sha(status_path) != data['appliedStatusSha256']):
        problems.append('CI 文件记录的 appliedStatusSha256 与当前 applied_status.json 不一致（口径来源已变化）')
    if problems:
        return {**out, 'available': False, 'status': 'stale', 'reason': '；'.join(problems)}
    groups = data.get('groups') or []
    active = {key: value for key, value in (filters or {}).items() if key in CI_FILTERS and value}
    if active:
        groups = [group for group in groups if all(str(group.get(key)) == value for key, value in active.items())]
    # ES-3: annotate claim labels from existing CI fields (no bootstrap recompute).
    from experiments.eval_export_contract import annotate_ci_lift_claims

    annotated_payload = annotate_ci_lift_claims({'groups': groups}, 'psnr')
    return {**out, 'available': True, 'status': 'ok', **{key: data.get(key) for key in CI_KEYS},
            'filters': active, 'groupCount': len(annotated_payload['groups']),
            'groups': annotated_payload['groups'],
            'liftClaimSummary': annotated_payload['liftClaimSummary'],
            'liftClaimRule': annotated_payload['liftClaimRule']}


# --- mechanism layer PNGs (eval-sci derived/mechanism/, ~253 PNGs) ---
MECHANISM_DIR = 'mechanism'
MECHANISM_INDEX = 'index.json'


def mechanism_root(entry: dict) -> Path:
    return experiment_registry.RESULTS / entry['directory'] / 'derived' / MECHANISM_DIR


def mechanism_index(experiment_id: str):
    entry = registry_entry(experiment_id)
    if entry is None:
        return None
    root = mechanism_root(entry)
    index_path = root / MECHANISM_INDEX
    out = {'experimentId': entry['id'], 'batch': entry['directory'],
           'root': f"experiments/results/{entry['directory']}/derived/mechanism",
           'available': index_path.is_file() or root.is_dir(),
           'servedBy': '只读转发评测科学家 mechanism 层 PNG；路径经 resolve 后必须落在白名单根目录内'}
    if not out['available']:
        return {**out, 'status': 'missing', 'reason': '本批次没有 derived/mechanism/（由评测科学家 experiments/mechanism_cases.py 生成）', 'cases': []}
    cases = []
    if index_path.is_file():
        try:
            data = json.loads(index_path.read_text('utf-8'))
            cases = data if isinstance(data, list) else data.get('cases') or data.get('items') or []
        except ValueError:
            cases = []
    if not cases and root.is_dir():
        cases = [{'caseId': p.name} for p in sorted(root.iterdir()) if p.is_dir()]
    return {**out, 'status': 'ok', 'cases': cases}


def resolve_mechanism_png(experiment_id: str, relative: str):
    """Return a Path inside derived/mechanism/ for a .png, or (None, reason).

    Rejects .., absolute paths, URL encoding tricks, and symlink escapes: the resolved path
    must stay under the mechanism root (Path.is_relative_to).
    """
    entry = registry_entry(experiment_id)
    if entry is None:
        return None, '实验批次不存在'
    if not relative or relative.startswith('/') or '\\' in relative:
        return None, '路径不合法'
    # decode once; reject encoded separators and parent refs after decoding
    from urllib.parse import unquote
    decoded = unquote(relative)
    if decoded != relative and ('..' in decoded or decoded.startswith('/') or '\\' in decoded):
        return None, '路径不合法（编码穿越）'
    if '..' in relative.split('/'):
        return None, '路径不合法（含 ..）'
    if not decoded.lower().endswith('.png'):
        return None, '只允许 .png'
    root = mechanism_root(entry).resolve()
    if not root.is_dir():
        return None, '本批次没有 mechanism 目录'
    try:
        target = (root / decoded).resolve()
    except (OSError, ValueError):
        return None, '路径无法解析'
    try:
        target.relative_to(root)
    except ValueError:
        return None, '路径越界：解析后不在 mechanism 根目录内'
    if target.is_symlink():
        # even if resolve() followed it inside, refuse symlinks as a defense in depth
        return None, '拒绝符号链接'
    if not target.is_file():
        return None, '文件不存在'
    return target, None


def resolve_report_derived(experiment_id: str, relative: str):
    """Compatibility reader for the report's existing /derived/ URLs.

    Only registered result derivatives and listed mechanism images are exposed.
    Frozen files are never rewritten or silently upgraded to current evidence.
    Returns (path, HTTP status, reason).
    """
    from urllib.parse import unquote

    entry = registry_entry(experiment_id)
    if entry is None:
        return None, 404, '实验批次不存在'
    decoded = unquote(relative)
    parts = relative.split('/')
    if (not relative or decoded != relative or relative.startswith('/')
            or '\\' in relative or ':' in relative or any(p in ('', '.', '..') for p in parts)):
        return None, 400, '派生文件路径不合法'
    names = (APPLIED_STATUS, CI_BY_ARTIFACT, 'negative_lift_causes.json')
    is_root = len(parts) == 1 and relative in names
    is_index = parts == ['mechanism', 'index.json']
    is_case = (len(parts) == 3 and parts[0] == 'mechanism'
               and (parts[2] == 'mechanism.json' or parts[2].endswith('.png')))
    if not (is_root or is_index or is_case):
        return None, 404, '未登记的报告派生文件'
    root = (experiment_registry.RESULTS / entry['directory'] / 'derived').resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        return None, 400, '派生文件路径越界'
    if not path.is_file():
        return None, 404, '本批次没有这份派生文件'
    if is_root:
        if relative in (APPLIED_STATUS, CI_BY_ARTIFACT):
            checked = (applied_status(experiment_id, include_rows=True)
                       if relative == APPLIED_STATUS else ci_by_artifact(experiment_id))
            if not checked['available']:
                return None, 409 if checked['status'] == 'stale' else 404, checked['reason']
        else:
            data = json.loads(path.read_text('utf-8'))
            problems = _check_identity(entry, data, _sha(experiment_registry.RESULTS / entry['directory'] / 'results.json'))
            if problems:
                return None, 409, '；'.join(problems)
    if is_index or is_case:
        index_path = root / 'mechanism' / 'index.json'
        if not index_path.is_file() or not index_path.resolve().is_relative_to(root):
            return None, 404, '机制案例登记不存在'
        index = json.loads(index_path.read_text('utf-8'))
        if index.get('batch') != entry['directory']:
            return None, 409, '机制案例登记与批次不一致'
        if is_case:
            if parts[1] not in {c.get('caseId') for c in index.get('cases', [])}:
                return None, 404, '未登记的机制案例'
            detail_path = root / 'mechanism' / parts[1] / 'mechanism.json'
            if not detail_path.is_file() or not detail_path.resolve().is_relative_to(root):
                return None, 404, '机制案例内容不存在'
            detail = json.loads(detail_path.read_text('utf-8'))
            if detail.get('caseId') != parts[1] or detail.get('batch') != entry['directory']:
                return None, 409, '机制案例内容与登记不一致'
            if parts[2].endswith('.png'):
                image = next((i for i in detail.get('images', []) if i.get('file') == parts[2]), None)
                if not image or not image.get('sha256'):
                    return None, 404, '未登记的机制影像'
                if _sha(path) != image['sha256']:
                    return None, 409, '机制影像 SHA-256 不匹配'
    return path, 200, None
