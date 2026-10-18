"""Actual Chromium/Edge E2E acceptance for online and fallback museum modes."""
import argparse,json,re,sys,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from catalog import museum_records,load

def run(url,output):
    output.mkdir(parents=True,exist_ok=True);rows=museum_records();results={'online':{},'fallback':{},'errors':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True,args=['--enable-unsafe-swiftshader'])
        for offline in [False,True]:
            mode='fallback' if offline else 'online'
            ctx=browser.new_context(viewport={'width':1920,'height':1080},accept_downloads=True)
            if offline:ctx.route('**/api/**',lambda route:route.abort())
            page=ctx.new_page();page.on('pageerror',lambda error:results['errors'].append(str(error)))
            page.goto(url);expect(page.locator('header').get_by_role('button',name='贞石典藏馆',exact=False)).to_be_visible()
            expect(page.locator('canvas').first).to_be_visible(timeout=30000)
            if not offline:page.screenshot(path=str(output/'00_首页核心入口.png'),full_page=True)
            page.locator('header').get_by_role('button',name='贞石典藏馆').click()
            expect(page.get_by_test_id('museum-card')).to_have_count(28)
            before=[]
            for r in rows:
                card=page.locator(f'[data-stele-id="{r["id"]}"]');card.scroll_into_view_if_needed()
                expect(card.get_by_role('heading',name=r['title'],exact=True)).to_be_visible()
                for field in ['year','rubbingPeriod','collectionInstitution','collectionNumber','artifactType']:
                    assert r[field] in card.inner_text(),(r['id'],field)
                img=card.get_by_test_id('museum-cover')
                expect(img).to_have_attribute('src',r['imageAssets']['cover'])
                page.wait_for_function('(id)=>{const i=document.querySelector(`[data-stele-id="${id}"] img`);return i && i.complete && i.naturalWidth===1100 && i.naturalHeight===1420}',arg=r['id'])
                assert card.get_by_role('link',name='查看馆藏来源',exact=True).get_attribute('href')==r['sourceUrl']
                before.append(r['id'])
            results[mode]['verifiedCards']=before
            dynasties=['全部','东汉','北魏','唐代','宋代','元代','明代','清代']
            for index,dynasty in enumerate(dynasties,1):
                page.get_by_role('button',name=re.compile('^'+dynasty+r'\s*\d+$')).click()
                expect(page.get_by_test_id('museum-card')).to_have_count(28 if dynasty=='全部' else 4)
                if dynasty!='全部':assert set(page.get_by_test_id('museum-card').evaluate_all('(cards)=>cards.map(c=>c.dataset.steleId)'))=={r['id'] for r in rows if r['dynasty']==dynasty}
                if not offline:page.screenshot(path=str(output/f'{index:02d}_{dynasty}{28 if index==1 else 4}件.png'),full_page=True)
            results[mode]['dynastyCounts']={d:28 if d=='全部' else 4 for d in dynasties}
            # Genuine combined filtering, including an empty result and reset.
            page.get_by_role('button',name=re.compile(r'^元代\s*4$')).click()
            search=page.get_by_placeholder('搜索碑名、书家、撰文者、馆藏号、地望...')
            search.fill('贈拓000412');expect(page.get_by_test_id('museum-card')).to_have_count(1)
            grade=page.locator('[data-stele-id="yuan_04_jingyuanchang"]').get_attribute('data-image-condition')
            page.get_by_role('button',name=grade,exact=True).click();expect(page.get_by_test_id('museum-card')).to_have_count(1)
            page.get_by_role('button',name='严重漫漶',exact=True).click();expect(page.get_by_test_id('museum-card')).to_have_count(0)
            page.get_by_role('button',name='重置所有筛选条件').click();expect(page.get_by_test_id('museum-card')).to_have_count(28)
            results[mode]['searchWeatheringCombined']=True
            replacements=[r for r in rows if r['id'] in {x['newId'] for x in load('replacement_mapping.json')}]
            inspect=[rows[0],rows[4],rows[8],rows[12],rows[20],*replacements]
            for r in inspect:
                card=page.locator(f'[data-stele-id="{r["id"]}"]')
                for role,label in [('readable','查看高清拓本'),('archive','查看完整档案')]:
                    card.get_by_role('button',name=label,exact=True).click();dialog=page.get_by_role('dialog')
                    expect(dialog.get_by_test_id('archive-image')).to_have_attribute('src',r['imageAssets'][role])
                    page.wait_for_function('()=>{const i=document.querySelector(`[data-testid="archive-image"]`);return i && i.complete && i.naturalWidth>0}')
                    dialog.get_by_role('button',name='放大',exact=True).click();expect(dialog.get_by_test_id('archive-zoom')).to_have_text('125%')
                    dialog.get_by_role('button',name='缩小',exact=True).click();expect(dialog.get_by_test_id('archive-zoom')).to_have_text('100%')
                    canvas=dialog.get_by_test_id('archive-pan');box=canvas.bounding_box()
                    page.mouse.move(box['x']+150,box['y']+100);page.mouse.down();page.mouse.move(box['x']+225,box['y']+150);page.mouse.up()
                    assert '75px' in dialog.get_by_test_id('archive-image').get_attribute('style')
                    if not offline and r==rows[0]:page.screenshot(path=str(output/('09_高清拓本查看.png' if role=='readable' else '10_完整馆藏档案.png')))
                    if not offline and r['id']=='yuan_04_jingyuanchang' and role=='readable':page.screenshot(path=str(output/'11_元代新替换馆藏.png'))
                    dialog.get_by_role('button',name='关闭档案').click()
            results[mode]['detailReadArchiveZoomPan']=[r['id'] for r in inspect]
            if not offline:
                page.get_by_role('button',name=re.compile(r'^清代\s*4$')).click();page.screenshot(path=str(output/'12_清代四件新馆藏.png'),full_page=True)
            # Fail a cover explicitly: verify failure/retry, never another rubbing.
            page.get_by_role('button',name=re.compile(r'^全部\s*28$')).click()
            first=rows[0];page.route('**/'+first['id']+'_cover.jpg*',lambda route:route.abort())
            page.evaluate('(id)=>{const img=document.querySelector(`[data-stele-id="${id}"] img`);img.src=img.src+"&acceptance_failure=1"}',first['id'])
            firstcard=page.locator(f'[data-stele-id="{first["id"]}"]');expect(firstcard.get_by_text('本件图像加载失败')).to_be_visible()
            assert firstcard.locator('img').count()==0
            page.unroute('**/'+first['id']+'_cover.jpg*');firstcard.get_by_role('button',name='重试').click()
            expect(firstcard.get_by_test_id('museum-cover')).to_be_visible();results[mode]['failureRetryNoSubstitution']=True
            # Every museum action resolves the same artifact in the workbench.
            for r in rows:
                page.locator(f'[data-stele-id="{r["id"]}"]').get_by_role('button',name='微痕修复').click()
                expect(page.locator('header').first.locator('select')).to_have_value(r['id'])
                expect(page.get_by_text('当前文物输入图像 · 尚未生成算法修复结果')).to_be_visible()
                assert page.locator(f'img[src="{r["imageAssets"]["readable"]}"]').count()>0
                page.locator('header').get_by_role('button',name='贞石典藏馆').click()
            results[mode]['museumWorkbenchIds']=28
            # Four existing core entries, actual original asset, no forced Wang Song mapping.
            page.get_by_role('button',name='智考工作台').click()
            for core in load('core_samples.json'):
                page.locator('header').first.locator('select').select_option(core['id'])
                expect(page.locator('header').first.locator('select')).to_have_value(core['id'])
                assert page.locator(f'img[src="{core["raw_image"]}"]').count()>0
            results[mode]['coreIds']=[r['id'] for r in load('core_samples.json')]
            if not offline:page.screenshot(path=str(output/'13_核心工作台兼容验证.png'),full_page=True)
            page.get_by_role('button',name='时空图谱中心').click();page.wait_for_timeout(700)
            expect(page.locator('header').first.locator('select')).to_have_value('wei-jianyi')
            results[mode]['coreGraphPage']=True
            page.locator('header').first.locator('select').select_option('qing_02_wushi_reerection')
            expect(page.get_by_role('heading',name='重立武氏祠石记 · 馆藏资料关联')).to_be_visible()
            assert '翁方纲' in page.inner_text('main');results[mode]['verifiedMuseumGraph']=True
            page.get_by_role('button',name='算法评测报告').click()
            expect(page.get_by_role('heading',name='墨韵智考·金石数字化实验报告').last).to_be_visible()
            page.get_by_role('combobox',name='选择报告运行记录').select_option('')
            expect(page.get_by_text('尚未执行处理。没有真实运行输出或配对真值评测。')).to_be_visible()
            with page.expect_download() as info:page.get_by_role('button',name='导出 JSON').click()
            download=info.value;dest=output/(mode+'_报告.json');download.save_as(dest)
            report=json.loads(dest.read_text('utf-8'));assert report['stele']['id']=='qing_02_wushi_reerection' and report['stele']['title']=='重立武氏祠石记' and report['evaluationStatus']=='not_run'
            page.evaluate('window.print=()=>window.__printCalled=true');page.get_by_role('button',name='打印 / 保存 PDF').click();assert page.evaluate('window.__printCalled')
            if not offline:page.pdf(path=str(output/'14_实际网页报告.pdf'),format='A4',print_background=True)
            results[mode]['jsonAndPrintPdf']=True
            # Second required viewport.
            page.set_viewport_size({'width':1440,'height':900});page.locator('header').get_by_role('button',name='贞石典藏馆').click()
            expect(page.get_by_test_id('museum-card')).to_have_count(28)
            assert page.evaluate('document.documentElement.scrollWidth <= 1440')
            if not offline:page.screenshot(path=str(output/'15_1440x900典藏馆.png'),full_page=True)
            results[mode]['viewport1440x900']=True;ctx.close()
        browser.close()
    assert not results['errors'],results['errors']
    (output/'browser_acceptance.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf-8')
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:5175');parser.add_argument('--output',type=Path,default=ROOT/'screenshots/museum-v3');args=parser.parse_args()
    print(json.dumps(run(args.url,args.output),ensure_ascii=False,indent=2))
