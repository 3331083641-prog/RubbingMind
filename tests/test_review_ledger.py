"""C-06 option A: review ledger beside the catalogue; approval and pending evidence review are both kept."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'data/catalog/review_ledger.json'


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def test_ledger_is_up_to_date_and_web_copy_identical():
    result = subprocess.run([sys.executable, 'scripts/build_review_ledger.py', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert LEDGER.read_bytes() == (ROOT / 'apps/web/src/data/reviewLedger.json').read_bytes()


def test_ledger_covers_28_records_with_both_states():
    ledger = load(LEDGER)
    catalogue = {r['id']: r for r in load(ROOT / 'data/catalog/steles28.json')}
    assert [r['id'] for r in ledger['records']] == list(catalogue)
    for record in ledger['records']:
        evidence = load(ROOT / record['evidenceReview']['evidenceFile'])
        assert record['catalogueApproval']['status'] == catalogue[record['id']]['sourceVerification']['status']
        assert record['evidenceReview']['humanReviewStatus'] == evidence['processing']['human_review_status']
        assert record['catalogueApproval']['label'] and record['evidenceReview']['label']
        if record['evidenceReview']['humanReviewStatus'].startswith('pending_third_round'):
            assert record['evidenceReview']['label'] == '证据待第三轮复核'


def test_reviewer_date_scope_are_not_invented():
    ledger = load(LEDGER)
    assert ledger['manifestBasis']['reviewerOrDateRecorded'] is False
    for record in ledger['records']:
        user = record['userApproval']
        assert user == {'approvedBy': None, 'approvedAt': None, 'approvalScope': None, 'status': '待用户填写'}


def test_ui_component_renders_both_labels():
    component = (ROOT / 'apps/web/src/components/ReviewStatusBadges.tsx').read_text(encoding='utf-8')
    assert 'catalogueApproval.label' in component and 'evidenceReview.label' in component
    # Museum card + archive viewer — both required (merge regressions have dropped MuseumPage).
    for page in ('apps/web/src/pages/MuseumPage.tsx', 'apps/web/src/components/RubbingArchiveViewer.tsx'):
        text = (ROOT / page).read_text(encoding='utf-8')
        assert text.count('<ReviewStatusBadges') >= 1, f'{page}: missing ReviewStatusBadges mount'
