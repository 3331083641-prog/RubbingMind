"""Item C: ming_02 carrier nature is flagged “载体性质待人工鉴定” in the claim, the ledger and the reused badges."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAG = '载体性质待人工鉴定'


def _claims(obj):
    if isinstance(obj, dict):
        if 'claimId' in obj:
            yield obj
        for v in obj.values():
            yield from _claims(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _claims(v)


def test_claim_carries_flag_without_upgrading():
    data = json.loads((ROOT / 'data/catalog/claims/ming_02_luxianzhi.json').read_text(encoding='utf-8'))
    claim = next(c for c in _claims(data) if c['claimId'] == 'ming_02_luxianzhi:work:objectNature')
    assert claim['reviewFlags'] == [FLAG]
    assert claim['status'] == 'conflict' and claim['evidenceLevel'] == '待人工复核' and claim['value'] is None
    assert {a['value'] for a in claim['alternatives']} == {'拓片（馆方分类）', '墓志草稿（题跋：“此潯州知府陸君墓志草稿”）'}


def test_ledger_passes_flag_to_ui_data_only_for_ming_02():
    for path in ('data/catalog/review_ledger.json', 'apps/web/src/data/reviewLedger.json'):
        ledger = json.loads((ROOT / path).read_text(encoding='utf-8'))
        flagged = {r['id']: [f['flag'] for f in r['contentFlags']] for r in ledger['records'] if r['contentFlags']}
        assert flagged == {'ming_02_luxianzhi': [FLAG]}, path


def test_badges_render_flags_on_museum_card_and_viewer():
    badges = (ROOT / 'apps/web/src/components/ReviewStatusBadges.tsx').read_text(encoding='utf-8')
    assert 'contentFlags' in badges and 'data-testid="content-flag"' in badges and FLAG not in badges  # text comes from data
    # Two mount points: MuseumPage card + RubbingArchiveViewer (arch/report merges must not drop either).
    mounts = {
        'apps/web/src/pages/MuseumPage.tsx': 0,
        'apps/web/src/components/RubbingArchiveViewer.tsx': 0,
    }
    for page in mounts:
        text = (ROOT / page).read_text(encoding='utf-8')
        mounts[page] = text.count('<ReviewStatusBadges')
        assert mounts[page] >= 1, f'{page}: ReviewStatusBadges JSX mount missing (got {mounts[page]})'
    assert sum(mounts.values()) >= 2
