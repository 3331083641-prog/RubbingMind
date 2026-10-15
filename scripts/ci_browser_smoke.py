"""Small Chromium browser regression for the five-page shell and 28-card fallback."""
import os
import re
from playwright.sync_api import sync_playwright, expect

URL = os.environ.get('RUBBINGMIND_FRONTEND_URL', 'http://127.0.0.1:5173')

def enter_page(page, label, marker, count=None):
    """Retry a navigation if Vite's first dependency optimization reloads dev mode."""
    for attempt in range(3):
        page.locator('header').first.get_by_role('button', name=label).click()
        try:
            if count is None:
                expect(marker).to_be_visible(timeout=12000)
            else:
                expect(marker).to_have_count(count, timeout=12000)
            page.wait_for_timeout(700)
            if count is None:
                expect(marker).to_be_visible(timeout=3000)
            else:
                expect(marker).to_have_count(count, timeout=3000)
            return
        except AssertionError:
            if attempt == 2:
                raise
            page.wait_for_load_state('domcontentloaded')
            page.wait_for_timeout(500)

with sync_playwright() as p:
    channel = os.environ.get('RUBBINGMIND_BROWSER_CHANNEL')
    browser = p.chromium.launch(channel=channel, headless=True, args=['--enable-unsafe-swiftshader'])
    for offline in (False, True):
        context = browser.new_context(viewport={'width': 1440, 'height': 900})
        if offline:
            context.route('**/api/**', lambda route: route.abort())
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(URL)
        expect(page.get_by_role('button', name='首页门户')).to_be_visible()
        enter_page(page, '贞石典藏馆', page.get_by_test_id('museum-card'), 28)
        for dynasty in ['东汉', '北魏', '唐代', '宋代', '元代', '明代', '清代']:
            page.get_by_role('button', name=re.compile('^' + dynasty + r'\s*4$')).click()
            expect(page.get_by_test_id('museum-card')).to_have_count(4)
        enter_page(page, '智考工作台', page.get_by_role('heading', name='真实处理历史'))
        enter_page(page, '时空图谱中心', page.get_by_test_id('stele-tang-duobao'))
        enter_page(page, '算法评测报告', page.get_by_role('heading', name='墨韵智考·金石数字化实验报告').last)
        assert not errors, errors
        context.close()
    browser.close()
print('Browser smoke passed: online + fallback, five-page shell, 28 items, seven filters.')
