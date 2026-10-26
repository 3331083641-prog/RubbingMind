"""Chromium regression for the five-page shell, 28 cards, and offline fallback.

The catalogue status attribute must leave "loading" before any card count is
trusted. CI should point this script at a built preview, not the Vite dev
server, so dependency optimization cannot reload the page mid-assertion.
A failure writes a screenshot, console log, network log, and Playwright trace.
"""
import json
import os
import re
import traceback
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

URL = os.environ.get('RUBBINGMIND_FRONTEND_URL', 'http://127.0.0.1:5173')
OUT = Path(__file__).resolve().parents[1] / 'screenshots' / 'ci-smoke'
PAGES = (
    ('贞石典藏馆', 'museum'),
    ('智考工作台', 'workbench'),
    ('时空图谱中心', 'graph'),
    ('算法评测报告', 'reports'),
)


def _status(page):
    return page.locator('[data-catalogue-status]').first


def wait_catalogue(page, expected):
    page.wait_for_function(
        """(expected) => document.querySelector('[data-catalogue-status]')?.dataset.catalogueStatus === expected""",
        arg=expected,
        timeout=20000,
    )


def open_page(page, label, tab):
    page.locator('header').first.get_by_role('button', name=label).click()
    page.wait_for_function(
        """(tab) => document.querySelector('[data-catalogue-status]')?.dataset.tab === tab""",
        arg=tab,
        timeout=20000,
    )


def wait_museum(page, count):
    page.wait_for_function(
        """(count) => {
          const root = document.querySelector('[data-catalogue-status]');
          const museum = document.querySelector('[data-testid="museum-page"]');
          const cards = document.querySelectorAll('[data-testid="museum-card"]');
          return root && museum && root.dataset.catalogueStatus !== 'loading'
            && root.dataset.tab === 'museum'
            && cards.length === count
            && museum.dataset.visibleCount === String(count);
        }""",
        arg=count,
        timeout=20000,
    )


def dump_failure(context, page, console, network, exc):
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        page.screenshot(path=str(OUT / 'failure.png'), full_page=True)
    except Exception as shot_error:
        (OUT / 'screenshot-error.txt').write_text(str(shot_error), encoding='utf-8')
    (OUT / 'console.json').write_text(json.dumps(console, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'network.json').write_text(json.dumps(network[-80:], ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'error.txt').write_text(''.join(traceback.format_exception(exc)), encoding='utf-8')
    try:
        context.tracing.stop(path=str(OUT / 'trace.zip'))
    except Exception:
        pass


def run(url=URL):
    channel = os.environ.get('RUBBINGMIND_BROWSER_CHANNEL')
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=channel, headless=True, args=['--enable-unsafe-swiftshader'])
        try:
            for offline in (False, True):
                context = browser.new_context(viewport={'width': 1440, 'height': 900})
                context.tracing.start(screenshots=True, snapshots=True, sources=True)
                if offline:
                    context.route('**/api/**', lambda route: route.abort())
                page = context.new_page()
                console, network, page_errors = [], [], []
                page.on('console', lambda message: console.append({'type': message.type, 'text': message.text}))
                page.on('pageerror', lambda error: page_errors.append(str(error)))
                page.on('response', lambda response: network.append({'url': response.url, 'status': response.status}))
                page.on('requestfailed', lambda request: network.append({'url': request.url, 'status': 'failed', 'error': request.failure}))
                try:
                    page.goto(url, wait_until='domcontentloaded')
                    expect(page.get_by_role('button', name='首页门户')).to_be_visible()
                    wait_catalogue(page, 'fallback' if offline else 'ready')
                    open_page(page, '贞石典藏馆', 'museum')
                    wait_museum(page, 28)
                    ids = page.locator('[data-testid="museum-card"]').evaluate_all("nodes => nodes.map(node => node.dataset.steleId)")
                    assert len(ids) == len(set(ids)) == 28, ids
                    banner = page.get_by_test_id('museum-banner-art')
                    expect(banner).to_have_css('background-size', 'cover')
                    expect(banner).to_have_css('pointer-events', 'none')
                    art = page.request.get(url.rstrip('/') + banner.get_attribute('data-banner-src'))
                    assert art.status == 200, art.status
                    assert art.headers.get('content-type', '').startswith('image/webp'), art.headers.get('content-type')
                    for dynasty in ['东汉', '北魏', '唐代', '宋代', '元代', '明代', '清代']:
                        page.get_by_role('button', name=re.compile('^' + dynasty + r'\s*4$')).click()
                        page.wait_for_function(
                            """() => document.querySelector('[data-testid="museum-page"]')?.dataset.visibleCount === '4'
                              && document.querySelectorAll('[data-testid="museum-card"]').length === 4""",
                            timeout=10000,
                        )
                    open_page(page, '智考工作台', 'workbench')
                    expect(page.get_by_role('heading', name='真实处理历史')).to_be_visible(timeout=20000)
                    open_page(page, '时空图谱中心', 'graph')
                    expect(page.get_by_test_id('stele-tang-duobao')).to_be_visible(timeout=20000)
                    open_page(page, '算法评测报告', 'reports')
                    expect(page.get_by_test_id('report-context-bar')).to_be_visible(timeout=20000)
                    if not offline:
                        expect(page.get_by_test_id('global-evaluation')).to_be_visible(timeout=20000)
                    else:
                        expect(page.get_by_role('alert').filter(has_text='实验数据读取失败')).to_be_visible(timeout=20000)
                    assert not page_errors, page_errors
                    context.tracing.stop()
                except Exception as exc:
                    dump_failure(context, page, console, network, exc)
                    raise
                finally:
                    context.close()
        finally:
            browser.close()
    print('Browser smoke passed: online + fallback, five-page shell, 28 items, seven filters.')


if __name__ == '__main__':
    run()
