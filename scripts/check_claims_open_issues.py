# -*- coding: utf-8 -*-
"""Scan claims open issues; --check vs CLAIMS_OPEN_ISSUES.md; --write regenerate ledger.

Open kinds:
  - status == conflict
  - evidenceLevel == 待人工复核
  - reviewFlags non-empty
  - catalogue *Verification == pending_review and claim not raised to 已验证
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / 'data/catalog/claims'
CATALOGUE = ROOT / 'data/catalog/steles28.json'
LEDGER = ROOT / 'docs/product-upgrade/CLAIMS_OPEN_ISSUES.md'
ROLE_FIELDS = ('author', 'calligrapher', 'titleCalligrapher', 'engraver', 'steleSubject')
DYNASTY_ORDER = ['东汉', '北魏', '唐代', '宋代', '元代', '明代', '清代']


def load_catalogue():
    return {r['id']: r for r in json.loads(CATALOGUE.read_text(encoding='utf-8'))}


def scan(cat=None):
    cat = cat or load_catalogue()
    rows = []
    for path in sorted(CLAIMS.glob('*.json')):
        if path.stem in ('schema', 'index'):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        sid = doc['steleId']
        record = cat.get(sid, {})
        dynasty = record.get('dynasty') or '?'
        for claim in doc['claims']:
            kinds = []
            if claim.get('status') == 'conflict':
                kinds.append('conflict')
            if claim.get('evidenceLevel') == '待人工复核':
                kinds.append('pending_human')
            flags = claim.get('reviewFlags') or []
            if flags:
                kinds.append('review_flag')
            field = claim.get('catalogueField')
            if field in ROLE_FIELDS and record.get(field + 'Verification') == 'pending_review':
                if claim.get('evidenceLevel') != '已验证':
                    kinds.append('catalogue_pending_review')
            if not kinds:
                continue
            alts = [str(a.get('value')) for a in claim.get('alternatives') or []]
            sources = []
            for src in claim.get('sources') or []:
                if src.get('type') == 'url':
                    sources.append(f"url:{src.get('publisher')}")
                elif src.get('type') == 'catalogue':
                    sources.append(f"cat:{src.get('field')}")
                elif src.get('type') == 'file':
                    sources.append(f"file:{src.get('path')}:{src.get('field')}")
            for alt in claim.get('alternatives') or []:
                for src in alt.get('sources') or []:
                    if src.get('type') == 'url':
                        sources.append(f"url:{src.get('publisher')}")
            rows.append({
                'steleId': sid,
                'title': doc.get('title') or record.get('title'),
                'dynasty': dynasty,
                'claimId': claim['claimId'],
                'entity': claim.get('entity'),
                'property': claim.get('property'),
                'status': claim.get('status'),
                'evidenceLevel': claim.get('evidenceLevel'),
                'value': claim.get('value'),
                'note': claim.get('note'),
                'missingReason': claim.get('missingReason'),
                'alternatives': alts,
                'reviewFlags': flags,
                'kinds': sorted(set(kinds)),
                'catalogueField': field,
                'catalogueValue': claim.get('catalogueValue'),
                'catalogueVerification': record.get((field or '') + 'Verification') if field in ROLE_FIELDS else None,
                'sources': list(dict.fromkeys(sources)),
            })
    return rows


def severity(row):
    prop = row['property'] or ''
    if row['status'] == 'conflict':
        if prop in ('dynasty', 'objectNature', 'dayCrossCheck', 'yearCrossCheck', 'ce',
                    'currentLocation', 'transfer', 'script'):
            return '高（影响分期/载体/历日/书体归属）'
        if prop in ('calligrapher', 'author', 'engraver', 'authorDispute',
                    'authorFieldConflict', 'authorEraConflict'):
            return '中（人物角色异文）'
        return '中（异文并列）'
    if 'catalogue_pending_review' in row['kinds'] or row['evidenceLevel'] == '待人工复核':
        return '中（待人工复核／未抬升）'
    if 'review_flag' in row['kinds']:
        return '高（显式 reviewFlag）'
    return '低'


def sides(row):
    if row['alternatives']:
        return ' ｜ '.join(f'「{a}」' for a in row['alternatives'][:4])
    if row['value'] is not None:
        value = str(row['value'])
        if len(value) > 80:
            value = value[:80] + '…'
        extra = ''
        if row.get('catalogueVerification') == 'pending_review':
            extra = f'（目录 {row["catalogueField"]}Verification=pending_review；claims 未抬升为已验证）'
        return f'主张：{value}{extra}'
    if row['status'] == 'missing':
        return f'缺失：{row.get("missingReason") or "未评测"}（目录字段 pending_review 未抬升）'
    return row.get('note') or '—'


def suggest(row):
    prop = row['property'] or ''
    if prop in ('dayCrossCheck', 'yearCrossCheck', 'ce', 'gregorianDay', 'eventDate'):
        return '对照碑面纪年／干支与历表（或馆方 Dates 字段）复核；只核验一致性，不改写目录。'
    if prop == 'dynasty':
        return '对照馆方 Period/Culture 标签与刻石纪年、作者生卒；区分遗迹语境标签与本件新刻朝代。'
    if prop == 'objectNature':
        return '对照馆方分类与题跋原文，必要时目验拓本／墨迹载体；确认是否存在原刻层。'
    if prop == 'script':
        return '对照馆方书体栏、释文标注与目录 scriptType；异文保持并列。'
    if prop in ('calligrapher', 'author', 'engraver', 'titleCalligrapher', 'steleSubject',
                'authorDispute', 'authorFieldConflict', 'authorEraConflict'):
        return '对照馆方 Maker／作者栏、碑面署款与目录角色字段／Verification；pending_review 勿升已验证。'
    if prop in ('currentLocation', 'transfer', 'sourceStone', 'dimensions'):
        return '对照多家馆方现藏／迁徙说明与尺寸著录；多源异文并列。'
    if 'review_flag' in row['kinds']:
        return '按 reviewFlags 提示做载体／鉴定复核。'
    return '对照馆方页与目录字段；保持开项，不臆断合并。'


def counts(rows):
    return {
        'openRows': len({r['claimId'] for r in rows}),
        'conflict': sum(1 for r in rows if 'conflict' in r['kinds']),
        'pendingHuman': sum(1 for r in rows if 'pending_human' in r['kinds']),
        'reviewFlag': sum(1 for r in rows if 'review_flag' in r['kinds']),
        'cataloguePendingReview': sum(1 for r in rows if 'catalogue_pending_review' in r['kinds']),
        'claimFiles': len([p for p in CLAIMS.glob('*.json') if p.stem not in ('schema', 'index')]),
    }


def render(rows):
    for row in rows:
        row['severity'] = severity(row)
        row['sides'] = sides(row)
        row['suggest'] = suggest(row)
    stats = counts(rows)
    by_dynasty = Counter(r['dynasty'] for r in rows)
    by_sev = Counter(r['severity'] for r in rows)
    by_prop = Counter(r['property'] for r in rows if 'conflict' in r['kinds'])
    lines = []
    add = lines.append
    add('# Claims 开项台账（冲突／待人工复核）')
    add('')
    add('> **口径（Green 2026-10-25）：** claim 文件已齐 **28/28**，不等于开项关闭。')
    add('> 本文件只汇总 `conflict` 异文并列、`evidenceLevel=待人工复核`、`reviewFlags`、以及目录 `*Verification=pending_review` 且未抬升为「已验证」的条目。')
    add('> **不定论、不合并异文、不改写已审证据。** 建议动作仅为人工复核提示。')
    add('')
    add('- 生成时间（Asia/Shanghai）：2026-10-25')
    add(f'- 扫描范围：`data/catalog/claims/*.json`（{stats["claimFiles"]} 件作品文件）+ `steles28.json` Verification 字段')
    add('- 校验脚本：`scripts/check_claims_open_issues.py --check`')
    add('')
    add('## 统计摘要')
    add('')
    add('| 指标 | 数量 |')
    add('|---|---:|')
    add(f'| claim 文件 | {stats["claimFiles"]}/28 |')
    add(f'| 开项行（去重 claimId） | {stats["openRows"]} |')
    add(f'| 其中 status=conflict | {stats["conflict"]} |')
    add(f'| 其中 evidenceLevel=待人工复核 | {stats["pendingHuman"]} |')
    add(f'| 含 reviewFlags | {stats["reviewFlag"]} |')
    add(f'| 目录 pending_review 未抬升 | {stats["cataloguePendingReview"]} |')
    add('')
    add('### 按朝代（开项行）')
    add('')
    add('| 朝代 | 开项行 |')
    add('|---|---:|')
    for dynasty in DYNASTY_ORDER:
        if by_dynasty.get(dynasty):
            add(f'| {dynasty} | {by_dynasty[dynasty]} |')
    for dynasty, n in sorted(by_dynasty.items()):
        if dynasty not in DYNASTY_ORDER:
            add(f'| {dynasty} | {n} |')
    add('')
    add('### 按严重度分组（仅便于排期，非史实结论）')
    add('')
    add('| 分组 | 开项行 |')
    add('|---|---:|')
    for key, n in sorted(by_sev.items(), key=lambda item: (-item[1], item[0])):
        add(f'| {key} | {n} |')
    add('')
    add('### 冲突字段分布（status=conflict）')
    add('')
    add('| property | 条数 |')
    add('|---|---:|')
    for key, n in by_prop.most_common():
        add(f'| {key} | {n} |')
    add('')
    # --- JS-4: conflict parallel listing ---
    conflicts = [r for r in rows if 'conflict' in r['kinds']]
    conflicts.sort(key=lambda item: (
        DYNASTY_ORDER.index(item['dynasty']) if item['dynasty'] in DYNASTY_ORDER else 99,
        item['claimId'],
    ))
    add('## 冲突并列一览（JS-4 · status=conflict）')
    add('')
    add(f'> 异文两侧并列，**不定论、不合并、不关闭**。共 **{len(conflicts)}** 条（与统计摘要 conflict 一致）。')
    add('> 用途：人工对照馆方页／碑面／目录时，一眼看到两侧主张；关闭须有新证据并改对应 claims JSON。')
    add('')
    add('| # | claimId | 作品 | 字段 | 侧 A | 侧 B／更多 | 建议人工动作 |')
    add('|---:|---|---|---|---|---|---|')
    for i, row in enumerate(conflicts, 1):
        alts = row['alternatives'] or []
        if len(alts) >= 2:
            side_a = str(alts[0]).replace('|', '\\|').replace('\n', ' ')
            side_b = ' ｜ '.join(str(x).replace('|', '\\|').replace('\n', ' ') for x in alts[1:4])
        else:
            side_a = (row['sides'] or '—').replace('|', '\\|').replace('\n', ' ')
            side_b = '—'
        if len(side_a) > 100:
            side_a = side_a[:100] + '…'
        if len(side_b) > 120:
            side_b = side_b[:120] + '…'
        add(
            f"| {i} | `{row['claimId']}` | {row['steleId']} | "
            f"{row['entity']}.{row['property']} | {side_a} | {side_b} | {row['suggest']} |"
        )
    add('')
    # --- JS-5: human review checklist ---
    review_rows = [
        r for r in rows
        if ('pending_human' in r['kinds']
            or 'catalogue_pending_review' in r['kinds']
            or 'review_flag' in r['kinds'])
    ]
    seen = set()
    checklist = []
    for row in sorted(
        review_rows,
        key=lambda item: (
            DYNASTY_ORDER.index(item['dynasty']) if item['dynasty'] in DYNASTY_ORDER else 99,
            0 if 'conflict' in item['kinds'] else 1,
            item['claimId'],
        ),
    ):
        cid = row['claimId']
        if cid in seen:
            continue
        seen.add(cid)
        checklist.append(row)
    kind_label_short = {
        'conflict': 'conflict',
        'pending_human': '待人工复核',
        'review_flag': 'reviewFlag',
        'catalogue_pending_review': '目录pending_review未抬升',
    }
    add('## 待人工复核工作清单（JS-5）')
    add('')
    add(f'> 供人工逐条勾选；**脚本与台账不自动关闭**。去重 claimId 共 **{len(checklist)}** 条仍开放。')
    add('> 含 `evidenceLevel=待人工复核`、目录 `*Verification=pending_review` 未抬升、`reviewFlags`。勾选仅表示人工已看过，关闭开项仍须改 claims JSON 并有证据。')
    add('')
    add('| ☐ | claimId | 作品 | 类型摘要 | 建议人工动作 |')
    add('|---|---|---|---|---|')
    for row in checklist:
        kinds = '、'.join(kind_label_short[k] for k in row['kinds'])
        if row['reviewFlags']:
            kinds += '（' + '；'.join(row['reviewFlags']) + '）'
        add(
            f"| ☐ | `{row['claimId']}` | {row['steleId']} | {kinds} | {row['suggest']} |"
        )
    add('')
    add('## 明细')
    add('')
    add('说明：同一 claim 可同时属于多种开项类型（如 conflict 且待人工复核）。')
    add('')
    by_stele = defaultdict(list)
    for row in rows:
        by_stele[row['steleId']].append(row)
    ordered = []
    for sid, items in by_stele.items():
        dynasty = items[0]['dynasty']
        rank = DYNASTY_ORDER.index(dynasty) if dynasty in DYNASTY_ORDER else 99
        ordered.append((rank, sid, items))
    ordered.sort()
    kind_label = {
        'conflict': 'conflict',
        'pending_human': '待人工复核',
        'review_flag': 'reviewFlag',
        'catalogue_pending_review': '目录pending_review未抬升',
    }
    for _rank, sid, items in ordered:
        add(f'### {sid} · {items[0]["title"]}（{items[0]["dynasty"]}）')
        add('')
        add('| claimId | 字段 | 类型 | 两侧／主张摘要 | 来源 | 证据等级 | 建议人工动作 |')
        add('|---|---|---|---|---|---|---|')
        for row in sorted(items, key=lambda item: (0 if 'conflict' in item['kinds'] else 1, item['claimId'])):
            kinds = '、'.join(kind_label[k] for k in row['kinds'])
            if row['reviewFlags']:
                kinds += f"（{'；'.join(row['reviewFlags'])}）"
            src = '；'.join(row['sources'][:6]) or '—'
            sides_text = (row['sides'] or '—').replace('|', '\\|').replace('\n', ' ')
            add(
                f"| `{row['claimId']}` | {row['entity']}.{row['property']} | {kinds} | "
                f"{sides_text} | {src} | {row['evidenceLevel']} | {row['suggest']} |"
            )
        add('')
    add('## 维护约定')
    add('')
    add('1. 新增／关闭开项时：先改对应 `data/catalog/claims/<id>.json`，再运行 `python scripts/check_claims_open_issues.py --check`（或 `--write` 重生成本文件）。')
    add('2. 关闭条件须人工确认；脚本不自动消除 conflict／待人工复核。')
    add('3. C-08 主库禁止 `--apply`；本台账不触发目录或 SQLite 写回。')
    add('4. 用语：写「claim 文件 28/28，开项 N 条」；勿写「收官关闭／冲突全部关闭」。')
    add('5. JS-4／JS-5：本文件「冲突并列一览」与「待人工复核工作清单」为呈现与人工排期用；claim 文件 28/28 + 开项台账/--check 已闭环功能，但开项仍开放（不等于史实定论关闭）。')
    add('')
    return '\n'.join(lines) + '\n', stats


def claim_ids_in_ledger(text: str) -> set[str]:
    return set(re.findall(r'`([a-z0-9_]+(?::[a-zA-Z0-9_]+)+)`', text))


def parse_stat(text: str, label: str) -> int | None:
    match = re.search(rf'\|\s*{re.escape(label)}\s*\|\s*(\d+)\s*\|', text)
    return int(match.group(1)) if match else None


def check(rows):
    if not LEDGER.exists():
        print(f'FAIL: missing ledger {LEDGER}', file=sys.stderr)
        return 2
    text = LEDGER.read_text(encoding='utf-8')
    expected = {r['claimId'] for r in rows}
    found = claim_ids_in_ledger(text)
    missing = sorted(expected - found)
    extra = sorted(found - expected)
    stats = counts(rows)
    errors = []
    if missing:
        errors.append(f'ledger missing claimIds: {missing}')
    if extra:
        errors.append(f'ledger extra claimIds: {extra}')
    mapping = {
        '开项行（去重 claimId）': 'openRows',
        '其中 status=conflict': 'conflict',
        '其中 evidenceLevel=待人工复核': 'pendingHuman',
        '含 reviewFlags': 'reviewFlag',
        '目录 pending_review 未抬升': 'cataloguePendingReview',
    }
    for label, key in mapping.items():
        value = parse_stat(text, label)
        if value is None:
            errors.append(f'ledger missing stat row: {label}')
        elif value != stats[key]:
            errors.append(f'stat mismatch {label}: ledger={value} scan={stats[key]}')
    files_stat = re.search(r'\|\s*claim 文件\s*\|\s*(\d+)/28\s*\|', text)
    if not files_stat:
        errors.append('ledger missing claim 文件 N/28 row')
    elif int(files_stat.group(1)) != stats['claimFiles']:
        errors.append(f'claim files mismatch: ledger={files_stat.group(1)} scan={stats["claimFiles"]}')
    if '## 冲突并列一览' not in text:
        errors.append('ledger missing JS-4 section: ## 冲突并列一览')
    if '## 待人工复核工作清单' not in text:
        errors.append('ledger missing JS-5 section: ## 待人工复核工作清单')
    if '不等于开项关闭' not in text and '开项仍' not in text:
        errors.append('ledger must state claim files ≠ open-item closure')
    if errors:
        for err in errors:
            print('FAIL:', err, file=sys.stderr)
        return 1
    print(json.dumps({'ok': True, **stats}, ensure_ascii=False))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true', help='verify ledger matches live claims scan')
    parser.add_argument('--write', action='store_true', help='regenerate docs/product-upgrade/CLAIMS_OPEN_ISSUES.md')
    parser.add_argument('--json', action='store_true', help='print scan JSON to stdout')
    args = parser.parse_args(argv)
    rows = scan()
    if args.json:
        print(json.dumps({'counts': counts(rows), 'rows': rows}, ensure_ascii=False, indent=2))
        return 0
    if args.write:
        text, stats = render(rows)
        LEDGER.write_text(text, encoding='utf-8')
        print(json.dumps({'wrote': str(LEDGER), **stats}, ensure_ascii=False))
        return 0
    if args.check:
        return check(rows)
    # default: summary
    print(json.dumps(counts(rows), ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
