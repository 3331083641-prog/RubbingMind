"""Real report-stage regression. Use an isolated server; --exercise-run can process a public catalogue image."""
from __future__ import annotations
import argparse,json,math,os,sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from playwright.sync_api import sync_playwright,expect
from scripts.browser_target import assert_safe_target
EXP='controlled-rubbings-v2-text-2026-10-17'

def run(url,out,video=False,exercise_run=False):
    out.mkdir(parents=True,exist_ok=True);checks=[];errors=[];requests=[]
    result={'checks':checks,'pageErrors':errors,'privateDataUsed':False}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel=os.getenv('RUBBINGMIND_BROWSER_CHANNEL'),headless=True,args=['--enable-unsafe-swiftshader'])
        context=browser.new_context(viewport={'width':1440,'height':900},accept_downloads=True,**({'record_video_dir':str(out/'video'),'record_video_size':{'width':1440,'height':900}} if video else {}))
        # Exercise full motion independently of the runner's CPU count. The
        # low-concurrency policy is checked in its own context below.
        context.add_init_script("Object.defineProperty(navigator,'hardwareConcurrency',{get:()=>8})")
        page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:requests.append(r.url));expect.set_options(timeout=30000)
        def goto(**patch):
            params={'tab':'reports','view':'global','steleId':'tang_01_duobao','experimentId':EXP};params.update(patch)
            page.goto(url+'/?'+urlencode(params),wait_until='domcontentloaded')
        def stage(name):
            button=page.get_by_test_id('studio-module-'+name)
            (button if button.is_visible() else page.get_by_test_id('studio-secondary-'+name)).click()
            expect(page.get_by_test_id('report-main-stage')).to_have_attribute('data-panel',name)
            page.wait_for_function("()=>!document.getAnimations().some(a=>a.playState==='running')")
        def shot(name,full=False):page.screenshot(path=str(out/name),full_page=full)
        def download(name):
            with page.expect_download() as event:page.get_by_role('button',name='导出 JSON',exact=True).click()
            event.value.save_as(out/name);return json.loads((out/name).read_text(encoding='utf-8'))
        goto();expect(page.get_by_test_id('method-comparison-chart').locator('canvas').first).to_be_visible()
        page.wait_for_timeout(750)
        assert page.get_by_test_id('report-main-stage').bounding_box()['width']/page.locator('.studio-layout').bounding_box()['width'] > .65
        assert not page.locator('.studio-details[open]').count()
        for width,height in [(1920,1080),(1440,900),(1366,768),(390,844)]:
            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(650)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2'),width
            box=page.get_by_test_id('method-comparison-chart').bounding_box()
            assert box['y'] < height and box['height'] >= 260
            shot(f'overview-{width}.png')
        page.set_viewport_size({'width':1440,'height':900});page.wait_for_timeout(500)
        data=download('global-report.json');rows=page.request.get(url+'/api/experiments/'+EXP).json()['rows']
        derived=page.request.get(url+'/api/experiments/'+EXP+'/derived/applied_status.json')
        assert derived.ok,'Need validated DER to independently verify classifications'
        states={d['rowIndex']:d['appliedStatus'] for d in derived.json()['rows']}
        bases={(r.get('split'),r['caseId']):r for r in rows if r['method']=='degraded'}
        selected=[(i,r) for i,r in enumerate(rows) if r.get('split')=='test' and r['method']!='degraded']
        values=defaultdict(list)
        for i,r in selected:
            if r['method']==data['experiment']['filters']['method'] and states.get(i)=='processed':
                values[r['sampleId']].append(r['psnr']-bases[(r.get('split'),r['caseId'])]['psnr'])
        expected=sum(sum(v)/len(v) for v in values.values())/len(values)
        actual=float(page.get_by_test_id('studio-primary').locator('[data-final-value]').get_attribute('data-final-value'))
        assert math.isclose(expected,actual,abs_tol=1e-10),(expected,actual)
        negatives=sum(1 for i,r in selected if r['method']==data['experiment']['filters']['method'] and states[i]!='failed' and r.get('psnr') is not None and bases[(r.get('split'),r['caseId'])].get('psnr') is not None and r['psnr']<bases[(r.get('split'),r['caseId'])]['psnr'])
        assert int(page.get_by_test_id('studio-negative-count').locator('[data-final-value]').get_attribute('data-final-value'))==negatives
        for distribution in data['experiment']['visualizations']['distribution']:
            counts=[0]*6
            for i,r in selected:
                if r['method']!=distribution['method']:continue
                status=states[i];delta=r.get('psnr');base=bases[(r.get('split'),r['caseId'])].get('psnr')
                if r.get('error') or status=='failed':counts[5]+=1
                elif status in ('passthrough','passthrough_not_applicable'):counts[3]+=1
                elif status!='processed' or delta is None or base is None:counts[4]+=1
                else:counts[0 if delta>base else 1 if delta<base else 2]+=1
            assert counts==distribution['counts'],(distribution['method'],counts,distribution['counts'])
        for point in data['experiment']['visualizations']['timing']:
            grouped=defaultdict(list)
            for i,r in selected:
                base=bases[(r.get('split'),r['caseId'])].get('psnr')
                if r['method']==point['method'] and not r.get('error') and (point['scope']=='all' or states[i]=='processed') and r.get('processingMs') is not None and r.get('psnr') is not None and base is not None:
                    grouped[r['sampleId']].append((r['processingMs'],r['psnr']-base))
            means=lambda n:sum(sum(x[n] for x in v)/len(v) for v in grouped.values())/len(grouped)
            assert math.isclose(point['milliseconds'],means(0),abs_tol=1e-9)
            assert math.isclose(point['quality'],means(1),abs_tol=1e-9)
            assert point['rows']==sum(map(len,grouped.values()))
        checks.append('API/DER independently recomputed artifact-weighted primary mean and all outcome counts match UI/JSON')
        initial=page.get_by_test_id('method-comparison-chart').bounding_box()['width'];before=page.url
        page.get_by_role('button',name='专注查看',exact=True).click();page.wait_for_timeout(600)
        assert page.get_by_test_id('method-comparison-chart').bounding_box()['width']>initial*1.2
        canvas=page.get_by_test_id('method-comparison-chart').locator('canvas').first
        assert canvas.evaluate('(c)=>Math.abs(parseFloat(c.style.width)-c.parentElement.clientWidth)<3')
        shot('focus-comparison.png');page.keyboard.press('Escape');page.wait_for_timeout(500)
        assert abs(page.get_by_test_id('method-comparison-chart').bounding_box()['width']-initial)<3 and page.url==before
        checks.append('focus resize and ESC preserve filters and restore chart geometry')
        batch_requests=sum('/api/experiments/'+EXP in r and '/derived/' not in r and '/assets/' not in r and '/diagnosis' not in r for r in requests)
        for name in ['images','heatmap','distribution','timing','failures','mechanism','overview']:
            stage(name)
            if name=='images':
                expect(page.get_by_test_id('experiment-triptych')).to_be_visible()
                for image in page.get_by_test_id('experiment-triptych').locator('img').all():image.evaluate('(i)=>i.decode()')
                page.get_by_role('button',name='滑杆对比',exact=True).click();expect(page.get_by_label('滑杆对比位置')).to_be_visible();page.get_by_label('滑杆对比位置').fill('35')
                page.get_by_role('button',name='并排',exact=True).click()
            elif name in ('heatmap','distribution','timing'):expect(page.get_by_test_id('studio-'+name+'-chart').locator('canvas').first).to_be_visible()
            elif name=='failures':
                expect(page.get_by_test_id('failure-cases')).to_contain_text('负提升')
                page.get_by_test_id('failure-image-gallery').locator('button').first.click()
                expect(page.get_by_test_id('failure-detail-triptych')).to_be_visible();shot('failure-case-expanded.png')
                page.get_by_role('button',name='返回案例墙',exact=False).click()
            elif name=='mechanism':
                expect(page.get_by_test_id('mechanism-head-lag-note')).to_contain_text('最新交付代码')
                for step in ['频域分析','方法选择','保真判断','输出差分']:
                    page.get_by_role('tab',name=step,exact=True).click()
                    if step!='方法选择':page.get_by_test_id('mechanism-detail').locator('img:visible').first.evaluate('(i)=>i.decode()')
                shot('mechanism-flow-expanded.png')
            shot(name+'-expanded.png',full=True)
        assert sum('/api/experiments/'+EXP in r and '/derived/' not in r and '/assets/' not in r and '/diagnosis' not in r for r in requests)==batch_requests
        checks.append('all evidence windows expand into main stage without reloading batch data; real slider and mechanism steps')
        page.evaluate("()=>{document.startViewTransition=undefined;window.__studioFallback=0;const original=Element.prototype.animate;Element.prototype.animate=function(...args){if(this.hasAttribute('inert'))window.__studioFallback++;return original.apply(this,args)}}")
        stage('images');assert page.evaluate('window.__studioFallback')==1;stage('overview');checks.append('FLIP fallback animates the selected window without the View Transition API')
        page.get_by_label('评价指标',exact=True).select_option('ssim');page.wait_for_timeout(700)
        assert 'metric=ssim' in page.url
        page.reload(wait_until='domcontentloaded');expect(page.get_by_label('评价指标',exact=True)).to_have_value('ssim')
        page.get_by_text('筛选与实验上下文',exact=True).click();page.get_by_label('退化类型筛选',exact=True).select_option('blur');page.get_by_label('处理方法',exact=True).select_option('adaptive_joint')
        stage('images');expect(page.get_by_test_id('case-worst')).to_be_disabled()
        page.get_by_test_id('case-passthrough').click();expect(page.get_by_test_id('experiment-triptych')).to_be_visible()
        shot('passthrough-evidence.png')
        checks.append('metric URL reload, degradation filtering and genuine unprocessed example retained')
        goto(panel='images',experimentId='heldout-v20-v21-2026-10-18');expect(page.get_by_test_id('no-images')).to_be_visible();shot('metrics-only-empty.png')
        goto(experimentId='not-a-registered-experiment');expect(page.get_by_test_id('app-unknown-experiment')).to_be_visible();shot('unknown-experiment.png')
        goto();expect(page.get_by_test_id('report-main-stage')).to_be_visible();stage('overview')
        page.evaluate("()=>{window.print=()=>{throw new Error('test print blocked')}}");page.get_by_role('button',name='打印 / 保存 PDF',exact=True).click();expect(page.get_by_role('alert').filter(has_text='打印窗口未能打开')).to_be_visible()
        page.evaluate('()=>{window.print=()=>{window.__reportPrint=true}}');page.get_by_role('button',name='打印 / 保存 PDF',exact=True).click();page.wait_for_function('window.__reportPrint===true')
        page.pdf(path=str(out/'report.pdf'),format='A4',print_background=True)
        page.emulate_media(media='print');assert page.get_by_test_id('print-studio-evidence').is_visible();assert not page.get_by_test_id('report-main-stage').is_visible();page.emulate_media(media='screen')
        checks.append('full stable PDF with additional evidence tables and JSON export')
        runs=page.request.get(url+'/api/steles/tang_01_duobao/runs').json();real=next((r for r in runs if not r.get('legacy')),None)
        if not real and exercise_run:
            goto(tab='workbench');page.get_by_role('button',name='执行频空域联合去噪',exact=True).click();expect(page.get_by_label('选择运行记录',exact=True)).not_to_have_value('',timeout=60000)
            runs=page.request.get(url+'/api/steles/tang_01_duobao/runs').json();real=next(r for r in runs if not r.get('legacy'))
        if real:
            goto(view='artifact',runId=real['runId']);expect(page.get_by_test_id('run-outcome')).to_be_visible();shot('artifact-run-report.png',full=True)
            exported=download('artifact-report.json');assert exported['runId']==real['runId'] and exported['stele']['id']=='tang_01_duobao'
            page.locator('header').first.get_by_role('button',name='智考工作台').click();expect(page.get_by_label('选择运行记录',exact=True)).to_have_value(real['runId'])
            goto(view='artifact',runId=real['runId'],steleId='qing_02_wushi_reerection');expect(page.get_by_role('alert').filter(has_text='不在').first).to_be_visible()
            assert download('wrong-owner-report.json')['runId'] is None
            checks.append('real run report, return to workbench and wrong-owner run rejection without data substitution')
        low=browser.new_context(viewport={'width':1366,'height':768},reduced_motion='no-preference');low.add_init_script("Object.defineProperty(navigator,'hardwareConcurrency',{get:()=>2})")
        lp=low.new_page();lp.goto(url+'/?tab=reports',wait_until='domcontentloaded');expect(lp.locator('[data-motion=reduced]')).to_be_visible()
        lp.evaluate("()=>{document.startViewTransition=undefined;window.__studioFallback=0;const original=Element.prototype.animate;Element.prototype.animate=function(...args){if(this.hasAttribute('inert'))window.__studioFallback++;return original.apply(this,args)}}")
        lp.get_by_test_id('studio-module-images').click();expect(lp.get_by_test_id('report-main-stage')).to_have_attribute('data-panel','images')
        assert lp.evaluate('window.__studioFallback')==0
        low.close();checks.append('low-concurrency devices switch panels without forcing FLIP animation')
        reduced=browser.new_context(viewport={'width':1366,'height':768},reduced_motion='reduce');reduced.add_init_script("Object.defineProperty(navigator,'hardwareConcurrency',{get:()=>8})");rp=reduced.new_page();rp.goto(url+'/?tab=reports',wait_until='domcontentloaded');expect(rp.locator('[data-motion=reduced]')).to_be_visible()
        rp.wait_for_timeout(100);assert rp.locator('.report-page').evaluate("e=>!e.getAnimations({subtree:true}).some(a=>a.playState==='running')")
        reduced.close();checks.append('reduced motion shows final values without CSS entrance animations')
        offline=browser.new_context();offline.route('**/api/**',lambda route:route.abort());op=offline.new_page();op.goto(url+'/?tab=reports',wait_until='domcontentloaded');expect(op.get_by_role('alert').filter(has_text='实验数据读取失败')).to_be_visible();expect(op.get_by_role('button',name='重新载入')).to_be_visible();offline.close();checks.append('backend unavailable and unknown experiment states are explicit')
        context.close();browser.close()
    assert not errors,errors
    result['status']='passed';(out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');return result

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',required=True);parser.add_argument('--output',type=Path,default=ROOT/'screenshots/report-redesign/final');parser.add_argument('--video',action='store_true');parser.add_argument('--exercise-run',action='store_true');args=parser.parse_args()
    print(json.dumps(run(assert_safe_target(args.url).rstrip('/'),args.output,args.video,args.exercise_run),ensure_ascii=False,indent=2))
