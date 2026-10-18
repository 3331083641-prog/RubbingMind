"""Actual Chromium UI regression for adaptive processing, ROI, retrieval, experiments."""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'screenshots/technical-v2'
BATCH='controlled-rubbings-v2-text-2026-10-17'


def run(url,ci=False):
    OUT.mkdir(parents=True,exist_ok=True)
    result={'pageErrors':[],'checks':[],'screenshots':[]}
    def capture(page,name):
        page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/name),full_page=True);result['screenshots'].append(name)
    def nav(page,label):page.locator('header').first.get_by_role('button',name=label).click()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel=os.environ.get('RUBBINGMIND_BROWSER_CHANNEL'),headless=True,args=['--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':1920 if not ci else 1440,'height':1080 if not ci else 900},accept_downloads=True)
        page.on('pageerror',lambda e:result['pageErrors'].append(str(e)))
        page.goto(url,wait_until='domcontentloaded')
        expect(page.get_by_role('button',name='首页门户')).to_be_visible()
        if not ci:
            expect(page.get_by_role('button',name='正面',exact=True)).to_be_visible(timeout=60000)
            for label in ['正面','左侧','右侧','俯视','仰视','背面']:
                button=page.get_by_role('button',name=label,exact=True);button.click();expect(button).to_have_class(re.compile('bg-gold'))
            result['checks'].append('Three.js six direction controls')
        capture(page,'01-home.png')
        nav(page,'贞石典藏馆')
        expect(page.get_by_test_id('museum-card')).to_have_count(28)
        for dynasty in ['东汉','北魏','唐代','宋代','元代','明代','清代']:
            page.get_by_role('button',name=re.compile('^'+dynasty+r'\s*4$')).click()
            expect(page.get_by_test_id('museum-card')).to_have_count(4)
            for card in page.get_by_test_id('museum-card').all():
                card.scroll_into_view_if_needed();img=card.get_by_test_id('museum-cover')
                expect(img).to_be_visible();expect(img).to_have_js_property('complete',True)
                assert img.evaluate('(i)=>i.naturalWidth')==1100
        result['checks'].append('28 covers native width and seven dynasty filters')
        card=page.get_by_test_id('museum-card').first
        assessed=card.get_attribute('data-stele-id')
        card.get_by_role('button',name='查看本件评估').click()
        assessment=page.get_by_role('dialog',name='馆藏评估')
        expect(assessment.get_by_text('自动初筛，待人工复核')).to_be_visible()
        for label in ['处理前局部','处理后局部']:
            image=assessment.get_by_role('img',name=label)
            image.scroll_into_view_if_needed();image.evaluate('(i)=>i.decode()')
            assert image.evaluate('(i)=>i.naturalWidth')==512
        asset=page.request.get(url.rstrip('/')+f'/api/catalog/{assessed}/assessment/assets/output')
        assert asset.status==200
        assessment.get_by_role('button',name='关闭').click()
        result['checks'].append('archived assessment comparison is served without a local results directory')
        capture(page,'02-museum.png')
        nav(page,'智考工作台');page.locator('header select').first.select_option('tang_01_duobao')
        expect(page.get_by_label('频域处理方式')).to_have_value('adaptive')
        with page.expect_response(lambda r:r.url.endswith('/api/process') and r.request.method=='POST',timeout=60000) as response:
            page.get_by_role('button',name='执行频空域联合去噪').click()
        assert response.value.ok,response.value.text();run=response.value.json();result['runId']=run['runId']
        assert run['psnr'] is None and run['adaptiveDiagnostics']['features']
        expect(page.get_by_label('选择运行记录')).to_have_value(run['runId'])
        page.get_by_text('本次自适应决策与保真诊断',exact=True).click()
        capture(page,'03-adaptive-workbench.png')
        page.get_by_role('button',name='框选残字区域').click()
        dialog=page.get_by_role('dialog',name='框选残字');image=dialog.locator('img');expect(image).to_be_visible()
        image.evaluate('(i)=>i.decode()');box=image.bounding_box()
        page.mouse.move(box['x']+box['width']*.25,box['y']+box['height']*.25);page.mouse.down()
        page.mouse.move(box['x']+box['width']*.4,box['y']+box['height']*.45);page.mouse.up()
        with page.expect_response(lambda r:r.url.endswith('/inferences') and r.request.method=='POST') as response:
            page.get_by_role('button',name='提交实际选区').click()
        assert response.value.ok,response.value.text();inference=response.value.json();result['inferenceId']=inference['inferenceId']
        assert inference['steleId']=='tang_01_duobao' and inference['runId']==run['runId']
        assert inference['visualAnalysis']['version']=='glyph-shape-v2.1'
        assert inference['imageProvenance']['imageSource']=='restored'
        assert inference['imageProvenance']['runOwnership']=='verified'
        expect(page.get_by_role('img',name='残字分析 skeleton',exact=True)).to_be_visible()
        page.get_by_role('button',name='驳回本次候选').click()
        expect(page.get_by_text('本次候选已人工驳回；操作已保存。',exact=True)).to_be_visible()
        capture(page,'04-actual-glyph-analysis.png')
        result['checks'].append('official input adaptive processing, real crop, visual analysis and durable rejection')
        nav(page,'时空图谱中心');page.locator('header select').first.select_option('tang-duobao')
        panel=page.get_by_role('region',name='史料智能检索');expect(panel).to_be_visible()
        panel.get_by_label('史料问题').fill('《多宝塔碑》的撰文者与书丹者是谁？')
        with page.expect_response(lambda r:r.url.endswith('/api/research/query')) as response:panel.get_by_role('button',name='检索史料').click()
        assert response.value.ok;research=response.value.json();assert research['evidence'] and research['relations']
        expect(page.get_by_test_id('research-answer')).to_contain_text('岑勋')
        expect(page.get_by_test_id('research-answer')).to_contain_text('颜真卿')
        (OUT/'actual-research-query.json').write_text(json.dumps(research,ensure_ascii=False,indent=2),'utf8')
        if not ci:
            map_el=page.get_by_test_id('historical-map');expect(map_el).to_have_attribute('data-ready','true',timeout=30000)
            locate=panel.get_by_role('button',name='在现有GIS中定位').first
            expect(locate).to_be_visible();locate.click()
            expect(page.get_by_role('tab',name='地理关联',exact=True)).to_have_attribute('aria-selected','true')
        capture(page,'05-evidence-graphrag.png')
        page.locator('header select').first.select_option('wei-jianyi')
        panel=page.get_by_role('region',name='史料智能检索')
        panel.get_by_label('史料问题').fill('北魏建义元年演示样本是否已经确认真实文物身份？');panel.get_by_role('button',name='检索史料').click()
        expect(page.get_by_test_id('research-answer')).to_contain_text('未确认')
        capture(page,'06-unverified-identity.png')
        page.locator('header select').first.select_option('qing_02_wushi_reerection')
        expect(page.get_by_test_id('graph-museum-image')).to_be_visible()
        panel=page.get_by_role('region',name='史料智能检索')
        panel.get_by_label('史料问题').fill('重立武氏祠石记原刻年代是什么？');panel.get_by_role('button',name='检索史料').click()
        expect(page.get_by_test_id('research-answer')).to_contain_text('1787')
        capture(page,'07-museum-unified-research.png')
        result['checks'].append('real evidence retrieval, sourced expansion, unverified identity refusal and museum research')
        page.locator('header select').first.select_option('tang_01_duobao');nav(page,'算法评测报告')
        page.get_by_label('选择报告运行记录').select_option(run['runId'])
        expect(page.get_by_text('运行 ID：'+run['runId'],exact=False)).to_be_visible()
        with page.expect_download() as download:page.get_by_role('button',name='导出 JSON',exact=True).click()
        download.value.save_as(OUT/'actual-run-report.json')
        report=json.loads((OUT/'actual-run-report.json').read_text('utf8'))
        assert report['runId']==run['runId'] and report['stele']['id']=='tang_01_duobao' and report['adaptiveDiagnostics']
        assert any(i['inferenceId']==inference['inferenceId'] and i['status']=='human_rejected' for i in report['inferenceRecords'])
        page.pdf(path=str(OUT/'actual-run-report.pdf'),format='A4',print_background=True)
        heldout=page.get_by_role('region',name='v2.0与v2.1留出对比')
        expect(heldout).to_contain_text('受控退化实验')
        expect(heldout).to_contain_text('负提升')
        heldout.get_by_role('button',name='遮挡').click()
        expect(heldout).to_contain_text('adaptive_v21')
        experiment=page.get_by_role('region',name='算法实验与消融分析')
        experiment.get_by_label('实验批次').select_option(BATCH)
        expect(experiment.get_by_label('实验批次')).to_have_value(BATCH)
        experiment.get_by_label('实验样本',exact=True).select_option('han_04_shichen')
        experiment.get_by_label('退化类型').select_option('gaussian')
        experiment.get_by_label('处理方法').select_option('adaptive_joint')
        expect(experiment.get_by_test_id('experiment-table').locator('tbody tr')).to_have_count(1)
        api=page.request.get(url.rstrip('/')+'/api/experiments/'+BATCH).json()
        values=[r for r in api['rows'] if r['sampleId']=='han_04_shichen' and r['degradation']=='gaussian' and r['method']=='adaptive_joint' and r['split']=='test']
        expected=f"{sum(r['psnr'] for r in values)/len(values):.3f}"
        expect(experiment.get_by_test_id('experiment-table').locator('tbody tr td').nth(3)).to_have_text(expected)
        for img in experiment.locator('img').all():
            img.scroll_into_view_if_needed();img.evaluate('(i)=>i.decode()');assert img.evaluate('(i)=>i.naturalWidth')==256
        capture(page,'08-experiment-explorer.png')
        result['checks'].append('selected real run report JSON/PDF, source-linked experiment images and API/UI numeric equality')
        for width,height in ([(1920,1080),(1440,900),(1366,768)] if not ci else [(1440,900)]):
            page.set_viewport_size({'width':width,'height':height})
            capture(page,f'09-reports-{width}.png')
            nav(page,'时空图谱中心');page.locator('header select').first.select_option('tang-duobao')
            expect(page.get_by_test_id('stele-tang-duobao')).to_be_visible()
            capture(page,f'10-graph-{width}.png')
            nav(page,'智考工作台');expect(page.get_by_role('heading',name='真实处理历史')).to_be_visible()
            capture(page,f'11-workbench-{width}.png')
            nav(page,'算法评测报告')
        if not ci:
            mobile=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
            phone=mobile.new_page();phone.on('pageerror',lambda e:result['pageErrors'].append(str(e)))
            phone.goto(url);nav(phone,'时空图谱中心')
            expect(phone.get_by_role('region',name='史料智能检索')).to_be_visible()
            phone.get_by_label('史料问题').fill('多宝塔碑的作者是谁？');phone.get_by_role('button',name='检索史料').tap()
            expect(phone.get_by_test_id('research-answer')).to_contain_text('岑勋')
            capture(phone,'12-mobile-touch-retrieval.png')
            result['mobileOverflow']=phone.evaluate('document.documentElement.scrollWidth > innerWidth+2')
            mobile.close()
        offline=browser.new_context(viewport={'width':1440,'height':900});offline.route('**/api/**',lambda route:route.abort())
        fail=offline.new_page();fail.goto(url);nav(fail,'贞石典藏馆');expect(fail.get_by_test_id('museum-card')).to_have_count(28)
        nav(fail,'时空图谱中心');panel=fail.get_by_role('region',name='史料智能检索');expect(panel.get_by_role('alert')).to_be_visible()
        result['checks'].append('API unavailable: 28-item fallback retained and research reports failure')
        offline.close();browser.close()
    assert not result['pageErrors'],result['pageErrors']
    (OUT/'browser-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default=os.getenv('RUBBINGMIND_FRONTEND_URL','http://127.0.0.1:5180'));parser.add_argument('--ci',action='store_true');args=parser.parse_args()
    print(json.dumps(run(args.url,args.ci),ensure_ascii=False,indent=2))
