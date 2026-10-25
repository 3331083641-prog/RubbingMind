"""Real Playwright browser acceptance and captures. Requires running backend + Vite."""
import json, os, sys
from pathlib import Path
import requests
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
BACKEND_URL=os.environ.get('GRAPH_BACKEND_URL','')
FRONTEND_URL=os.environ.get('GRAPH_FRONTEND_URL','')
from scripts.browser_target import assert_safe_target
BACKEND_URL = assert_safe_target(BACKEND_URL, label='GRAPH_BACKEND_URL')
FRONTEND_URL = assert_safe_target(FRONTEND_URL, label='GRAPH_FRONTEND_URL')
OUT=Path(os.environ.get('GRAPH_SCREENSHOT_DIR', str(ROOT/'screenshots/remediation-2026-10-15/graph')))
OUT.mkdir(parents=True,exist_ok=True)
if hasattr(sys.stdout,'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')

def capture(page, path):
    # Locator actions may scroll down to the timeline. Keep sticky navigation at the
    # document top before a full-page capture, so it cannot be composited mid-page.
    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_timeout(150)
    page.screenshot(path=str(path),full_page=True)

def network_node_position(page, name):
    return page.evaluate('''async (name) => {
        const url=performance.getEntriesByType('resource').find(e=>e.name.includes('echarts_core.js')).name;
        const module=await import(url);
        const chart=module.getInstanceByDom(document.querySelector('[data-testid="knowledge-network"]>div'));
        const data=chart.getModel().getSeriesByIndex(0).getData();
        const node=data.getItemGraphicEl(data.indexOfName(name));
        const xy=node.transformCoordToGlobal(0,0);
        return {x:xy[0],y:xy[1],zoom:chart.getOption().series[0].zoom};
    }''',name)

