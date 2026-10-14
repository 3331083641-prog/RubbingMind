"""Real browser acceptance. No click is considered a pass without an assertion.
Backend validation precedes frontend startup; run on the existing Vite server.
"""
from pathlib import Path
import json
import time
import math
import argparse
import sys
import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'screenshots/stele-final'
OUT.mkdir(parents=True,exist_ok=True)
if sys.platform=='win32': sys.stdout.reconfigure(encoding='utf-8')
VIEWS={'front':'正面','back':'背面','left':'左侧','right':'右侧','top':'俯视','bottom':'仰视','perspective':'透视'}

def run(url):
    report={'url':url,'checks':{},'performance':{},'console_errors':[],'request_failures':[]}
    def check(name,condition,detail=None):
        report['checks'][name]={'pass':bool(condition),'detail':detail}
        print(('PASS ' if condition else 'FAIL ')+name,flush=True)
        save_report(report)
        assert condition,name
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True,args=['--use-gl=angle','--use-angle=d3d11','--enable-webgl'])
        page=browser.new_page(viewport={'width':1920,'height':1080},device_scale_factor=1)
        page.on('pageerror',lambda error:report['console_errors'].append(str(error)))
        page.on('console',lambda msg:report['console_errors'].append(msg.text) if msg.type=='error' else None)
        page.on('response',lambda response:report['request_failures'].append({'url':response.url,'status':response.status}) if response.status>=400 else None)
        page.goto(url,wait_until='networkidle',timeout=120000)
        page.wait_for_selector('canvas[data-stele-ready="true"]',timeout=120000)
        page.add_style_tag(content='body.stele-photo [data-stele-viewer] > :not(:first-child), body.stele-photo [data-stele-fullscreen] > :first-child {visibility:hidden;}')
        canvas=page.locator('canvas[data-stele-ready="true"]').last
        def inspect(): return canvas.evaluate('(c)=>window.__steleQA.get(c).inspect()')
        def preset(key,ui=True):
            if ui: page.get_by_role('button',name=VIEWS[key],exact=True).last.click()
            else: canvas.evaluate('(c,k)=>window.__steleQA.get(c).preset(k)',key)
            if ui:
                page.wait_for_function('c=>!window.__steleQA.get(c).inspect().transitioning',arg=canvas.element_handle(),timeout=15000)
            page.wait_for_timeout(250)
        def mode(m):
            canvas.evaluate('(c,m)=>window.__steleQA.get(c).renderMode(m)',m)
            page.evaluate('m=>document.body.classList.toggle("stele-photo",m!=="web")',m)
            page.wait_for_timeout(250)
        def screenshot(filename,window=False):
            (canvas.locator('..').locator('..') if window else canvas).screenshot(path=str(OUT/filename))
        def frame_ok(stats):
            pts=stats['bounds']
            return len(pts)==8 and all(abs(x)<.99 and abs(y)<.99 and -1<z<1 for x,y,z in pts)
        check('model loaded and PBR assigned',inspect()['ready'] and all(all(m[k] for k in ('map','normal','roughness','ao')) and m['metalness']==0 and not m['transparent'] for m in inspect()['materials']))
        for w,h in [(1920,1080),(1440,900),(1366,768)]:
            page.set_viewport_size({'width':w,'height':h}); preset('perspective')
            stats=inspect(); check(f'normal framing {w}x{h}',frame_ok(stats),stats['bounds'])
            screenshot(f'web_normal_{w}x{h}.png',True)
            for key in VIEWS:
                preset(key); check(f'normal preset {key} {w}x{h}',frame_ok(inspect()),inspect()['bounds'])
            preset('front')
        # Real input tests, compare resulting camera state.
        before=inspect(); rect=canvas.bounding_box(); cx=rect['x']+rect['width']*.5; cy=rect['y']+rect['height']*.47
        page.mouse.move(cx,cy); page.mouse.down(); page.mouse.move(cx+90,cy-20,steps=12); page.mouse.up(); page.wait_for_timeout(700)
        check('mouse rotation',math.dist(before['position'],inspect()['position'])>.1)
        before=inspect(); page.mouse.wheel(0,-260); page.wait_for_timeout(700)
        check('wheel zoom',abs(math.dist(before['position'],before['target'])-math.dist(inspect()['position'],inspect()['target']))>.1)
        before=inspect(); page.mouse.move(cx,cy); page.mouse.down(button='right'); page.mouse.move(cx+40,cy+20,steps=8); page.mouse.up(button='right'); page.wait_for_timeout(500)
        check('right mouse pan',math.dist(before['target'],inspect()['target'])>.02)
        preset('front'); a=inspect()['interaction']; page.wait_for_timeout(350); b=inspect()['interaction']
        check('laser moves on stone face',a['intensity']>0 and abs(a['scanY']-b['scanY'])>.001)
        page.get_by_role('button',name='激光扫描: 开',exact=True).last.click(); page.wait_for_timeout(100)
        check('laser off',inspect()['interaction']['intensity']==0)
        screenshot('web_restoration_before.png')
        slider=page.get_by_role('slider').last; slider.focus(); slider.press('End'); page.wait_for_timeout(200)
        check('repair slider changes shader',inspect()['interaction']['ratio']==1)
        screenshot('web_restoration_after.png')
        a=np.asarray(Image.open(OUT/'web_restoration_before.png')).astype(float); b=np.asarray(Image.open(OUT/'web_restoration_after.png')).astype(float)
        check('repair changes rendered pixels',float(np.abs(a-b).mean())>.15,float(np.abs(a-b).mean()))
        slider.press('Home'); page.wait_for_timeout(100)
        hotspot=inspect()['hotspots'][0]; rect=canvas.bounding_box()
        page.mouse.click(rect['x']+hotspot['x'],rect['y']+hotspot['y']); page.get_by_text('概念铭文 · 残损区域 A',exact=True).wait_for()
        check('hotspot click shows feedback',page.get_by_text('后验概率:',exact=False).is_visible())
        screenshot('web_hotspot.png',True)
        preset('back'); rect=canvas.bounding_box(); hotspot=inspect()['hotspots'][0]
        page.mouse.click(rect['x']+hotspot['x'],rect['y']+hotspot['y']); page.wait_for_timeout(100)
        check('back face occludes hotspot',not page.get_by_text('概念铭文 · 残损区域 A',exact=True).is_visible())
        # Fullscreen uses the same asset. Keep normal view mounted beneath it.
        page.get_by_role('button',name='全屏沉浸式展陈',exact=True).click()
        page.wait_for_function('document.querySelectorAll("canvas[data-stele-ready=true]").length===2',timeout=120000)
        canvas=page.locator('canvas[data-stele-ready="true"]').last
        for w,h in [(1920,1080),(1440,900),(1366,768)]:
            page.set_viewport_size({'width':w,'height':h}); preset('perspective')
            check(f'fullscreen framing {w}x{h}',frame_ok(inspect()))
            screenshot(f'web_fullscreen_{w}x{h}.png',True)
        page.set_viewport_size({'width':1440,'height':1200})
        for m in ['clay','pbr']:
            mode(m); folder=OUT/m; folder.mkdir(exist_ok=True)
            for key in VIEWS:
                preset(key,False); check(f'{m} view {key}',frame_ok(inspect()))
                filename=f'stele_{key}.png'
                canvas.screenshot(path=str(folder/filename))
                if m=='pbr': canvas.screenshot(path=str(OUT/filename))
        mode('web'); preset('perspective')
        page.wait_for_timeout(3000); report['performance']['fullscreen']=inspect()
        page.get_by_role('button',name='退出全屏',exact=True).first.click(); page.wait_for_timeout(400)
        canvas=page.locator('canvas[data-stele-ready="true"]').last
        check('fullscreen closes and releases',page.locator('canvas[data-stele-ready="true"]').count()==1 and page.evaluate('window.__steleDisposed.length>=1'))
        page.wait_for_timeout(3000)
        report['performance']['normal']=inspect()
        # Read-only regression visit, no data mutations or backend setup.
        for label,expected in [('贞石典藏馆','中华贞石数字典藏馆'),('智考工作台','频空域微痕修复与释读工作台'),('时空图谱中心','金石时空知识图谱'),('算法评测报告','算法消融评测与金石考据报告')]:
            page.get_by_role('button',name=label,exact=False).first.click(); page.wait_for_timeout(800)
            check('page preserved '+label,page.get_by_text(expected,exact=False).first.is_visible())
            if label=='贞石典藏馆':
                check('28 collection entries preserved',page.locator('header select option').count()==28)
                page.get_by_role('button',name='3D',exact=True).first.click()
                page.wait_for_selector('canvas[data-stele-ready="true"]',timeout=120000)
                check('museum 3D loads same model',page.locator('canvas[data-stele-ready="true"]').count()==1)
                page.get_by_role('button',name='退出全屏',exact=True).first.click()
        check('all stele renderers released after navigation',page.evaluate('window.__steleQA.size===0'))
        report['disposal']=page.evaluate('window.__steleDisposed')
        check('released geometry and textures',all(d['geometries']==0 and d['textures']==0 and d['disconnected'] for d in report['disposal']),report['disposal'])
        check('no JavaScript or WebGL errors',not report['console_errors'],report['console_errors'])
        stele_failures=[r for r in report['request_failures'] if '/model3d/final/' in r['url']]
        check('no missing stele resources',not stele_failures,stele_failures)
        browser.close()
    save_report(report)
    print('Browser acceptance complete',flush=True)

def save_report(report):
    def rounded(value):
        if isinstance(value,float): return round(value,4)
        if isinstance(value,dict): return {k:rounded(v) for k,v in value.items()}
        if isinstance(value,list): return [rounded(v) for v in value]
        return value
    (OUT/'browser-validation.json').write_text(json.dumps(rounded(report),ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--url',default='http://127.0.0.1:5173/?steleQA=1'); args=parser.parse_args(); run(args.url)
