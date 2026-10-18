from catalog import load, report
from catalog_assessment import public_record


def test_assessment_and_report_stay_on_the_requested_stele():
    records = {row['id']: row for row in load('steles28.json')}
    caoquan = public_record('han_01_caoquan')
    duobao = public_record('tang_01_duobao')
    assert caoquan['steleId'] == 'han_01_caoquan'
    assert duobao['steleId'] == 'tang_01_duobao'
    assert caoquan['sourceImageSha256'] != duobao['sourceImageSha256']
    assert caoquan['runId'] != duobao['runId']
    caoquan_report = report(records['han_01_caoquan'])
    duobao_report = report(records['tang_01_duobao'])
    assert caoquan_report['stele_id'] == 'han_01_caoquan'
    assert duobao_report['stele_id'] == 'tang_01_duobao'
    assert caoquan_report['metrics']['psnr'] is None
    assert duobao_report['metrics']['ssim'] is None
    assert records['han_01_caoquan'].get('calligrapher') != '颜真卿'