def run():
    assert requests.get(BACKEND_URL+'/health',timeout=10).json()['status']=='healthy'
    assert requests.get(BACKEND_URL+'/generate',timeout=10).json()['steleId']=='tang-duobao'
    errors=[]; checks=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
        page.goto(FRONTEND_URL+'/',wait_until='networkidle')
        page.get_by_role('button',name='时空图谱中心').click()
        map=page.locator('[data-testid="historical-map"]')
        expect(map).to_have_attribute('data-ready','true',timeout=25000)
        page.wait_for_timeout(1500)
        expect(page.locator('.map-error')).to_have_count(0)
        assert page.evaluate('innerWidth')==1920
        capture(page, OUT/'01_中国全国地图.png')
        checks.append('初始全国底图、南海附图与省界加载')
        ids=[('tang-duobao','tang_01_duobao',752,'02_多宝塔碑GIS.png'),('han-caoquan','han_01_caoquan',185,'03_曹全碑GIS.png'),('wei-yuanhuai','wei-yuanhuai',517,'04_元怀墓志GIS.png'),('wei-jianyi','wei-jianyi',528,'05_建义元年样本GIS.png')]
        for width,height in [(1920,1080),(1440,900),(1366,768)]:
            page.set_viewport_size({'width':width,'height':height})
            for core,record,year,file in ids:
                page.get_by_test_id('stele-'+core).click()
                expect(page.locator('.calendar-result')).to_contain_text(str(year))
                expect(page.locator('header select').first).to_have_value(core)
                page.get_by_role('button',name='碑刻地理',exact=True).click()
                page.wait_for_timeout(950)
                assert page.evaluate('document.documentElement.scrollWidth')<=width, '横向溢出'
                expect(page.locator('.map-error')).to_have_count(0)
                expect(page.locator('.graph-page img')).not_to_have_count(0)
                assert page.locator('.graph-page img').evaluate_all('(imgs)=>imgs.every(i=>i.complete && i.naturalWidth>0)'), '图像缺失'
                if core=='wei-jianyi':
                    expect(page.locator('.historical-marker')).to_have_count(0)
                    expect(page.locator('.selected-entity')).to_contain_text('测试样本')
                    assert '昌黎韩夫人' not in page.locator('.graph-page').inner_text()
                if core=='han-caoquan': assert '千福寺' not in page.locator('.history-timeline').inner_text()
                capture(page, OUT/f'{width}x{height}_{core}.png')
                if width==1440: capture(page, OUT/file)
                checks.append(f'{width}×{height} 四碑切换 {core}')
            expect(page.locator('.graph-page canvas')).to_have_count(2)
        page.set_viewport_size({'width':1440,'height':900})
        page.get_by_test_id('stele-han-caoquan').click()
        expect(page.locator('.calendar-result')).to_contain_text('185')
        page.get_by_role('button',name='返回全国视图',exact=True).click()
        page.wait_for_timeout(800)
        before=float(map.get_attribute('data-zoom'))
        canvas=page.locator('.map-region canvas').first
        box=canvas.bounding_box()
        page.mouse.move(box['x']+box['width']*.4,box['y']+box['height']*.4)
        page.mouse.wheel(0,-550);page.wait_for_timeout(800)
        assert float(map.get_attribute('data-zoom'))>before
        old_center=map.get_attribute('data-center')
        page.mouse.down();page.mouse.move(box['x']+box['width']*.4+90,box['y']+box['height']*.4+50,steps=10);page.mouse.up();page.wait_for_timeout(700)
        assert map.get_attribute('data-center')!=old_center
        checks.append('真实地图滚轮缩放与拖拽平移')
        page.get_by_label('检索历史地名').fill('敦煌')
        page.get_by_role('option',name='敦煌效谷地望').click()
        expect(page.locator('.selected-entity')).to_contain_text('敦煌')
        expect(page.locator('.coordinate-detail')).to_contain_text('WGS84')
        page.wait_for_timeout(850)
        lng,lat=map.get_attribute('data-center').split(',')
        assert 92<float(lng)<96 and 39<float(lat)<42
        checks.append('地点检索、区域定位和坐标证据')
        page.get_by_role('button',name='自动定位',exact=True).click();page.wait_for_timeout(850)
        page.locator('[data-place-id="beilin"]').dblclick();page.wait_for_timeout(850)
        assert float(map.get_attribute('data-zoom'))>=9.9, map.get_attribute('data-zoom')
        checks.append('地点点击与双击局部放大')
        page.get_by_role('button',name='图层',exact=True).click()
        page.get_by_label('历史关联线',exact=True).check()
        expect(page.locator('.association-note')).to_contain_text('不代表')
        page.get_by_label('节点光晕与地形阴影',exact=True).uncheck()
        page.get_by_label('历史地点标签',exact=True).uncheck()
        expect(page.locator('.marker-label')).to_have_count(0)
        page.get_by_role('button',name='图层',exact=True).click()
        checks.append('图层开关、关闭光晕、关联线语义')
        page.get_by_role('button',name='人物关系',exact=True).click()
        expect(page.get_by_test_id('knowledge-network')).to_be_visible()
        page.wait_for_timeout(2000)
        page.get_by_label('筛选图谱节点').select_option('person')
        expect(page.locator('.node-filter')).to_contain_text('3 节点 · 2 关系')
        page.wait_for_timeout(1600)
        point=network_node_position(page,'曹全 · 景完')
        chart_box=page.locator('.knowledge-network canvas').bounding_box()
        page.mouse.click(chart_box['x']+point['x'],chart_box['y']+point['y'])
        expect(page.locator('.selected-entity')).to_contain_text('曹全')
        # Read actual rendered symbol coordinates and operate the canvas with the mouse.
        point=network_node_position(page,'曹全 · 景完')
        chart_box=page.locator('.knowledge-network canvas').bounding_box()
        page.mouse.move(chart_box['x']+point['x'],chart_box['y']+point['y']);page.mouse.down()
        page.mouse.move(chart_box['x']+point['x']+80,chart_box['y']+point['y']-25,steps=15);page.mouse.up()
        page.wait_for_timeout(250)
        moved=network_node_position(page,'曹全 · 景完')
        assert abs(moved['x']-point['x'])>15, '人物节点没有拖动'
        chart_box=page.locator('.knowledge-network canvas').bounding_box()
        page.mouse.move(chart_box['x']+chart_box['width']*.5,chart_box['y']+chart_box['height']*.4)
        page.mouse.wheel(0,-300);page.wait_for_timeout(700)
        zoomed=network_node_position(page,'曹全 · 景完')
        assert zoomed['zoom']>moved['zoom'], {'before':moved,'after':zoomed}
        checks.append('真实网络 Canvas 点击、节点拖动与滚轮缩放；筛选计数')
        capture(page, OUT/'06_人物知识图谱.png')
        page.get_by_label('筛选图谱节点').select_option('all')
        page.get_by_role('button',name='地图与图谱联动',exact=True).click()
        page.wait_for_timeout(1500)
        expect(page.get_by_test_id('knowledge-network')).to_be_visible()
        expect(map).to_be_visible()
        capture(page, OUT/'07_地图图谱联动.png')
        checks.append('知识网络筛选、人物考据与地图分屏联动')
        page.get_by_role('button',name='人物关系',exact=True).click()
        page.get_by_role('button',name='返回全国视图',exact=True).click()
        expect(map).to_be_visible()
        expect(page.get_by_test_id('knowledge-network')).to_have_count(0)
        checks.append('纯网络模式返回全国地图')
        page.get_by_role('button',name='历史轨迹',exact=True).click()
        page.get_by_test_id('event-cao-1956').click();page.wait_for_timeout(950)
        expect(page.locator('.selected-entity')).to_contain_text('移藏西安碑林')
        lng,lat=map.get_attribute('data-center').split(',')
        assert 108.9<float(lng)<109 and 34.2<float(lat)<34.3
        capture(page, OUT/'08_历史时间轴.png')
        page.get_by_label('轨迹播放速度').select_option('2')
        page.get_by_role('button',name='重新播放',exact=True).click()
        expect(page.get_by_role('button',name='暂停历史轨迹',exact=True)).to_be_visible()
        page.wait_for_timeout(1600)
        expect(page.locator('.selected-entity')).to_contain_text('举孝廉')
        page.get_by_role('button',name='暂停历史轨迹',exact=True).click()
        page.wait_for_timeout(1600)
        expect(page.locator('.selected-entity')).to_contain_text('举孝廉')
        page.get_by_role('button',name='重新播放',exact=True).click()
        expect(page.get_by_role('button',name='播放历史轨迹',exact=True)).to_be_visible(timeout=11000)
        expect(page.locator('.selected-entity')).to_contain_text('移藏西安碑林')
        checks.append('时间轴点击定位、播放、暂停、重播、速度与自动停止')
        for q,expected in [('唐天宝十一载','752'),('东汉中平二年','185'),('北魏熙平二年','517'),('北魏建义元年','528')]:
            page.get_by_label('纪年输入').fill(q);page.get_by_role('button',name='换算',exact=True).click()
            expect(page.locator('.calendar-result')).to_contain_text(expected)
        page.get_by_label('纪年输入').fill('未知年号');page.get_by_role('button',name='换算',exact=True).click()
        expect(page.locator('.unsupported')).to_contain_text('暂不支持或待考证')
        page.get_by_label('纪年输入').fill('东汉中平二年');page.get_by_role('button',name='换算',exact=True).click()
        expect(page.locator('.calendar-result')).to_contain_text('乙丑')
        capture(page, OUT/'09_纪年换算器.png')
        checks.append('四碑年号、干支与未知纪年拒绝回退')
        page.get_by_role('button',name='重置',exact=True).click();page.wait_for_timeout(850)
        expect(page.locator('.selected-entity')).to_contain_text('曹全碑')
        expect(page.get_by_label('纪年输入')).to_have_value('东汉中平二年')
        expect(page.locator('.graph-page canvas')).to_have_count(2)
        checks.append('全页恢复默认状态与 Canvas 实例数量')
        # Re-entering the graph disposes all map/chart listeners and instances.
        page.get_by_role('button',name='贞石典藏馆').click()
        expect(page.locator('.graph-page')).to_have_count(0)
        page.get_by_role('button',name='时空图谱中心').click()
        expect(map).to_have_attribute('data-ready','true',timeout=15000)
        page.wait_for_timeout(800)
        expect(page.locator('.graph-page canvas')).to_have_count(2)
        checks.append('切页卸载与重新载入；典藏馆未受影响')
        browser.close()
    report={'status':'passed' if not errors else 'failed','viewports':['1920x1080','1440x900','1366x768'],'checks':checks,'browserErrors':errors}
    (OUT/'browser-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
    assert not errors, errors

if __name__=='__main__':run()
