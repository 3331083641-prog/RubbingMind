import os
import sys
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
EXP = 'controlled-rubbings-v2-text-2026-10-17'

def capture(mode='before'):
    out = ROOT / f'screenshots/report-ui-refinement/{mode}'
    out.mkdir(parents=True, exist_ok=True)
    channel = os.getenv('RUBBINGMIND_BROWSER_CHANNEL', 'msedge')
    url = 'http://127.0.0.1:8740'
    
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        page = context.new_page()

        def goto(**patch):
            params = {'tab': 'reports', 'view': 'global', 'steleId': 'tang_01_duobao', 'experimentId': EXP}
            params.update(patch)
            page.goto(url + '/?' + urlencode(params), wait_until='networkidle')

        # 1. 全局评测首屏
        goto()
        page.wait_for_timeout(800)
        page.screenshot(path=str(out / '1-global-overview-1440.png'), full_page=False)
        
        # 1920 & 1366
        page.set_viewport_size({'width': 1920, 'height': 1080})
        page.wait_for_timeout(600)
        page.screenshot(path=str(out / '1-global-overview-1920.png'), full_page=False)
        
        page.set_viewport_size({'width': 1366, 'height': 768})
        page.wait_for_timeout(600)
        page.screenshot(path=str(out / '1-global-overview-1366.png'), full_page=False)

        # 恢复 1440x900
        page.set_viewport_size({'width': 1440, 'height': 900})
        page.wait_for_timeout(400)

        # 2. 主图表展开效果 (专注模式)
        page.get_by_role('button', name='专注查看', exact=True).click()
        page.wait_for_timeout(600)
        page.screenshot(path=str(out / '2-focus-mode.png'), full_page=False)
        page.keyboard.press('Escape')
        page.wait_for_timeout(400)

        # 3. 图像对照展开效果
        btn = page.get_by_test_id('studio-module-images')
        (btn if btn.is_visible() else page.get_by_test_id('studio-secondary-images')).click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(out / '3-images-expanded.png'), full_page=False)

        # 4. 失败案例展示效果
        btn = page.get_by_test_id('studio-module-failures')
        (btn if btn.is_visible() else page.get_by_test_id('studio-secondary-failures')).click()
        page.wait_for_timeout(800)
        page.screenshot(path=str(out / '4-failures-wall.png'), full_page=False)
        # 展开一个案例详情
        first_card = page.get_by_test_id('failure-image-gallery').locator('button').first
        if first_card.is_visible():
            first_card.click()
            page.wait_for_timeout(600)
            page.screenshot(path=str(out / '4-failure-detail.png'), full_page=False)
            page.get_by_role('button', name='返回案例墙', exact=False).click()
            page.wait_for_timeout(400)

        # 5. 本件处理报告首屏 (tang_01_duobao 有 real run)
        runs = page.request.get(url + '/api/steles/tang_01_duobao/runs').json()
        real = next((r for r in runs if not r.get('legacy')), runs[0] if runs else None)
        run_id = real['runId'] if real else ''
        goto(view='artifact', runId=run_id)
        page.wait_for_timeout(800)
        page.screenshot(path=str(out / '5-artifact-first-screen.png'), full_page=False)

        # 6. 本件报告图像对比
        triptych = page.locator('[data-testid="run-triptych"]')
        if triptych.is_visible():
            triptych.scroll_into_view_if_needed()
            page.wait_for_timeout(400)
            page.screenshot(path=str(out / '6-artifact-image-contrast.png'), full_page=False)

        # 7. 本件报告证据详情 (包括决策链、参数等)
        page.screenshot(path=str(out / '7-artifact-full-page.png'), full_page=True)

        # 8. 无运行记录状态
        goto(view='artifact', steleId='han_01_caoquan', runId='')
        page.wait_for_timeout(800)
        page.screenshot(path=str(out / '8-artifact-empty-or-legacy.png'), full_page=False)

        # 9. 页面收尾与底部空白效果 (full page or scrolled to bottom)
        goto(view='global', panel='overview')
        page.wait_for_timeout(600)
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(400)
        page.screenshot(path=str(out / '9-page-bottom-overview.png'), full_page=False)
        page.screenshot(path=str(out / '9-global-fullpage.png'), full_page=True)

        # 10. 移动端布局 (390x844)
        page.set_viewport_size({'width': 390, 'height': 844})
        goto(view='global', panel='overview')
        page.wait_for_timeout(600)
        page.screenshot(path=str(out / '10-mobile-global-390.png'), full_page=False)
        goto(view='artifact', runId=run_id)
        page.wait_for_timeout(600)
        page.screenshot(path=str(out / '10-mobile-artifact-390.png'), full_page=False)

        browser.close()
    print(f'Captured {mode} screenshots successfully in {out}')

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'before'
    capture(mode)
