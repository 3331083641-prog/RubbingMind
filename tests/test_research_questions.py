"""Catalogue-backed questions. Expected judgments come from the stored fields, not a new score."""
import evidence_retrieval as er

CASES = [
    {'question': '《多宝塔碑》的书丹者是谁？', 'steleId': None, 'judgment': 'supported', 'text': '颜真卿'},
    {'question': '《多宝塔碑》的书丹者是不是欧阳询？', 'steleId': None, 'judgment': 'contradicted', 'text': '颜真卿'},
    {'question': '《多宝塔碑》的撰文者是不是岑勋？', 'steleId': None, 'judgment': 'supported', 'text': '岑勋'},
    {'question': '《曹全碑》的撰文者是谁？', 'steleId': None, 'judgment': 'insufficient_evidence', 'text': '未核定'},
    {'question': '书丹者是不是王羲之？', 'steleId': 'ming_04_tongdian', 'judgment': 'disputed', 'text': '争议'},
    {'question': '撰文者是不是邓文原？', 'steleId': 'yuan_02_sundeyu', 'judgment': 'disputed', 'text': '争议'},
    {'question': '撰文者是不是赵孟頫？', 'steleId': 'yuan_04_jingyuanchang', 'judgment': 'insufficient_evidence', 'text': '未核定'},
    {'question': '《多宝塔碑》的书丹者是谁？', 'steleId': 'han_01_caoquan', 'judgment': 'insufficient_evidence', 'text': '不足以'},
    {'question': '刻工是谁？', 'steleId': 'han_01_caoquan', 'judgment': 'insufficient_evidence', 'text': '未核定'},
]


def test_research_question_set_keeps_support_conflict_and_refusal():
    for case in CASES:
        result = er.query(case['question'], case['steleId'])
        assert result['judgment'] == case['judgment'], (case, result['answer'])
        assert case['text'] in result['answer'], (case, result['answer'])
        if case['judgment'] == 'disputed':
            assert result['claim']['recorded'] is None
        if result.get('claim') and result['claim'].get('steleId'):
            assert result['claim']['steleId'] == (case['steleId'] or result['claim']['steleId'])
