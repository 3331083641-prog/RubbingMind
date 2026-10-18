"""Browser regression for the homepage hero ambient background video.

Run against a running frontend (dev or preview), e.g.
    set RUBBINGMIND_FRONTEND_URL=http://127.0.0.1:4173
    set RUBBINGMIND_BROWSER_CHANNEL=msedge
    python scripts/test_home_ambient_video_browser.py [--screenshots screenshots/home-video]

Optionally also check the Vite dev server, where React.StrictMode mounts -> cleans up -> re-runs
effects on the same <video> (a cleanup that strips the source used to leave only the poster):
    set RUBBINGMIND_DEV_URL=http://127.0.0.1:5180

H.264 playback needs a browser with proprietary codecs (Edge / Chrome channel). With the bundled
open-source Chromium the component must fall back to the poster, which this script also accepts.
/api is aborted on purpose: this test only covers the frontend background layer.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

URL = os.environ.get('RUBBINGMIND_FRONTEND_URL', 'http://127.0.0.1:5173').rstrip('/')
DEV_URL = (os.environ.get('RUBBINGMIND_DEV_URL') or '').rstrip('/')
CHANNEL = os.environ.get('RUBBINGMIND_BROWSER_CHANNEL') or None
VIDEO = '/assets/home/home-ambient-loop.mp4'
POSTER = '/assets/home/home-ambient-poster.webp'
BG = '[data-testid="home-ambient-bg"]'

parser = argparse.ArgumentParser()
parser.add_argument('--screenshots', default='')
parser.add_argument('--ci', action='store_true', help='Check assets, poster fallback, and playback only when this browser can decode H.264.')
args = parser.parse_args()
shots = Path(args.screenshots) if args.screenshots else None
if shots:
    shots.mkdir(parents=True, exist_ok=True)

results = {}


def shot(page, name):
    if shots:
        page.screenshot(path=str(shots / name))


def watch(page):
    problems = []
    page.on('pageerror', lambda e: problems.append(f'pageerror: {e}'))
    page.on('console', lambda m: m.type == 'error' and '/api' not in (m.location or {}).get('url', '')
            and 'ERR_FAILED' not in m.text and problems.append(f'console: {m.text}'))
    page.on('response', lambda r: r.status >= 400 and '/api/' not in r.url and problems.append(f'{r.status} {r.url}'))
    return problems


def new_context(browser, **kw):
    context = browser.new_context(**kw)
    context.route('**/api/**', lambda route: route.abort())
    return context


def state(page):
    return page.evaluate("""() => {
      const bg = document.querySelector('[data-testid="home-ambient-bg"]');
      const v = bg && bg.querySelector('video');
      return {mode: bg && bg.dataset.ambientMode, reason: bg && bg.dataset.ambientReason,
        hasVideo: !!v, paused: v ? v.paused : null, muted: v ? v.muted : null, loop: v ? v.loop : null,
        t: v ? v.currentTime : null, duration: v ? v.duration : null, readyState: v ? v.readyState : null,
        pointer: bg ? getComputedStyle(bg).pointerEvents : null,
        scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth};
    }""")


def hero_check(page, width, height):
    """Background covers the hero (padding box; the 1px bottom border stays visible), no horizontal scroll, title and buttons visible."""
    info = page.evaluate("""() => {
      const bg = document.querySelector('[data-testid="home-ambient-bg"]');
      const hero = bg.parentElement; const a = bg.getBoundingClientRect(), b = hero.getBoundingClientRect();
      const v = bg.querySelector('video'); const vr = v && v.getBoundingClientRect();
      return {bg: [a.x, a.y, a.width, a.height], hero: [b.x, b.y, b.width, b.height],
              video: vr ? [vr.x, vr.y, vr.width, vr.height] : null,
              fit: v ? getComputedStyle(v).objectFit : null,
              scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth};
    }""")
    assert all(abs(x - y) <= 1.5 for x, y in zip(info['bg'], info['hero'])), info
    if info['video']:
        assert all(abs(x - y) <= 1.5 for x, y in zip(info['video'], info['hero'])), info
        assert info['fit'] == 'cover', info
    assert info['scrollW'] <= info['innerW'], f'horizontal scroll at {width}: {info}'
    expect(page.get_by_role('heading', name='墨韵智考')).to_be_visible()
    for name in ['进入智考修复工作台', '浏览中华贞石典藏馆', '时空图谱与 GIS 考据']:
        button = page.get_by_role('button', name=name)
        expect(button).to_be_visible()
        box = button.bounding_box()
        # The button itself (not the background) must be the hit-test target at its centre.
        hit = page.evaluate('([x,y]) => { const el = document.elementFromPoint(x,y); return el && !!el.closest("button"); }',
                            [box['x'] + box['width'] / 2, box['y'] + box['height'] / 2])
        if box['y'] + box['height'] / 2 < height:
            assert hit, f'{name} not hit-testable at {width}'
    return info


def wait_playing(page, timeout=15000):
    page.wait_for_function("""() => { const v = document.querySelector('[data-testid="home-ambient-bg"] video');
      return v && !v.paused && v.currentTime > 0.3; }""", timeout=timeout)


def assert_really_playing(page, label):
    """Mode is video, the element has a real source, enough data, is not paused and time advances."""
    wait_playing(page, 20000)
    s = page.evaluate("""() => { const bg = document.querySelector('[data-testid="home-ambient-bg"]'); const v = bg.querySelector('video');
      return {mode: bg.dataset.ambientMode, src: v.currentSrc, readyState: v.readyState, paused: v.paused, t: v.currentTime}; }""")
    assert s['mode'] == 'video' and s['src'].endswith(VIDEO) and s['readyState'] >= 3 and not s['paused'], (label, s)
    page.wait_for_timeout(2500)
    t2 = state(page)['t']
    assert t2 != s['t'] and not state(page)['paused'], (label, 'currentTime did not advance', s, t2)
    s['tAfter2_5s'] = t2
    return s


def open_home(page):
    page.goto(URL + '/?steleQA=1')  # exposes the existing stele QA hook for interaction/FPS checks
    expect(page.locator(BG)).to_have_count(1, timeout=20000)
    page.wait_for_function("() => document.querySelector('section canvas')", timeout=20000)


def stele(page, expr='api.inspect()'):
    return page.evaluate("""(expr) => { const c = document.querySelector('section canvas');
      const api = window.__steleQA && window.__steleQA.get(c); return api ? eval(expr) : null; }""", expr)


def nav(page, label):
    page.locator('header').first.get_by_role('button', name=label).click()
    page.wait_for_timeout(1500)


def run_ci():
    """Short check for CI. Poster fallback is recorded separately from real playback."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=CHANNEL, headless=True, args=['--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'])
        context = new_context(browser)
        for path, mime in ((VIDEO, 'video/mp4'), (POSTER, 'image/webp')):
            response = context.request.get(URL + path)
            assert response.status == 200, (path, response.status)
            assert response.headers.get('content-type', '').startswith(mime), (path, response.headers.get('content-type'))
            results[path] = {'status': response.status, 'type': response.headers.get('content-type'), 'bytes': len(response.body())}
        page = context.new_page()
        problems = watch(page)
        page.goto(URL + '/?steleQA=1', wait_until='domcontentloaded')
        expect(page.locator(BG)).to_have_count(1, timeout=20000)
        page.wait_for_function("() => { const canvas = document.querySelector('section canvas'); return canvas && canvas.width > 40; }", timeout=20000)
        codec = page.evaluate("""() => document.createElement('video').canPlayType('video/mp4; codecs="avc1.4D401F"')""")
        results['codec'] = codec
        if not codec:
            expect(page.locator(BG)).to_have_attribute('data-ambient-mode', 'poster')
            expect(page.locator(BG)).to_have_attribute('data-ambient-reason', 'unsupported')
            results['playbackVerified'] = False
            results['mode'] = 'poster'
        else:
            played = assert_really_playing(page, 'ci')
            results['playbackVerified'] = True
            results['mode'] = 'video'
            results['playback'] = {'readyState': played['readyState'], 'time': played['t']}
        expect(page.get_by_role('heading', name='墨韵智考')).to_be_visible()
        assert state(page)['pointer'] == 'none'
        assert not problems, problems
        context.close()
        reduced = new_context(browser, viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        reduced_page = reduced.new_page()
        reduced_page.goto(URL + '/', wait_until='domcontentloaded')
        expect(reduced_page.locator(BG)).to_have_attribute('data-ambient-reason', 'reduced-motion', timeout=20000)
        assert reduced_page.locator(BG + ' video').count() == 0
        results['reducedMotion'] = 'poster only'
        reduced.close()
        browser.close()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print('Home ambient CI media check passed. playbackVerified is false when this browser only shows the poster.')


if args.ci:
    run_ci()
    raise SystemExit(0)

with sync_playwright() as p:
    browser = p.chromium.launch(channel=CHANNEL, headless=True, args=['--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'])

    # 1. Assets: status and MIME type.
    ctx = new_context(browser)
    for path, mime in ((VIDEO, 'video/mp4'), (POSTER, 'image/webp')):
        r = ctx.request.get(URL + path)
        assert r.status == 200, (path, r.status)
        assert r.headers.get('content-type', '').startswith(mime), (path, r.headers.get('content-type'))
        results[path] = {'status': r.status, 'type': r.headers.get('content-type'), 'bytes': len(r.body())}
    ctx.close()

    # 2. Desktop autoplay, loop wrap, hidden tab, scroll out of view, route change.
    ctx = new_context(browser, viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()
    problems = watch(page)
    video_requests = []
    page.on('request', lambda r: VIDEO in r.url and video_requests.append(r.url))
    open_home(page)
    codec = page.evaluate("() => document.createElement('video').canPlayType('video/mp4; codecs=\"avc1.4D401F\"')")
    results['codec'] = codec
    if not codec:
        expect(page.locator(BG)).to_have_attribute('data-ambient-mode', 'poster')
        print('Browser has no H.264: poster fallback verified; use RUBBINGMIND_BROWSER_CHANNEL=msedge for playback checks.')
    else:
        results['preview-strict'] = assert_really_playing(page, 'preview')
        s = state(page)
        assert s['muted'] and s['loop'] and s['pointer'] == 'none', s
        results['autoplay'] = s
        # Loop: currentTime must wrap back past 0 after the ~10.04 s clip.
        page.evaluate("""() => { const v = document.querySelector('[data-testid="home-ambient-bg"] video');
          window.__ambientWrap = {max: 0, wrapped: false, wrapAt: null};
          const tick = () => { const t = v.currentTime; const w = window.__ambientWrap;
            if (t + 1 < w.max && !w.wrapped) { w.wrapped = true; w.wrapAt = performance.now(); }
            w.max = Math.max(w.max, t); requestAnimationFrame(tick); }; tick(); }""")
        page.wait_for_function('() => window.__ambientWrap.wrapped', timeout=16000)
        page.wait_for_timeout(800)
        s = state(page)
        assert not s['paused'], s
        results['loop'] = {'maxTimeBeforeWrap': page.evaluate('window.__ambientWrap.max'), 'afterWrap': s['t'], 'duration': s['duration']}
        hero_check(page, 1440, 900)
        shot(page, 'video-playing.png')

        # Hidden tab (simulated visibilityState) -> paused; visible -> playing again.
        page.evaluate("""() => { Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'hidden'});
          document.dispatchEvent(new Event('visibilitychange')); }""")
        page.wait_for_timeout(400)
        assert state(page)['paused'], 'video should pause while the document is hidden'
        page.evaluate("""() => { Object.defineProperty(document, 'visibilityState', {configurable: true, get: () => 'visible'});
          document.dispatchEvent(new Event('visibilitychange')); }""")
        wait_playing(page, 5000)
        results['hidden'] = 'paused when hidden, resumed when visible'

        # Scroll hero out of view -> paused; back -> playing.
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(800)
        assert state(page)['paused'], 'video should pause when the hero is out of view'
        page.evaluate('window.scrollTo(0, 0)')
        wait_playing(page, 5000)
        results['offscreen'] = 'paused off-screen, resumed in view'

        # 3D stele still interactive with the video behind it.
        canvas = page.locator('section canvas').first
        page.get_by_role('button', name='正面', exact=True).click()
        page.wait_for_timeout(1800)
        before = stele(page)['position']
        cb = canvas.bounding_box()
        page.mouse.move(cb['x'] + cb['width'] / 2, cb['y'] + cb['height'] / 2)
        page.mouse.down(); page.mouse.move(cb['x'] + cb['width'] / 2 + 120, cb['y'] + cb['height'] / 2 + 20, steps=8); page.mouse.up()
        page.wait_for_timeout(600)
        rotated = stele(page)['position']
        assert rotated != before, 'drag should rotate the stele'
        page.mouse.wheel(0, -400)
        page.wait_for_timeout(800)
        zoomed = stele(page)['position']
        assert zoomed != rotated, 'wheel should zoom the stele'
        page.get_by_role('button', name='俯视', exact=True).click()
        page.wait_for_timeout(1800)
        assert stele(page)['position'] != zoomed, 'view preset should move the camera'
        page.get_by_title('全屏沉浸式展陈').click()
        expect(page.locator('[data-stele-fullscreen]')).to_be_visible()
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)
        if page.locator('[data-stele-fullscreen]').count():
            page.locator('[data-stele-fullscreen]').get_by_title(re.compile('退出|关闭')).first.click()
        expect(page.locator('[data-stele-fullscreen]')).to_have_count(0)
        results['stele'] = 'rotate, zoom, preset, fullscreen open/close OK'

        # FPS of the stele render loop with the video playing.
        page.get_by_role('button', name='透视', exact=True).click()
        page.wait_for_timeout(3000)
        results['steleFpsWithVideo'] = round(stele(page)['fps'] or 0, 1)
        results['gpu'] = stele(page)['gpu']

        # Other pages: no ambient background, no video element; returning home replays it.
        for label in ['贞石典藏馆', '智考工作台', '时空图谱中心', '算法评测报告']:
            nav(page, label)
            assert page.locator(BG).count() == 0 and page.locator('main video').count() == 0, f'video present on {label}'
        requests_before = len(video_requests)
        nav(page, '首页门户')
        wait_playing(page)
        results['routes'] = f'absent on 4 other pages, replays on return home ({len(video_requests)} video requests total, {requests_before} before return)'
    assert not problems, problems
    ctx.close()

    # 3. Screenshots / layout at several sizes.
    for w, h, name in ((1920, 1080, 'desktop-1920.png'), (1600, 900, 'desktop-1600.png'), (1440, 900, 'desktop-1440.png'),
                       (1366, 768, 'desktop-1366.png'), (1024, 768, 'tablet.png'), (390, 844, 'mobile.png'), (375, 812, 'mobile-375.png')):
        ctx = new_context(browser, viewport={'width': w, 'height': h})
        page = ctx.new_page()
        problems = watch(page)
        open_home(page)
        if codec:
            # The video plays on every screen size, including tablet and mobile.
            wait_playing(page)
            page.wait_for_timeout(3000)
        else:
            expect(page.locator(BG)).to_have_attribute('data-ambient-mode', 'poster')
            page.wait_for_timeout(2500)
        info = hero_check(page, w, h)
        # The first screen is filled by the hero (viewport minus the 68px header).
        assert info['hero'][3] >= h - 68 - 1.5, (name, info['hero'])
        shot(page, name)
        if codec and w == 1920:
            # Three frames of the same playback so the motion is visible across stills.
            page.evaluate("() => { const v = document.querySelector('[data-testid=\"home-ambient-bg\"] video'); v.currentTime = 0; }")
            for second in (1, 4, 7):
                page.wait_for_function('(s) => { const v = document.querySelector(\'[data-testid="home-ambient-bg"] video\'); return v && v.currentTime >= s && v.currentTime < s + 0.5; }',
                                       arg=second, timeout=15000, polling=50)
                shot(page, f'video-t{second}.png')
                results[f'video-t{second}.png'] = round(page.evaluate("() => document.querySelector('[data-testid=\"home-ambient-bg\"] video').currentTime"), 2)
        results[name] = {'mode': state(page)['mode'], 'reason': state(page)['reason'], 'hero': info['hero']}
        assert not problems, (name, problems)
        ctx.close()

    # 4. Reduced motion: poster only, no <video>, no video download.
    ctx = new_context(browser, viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    page = ctx.new_page()
    problems = watch(page)
    reqs = []
    page.on('request', lambda r: VIDEO in r.url and reqs.append(r.url))
    open_home(page)
    expect(page.locator(BG)).to_have_attribute('data-ambient-reason', 'reduced-motion')
    page.wait_for_timeout(3000)
    assert page.locator(BG + ' video').count() == 0 and not reqs, reqs
    hero_check(page, 1440, 900)
    results['steleFpsPosterOnly'] = round(stele(page)['fps'] or 0, 1)
    shot(page, 'reduced-motion.png')
    assert not problems, problems
    results['reducedMotion'] = 'poster only, no video element, no video request'
    ctx.close()

    # 5. Vite dev server (React.StrictMode double-invokes effects): the video must still play and loop.
    if DEV_URL and codec:
        ctx = new_context(browser, viewport={'width': 1920, 'height': 1080})
        page = ctx.new_page()
        problems = watch(page)
        page.goto(DEV_URL + '/')
        expect(page.locator(BG)).to_have_count(1, timeout=30000)
        dev = assert_really_playing(page, 'dev')
        page.evaluate("""() => { const v = document.querySelector('[data-testid="home-ambient-bg"] video');
          window.__ambientWrap = {max: 0, wrapped: false};
          const tick = () => { const t = v.currentTime; const w = window.__ambientWrap;
            if (t + 1 < w.max) w.wrapped = true; w.max = Math.max(w.max, t); requestAnimationFrame(tick); }; tick(); }""")
        page.wait_for_function('() => window.__ambientWrap.wrapped', timeout=16000)
        page.wait_for_timeout(500)
        assert not state(page)['paused']
        dev['wrapped'] = True
        dev['maxTimeBeforeWrap'] = page.evaluate('window.__ambientWrap.max')
        page.evaluate('window.scrollTo(0, 0)')
        shot(page, 'dev-motion-a.png')
        page.wait_for_timeout(3000)
        shot(page, 'dev-motion-b.png')
        results['dev-strictmode'] = dev
        assert not [p for p in problems if 'ERR_' not in p], problems
        ctx.close()
    browser.close()

print(json.dumps(results, ensure_ascii=False, indent=2))
print('Home ambient video browser regression passed.')
