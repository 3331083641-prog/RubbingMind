"""Capture and exercise the current five-page delivery against explicit test ports.

Run against an isolated audit server. --exercise-upload writes a known public
experiment fixture and processing run to that server, never to the catalogue.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlencode

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import requests
from playwright.sync_api import expect,sync_playwright
from scripts.browser_target import assert_safe_target

EXP='controlled-rubbings-v2-text-2026-10-17'
NAMES=('home','museum','workbench','graph','reports')
SIZES=((1920,1080),(1440,900),(1366,768))


def run(url,backend,out,exercise_upload=False):
    assert requests.get(backend+'/health',timeout=10).json()['status']=='healthy'
    assert requests.get(backend+'/generate',timeout=10).json()['steleId']=='tang-duobao'
    out.mkdir(parents=True,exist_ok=True)
    result={'checks':[],'viewports':[],'pageErrors':[],'screenshots':[],'privateDataUsed':False}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel=os.getenv('RUBBINGMIND_BROWSER_CHANNEL'),headless=True)
        context=browser.new_context(viewport={'width':1920,'height':1080},accept_downloads=True)
        page=context.new_page();page.on('pageerror',lambda e:result['pageErrors'].append(str(e)))
        expect.set_options(timeout=30000)

        def open_tab(tab,**extra):
            params={'tab':tab,'steleId':'tang-duobao' if tab in ('home','graph') else 'tang_01_duobao'}
            if tab=='home':params['steleQA']='1'
            if tab=='workbench':
                runs=page.request.get(url+'/api/steles/tang_01_duobao/runs').json()
                actual=next((r for r in runs if not r.get('legacy') and r.get('runId')),None)
                if actual:params['runId']=actual['runId']
            if tab=='reports':params.update(view='global',panel='overview',experimentId=EXP)
            params.update(extra)
            page.goto(url+'/?'+urlencode(params),wait_until='domcontentloaded')
            page.wait_for_function("tab=>{const e=document.querySelector('[data-catalogue-status]');return e?.dataset.catalogueStatus==='ready'&&e.dataset.tab===tab}",arg=tab)
            if tab=='home':
                page.wait_for_function("()=>{const c=document.querySelector('section canvas');return c&&window.__steleQA?.get(c)?.inspect().ready}")
            elif tab=='museum':expect(page.get_by_test_id('museum-card')).to_have_count(28)
            elif tab=='workbench':
                expect(page.get_by_role('heading',name='真实处理历史')).to_be_visible()
                if params.get('runId'):
                    expect(page.get_by_label('选择运行记录',exact=True)).to_have_value(params['runId'])
                    result['workbenchRunId']=params['runId']
            elif tab=='graph':expect(page.get_by_test_id('historical-map')).to_have_attribute('data-terrain-ready','true',timeout=60000)
            elif tab=='reports':
                expect(page.get_by_test_id('global-evaluation')).to_be_visible()
                expect(page.get_by_test_id('method-comparison-chart').locator('canvas').first).to_be_visible()
            page.wait_for_timeout(600)

        def capture(name,full=False,locator=None):
            target=out/name;target.parent.mkdir(parents=True,exist_ok=True)
            if locator is None:page.screenshot(path=str(target),full_page=full)
            else:locator.screenshot(path=str(target))
            result['screenshots'].append(name)

        for w,h in SIZES:
            page.set_viewport_size({'width':w,'height':h})
            for index,tab in enumerate(NAMES,1):
                open_tab(tab)
                if tab=='home' and w==1920:
                    page.wait_for_function("()=>{const v=document.querySelector('video');return v&&!v.paused&&v.currentTime>.3}",timeout=20000)
                    state=page.evaluate("()=>{const c=document.querySelector('section canvas');const q=window.__steleQA.get(c).inspect();const v=document.querySelector('video');return {modelReady:q.ready,meshes:q.meshes,triangles:q.triangles,videoTime:v.currentTime,videoReady:v.readyState}}")
                    page.wait_for_timeout(500)
                    assert page.locator('video').evaluate('(v)=>v.currentTime')!=state['videoTime']
                    result['homeMedia']=state
                overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth+2')
                result['viewports'].append({'width':w,'height':h,'page':tab,'horizontalOverflow':overflow})
                assert not overflow,(w,h,tab)
                capture(f'{w}x{h}/{index:02d}-{tab}.png')
        result['checks'].append('five pages at all three requested desktop viewports; real video and GLB')

        page.set_viewport_size({'width':1920,'height':1080});open_tab('reports')
        capture('reports/01-global-full.png',full=True)
        capture('reports/03-method-chart.png',locator=page.get_by_test_id('method-comparison-chart'))
        page.get_by_test_id('studio-module-images').click()
        triptych=page.get_by_test_id('experiment-triptych')
        expect(triptych).to_be_visible()
        for img in triptych.locator('img').all():
            img.evaluate('(i)=>i.decode()');assert img.evaluate('(i)=>i.naturalWidth')==256
        capture('reports/02-real-image-comparison.png',locator=triptych)
        with page.expect_download() as download:page.get_by_role('button',name='导出 JSON',exact=True).click()
        download.value.save_as(out/'reports/global-export.json')
        exported=json.loads((out/'reports/global-export.json').read_text(encoding='utf-8'))
        assert exported['experiment']['experimentId']==EXP
        assert exported['glyphEvaluation']['status']=='not_evaluated'
        ci_source=page.get_by_test_id('comparison-ci-source').get_attribute('data-ci-source')
        assert ci_source==('backend' if exported['experiment']['ciSource'].startswith('API ') else 'frontend')
        result['globalReport']={'experimentId':EXP,'appliedStatusSource':exported['experiment']['appliedStatusSource'],
                                'ciSource':exported['experiment']['ciSource'],'glyphAccuracyEvaluated':False}
        page.pdf(path=str(out/'reports/global-report.pdf'),format='A4',print_background=True)
        page.get_by_role('tab',name='失败案例与不确定性',exact=True).click()
        expect(page.get_by_test_id('failure-cases')).to_contain_text('负提升')
        capture('reports/04-failure-cases.png',full=True)
        page.get_by_role('tab',name='消融与机制',exact=True).click()
        mechanism=page.get_by_test_id('mechanism-panel')
        expect(mechanism.locator('img').first).to_be_visible()
        for img in mechanism.locator('img:visible').all():
            img.evaluate('(i)=>i.decode()');assert img.evaluate('(i)=>i.naturalWidth')>0
        expect(mechanism.get_by_test_id('mechanism-head-lag-note')).to_be_visible()
        capture('reports/05-mechanism.png',full=True)
        result['checks'].append('real triptych, chart, failure records, mechanism PNGs, JSON and print PDF')

        if exercise_upload:
            open_tab('museum')
            page.get_by_role('button',name='上传新碑拓样本入馆',exact=True).click()
            fixture=ROOT/'experiments/results/2026-10-17-v2-text/han_04_shichen_gaussian_0_input.png'
            raw=fixture.read_bytes()
            page.locator('input[type=file]').set_input_files({'name':'sync-audit-public-fixture.png','mimeType':'image/png','buffer':raw})
            with page.expect_response(lambda r:r.url.endswith('/api/upload') and r.request.method=='POST') as response:
                page.get_by_role('button',name='立即录入并开启智能考据',exact=True).click()
            assert response.value.ok,response.value.status
            record=response.value.json()['stele']
            assert record['source_kind']=='user_upload'
            assert record['originalFileSha256']==hashlib.sha256(raw).hexdigest()
            expect(page.get_by_label('当前碑刻')).to_have_value(record['id'])
            page.locator('header').first.get_by_role('button',name='智考工作台').click()
            with page.expect_response(lambda r:r.url.endswith('/api/process') and r.request.method=='POST',timeout=60000) as response:
                page.get_by_role('button',name='执行频空域联合去噪',exact=True).click()
            processed=response.value.json();assert response.value.ok
            assert processed['stele_id']==record['id'] and processed['psnr'] is None
            rows=page.request.get(url+'/api/steles').json()
            assert len([r for r in rows if r.get('source_kind')=='verified_review_v3'])==28
            result['upload']={'id':record['id'],'runId':processed['runId'],'source':'public controlled-degradation fixture',
                              'catalogueCountUnchanged':28,'originalShaMatches':True}
            capture('upload/01-real-upload-processing.png')
            result['checks'].append('UI upload persisted original bytes and executed real processing without adding authoritative catalogue records')

        page.set_viewport_size({'width':390,'height':844});open_tab('home')
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2')
        capture('mobile/01-home-390.png')
        context.close();browser.close()
    assert not result['pageErrors'],result['pageErrors']
    result['status']='passed'
    (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True);parser.add_argument('--backend',required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'screenshots/sync-verification')
    parser.add_argument('--exercise-upload',action='store_true');args=parser.parse_args()
    print(json.dumps(run(assert_safe_target(args.url).rstrip('/'),assert_safe_target(args.backend).rstrip('/'),
                         args.output,args.exercise_upload),ensure_ascii=False,indent=2))
