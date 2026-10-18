"""Browser acceptance for the V2.2 terrain visual refinement.

Focus: province borders must be clearly readable while the national border stays
the strongest line; label collision; independent border layers; 2D parity.

Requires the FastAPI backend (127.0.0.1:8000) and Vite (localhost:5173).

    python scripts/test_terrain3d_v22_browser.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
BACKEND_URL = os.environ.get('GRAPH_BACKEND_URL', 'http://127.0.0.1:8000')
FRONTEND_URL = os.environ.get('GRAPH_FRONTEND_URL', 'http://localhost:5173')
OUT = Path(os.environ.get('V22_SCREENSHOT_DIR', str(ROOT / 'screenshots/terrain3d-v22')))
OUT.mkdir(parents=True, exist_ok=True)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# name, longitude, latitude, zoom, pitch
VIEWS = [
    ('04_青藏高原省界特写', 88.0, 31.0, 5.9, 44),
    ('05_四川盆地周边省界特写', 105.2, 30.2, 6.3, 44),
    ('06_华北相邻省份特写', 114.6, 37.6, 6.2, 44),
    ('07_华东密集省份特写', 118.6, 31.4, 6.6, 44),
]

PROBES = [
    ('珠峰所在 z5 网格', 86.925, 27.988, 6000, 7600),
    ('拉萨', 91.14, 29.65, 3000, 4800),
    ('塔里木盆地', 83.0, 39.5, 700, 1700),
    ('四川盆地', 105.3, 30.2, 250, 900),
    ('华北平原', 116.4, 36.0, -20, 200),
]


def fly(page, lng: float, lat: float, zoom: float, pitch: float = 44):
    page.evaluate(
        "([lng,lat,zoom,pitch]) => window.__historicalMap.jumpTo({center:[lng,lat], zoom, pitch, bearing:0})",
        [lng, lat, zoom, pitch],
    )
    page.wait_for_timeout(2200)


def attr(page, name: str) -> str:
    return page.locator('[data-testid="historical-map"]').get_attribute(name) or ''


def hud(page) -> dict:
    return page.locator('[data-testid="terrain-hud"]').evaluate('el => ({...el.dataset})')


def shot(page, name: str, target: str = 'map'):
    locator = page.locator('.map-region') if target == 'map' else page
    locator.screenshot(path=str(OUT / f'{name}.png'))


def main() -> int:
    assert requests.get(BACKEND_URL + '/health', timeout=10).json()['status'] == 'healthy'
    errors: list[str] = []
    checks: list[str] = []
    report: dict = {'checks': checks, 'browserErrors': errors}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=1)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'ERR_CONNECTION_RESET' not in m.text else None)

        page.goto(FRONTEND_URL + '/', wait_until='networkidle')
        page.get_by_role('button', name='时空图谱中心').click()
        map_el = page.locator('[data-testid="historical-map"]')
        expect(map_el).to_have_attribute('data-terrain-ready', 'true', timeout=60000)
        page.wait_for_timeout(2400)

        # --- layer inventory -----------------------------------------------------
        page.wait_for_selector('[data-testid="terrain-hud"]', state='attached', timeout=30000)
        groups = (hud(page).get('vectorGroups') or '').split(',')
        for required in ('province', 'national', 'national-halo', 'national-casing', 'rivers'):
            assert required in groups, groups
        assert 'province-casing' not in groups, '省界不应再有暗色衬底层'
        checks.append('省际边界为独立图层（无暗色衬底），国界仍为三层描边')

        ratio = float(attr(page, 'data-frame-width'))
        assert 0.64 <= ratio <= 0.81, ratio
        report['frameWidth'] = ratio
        shot(page, '01_全国三维地图优化后', 'page')
        checks.append(f'全国构图中国占画幅 {ratio * 100:.1f}%')

        # --- border hierarchy at the national view -------------------------------
        fly(page, 104.5, 35.5, 2.9, 44)
        shot(page, '03_国界与省界整体对比', 'map')
        checks.append('国界与省界整体对比截图')

        # --- regional close-ups --------------------------------------------------
        for name, lng, lat, zoom, pitch in VIEWS:
            fly(page, lng, lat, zoom, pitch)
            expect(page.locator('.map-error')).to_have_count(0)
            shot(page, name, 'map')
            checks.append(f'{name} 截图（缩放 {zoom}）')

        # --- tilt view -----------------------------------------------------------
        fly(page, 103.0, 34.5, 4.3, 55)
        shot(page, '08_三维倾斜视角', 'map')
        assert float(attr(page, 'data-pitch')) > 50
        checks.append('倾斜 55° 视角截图')

        # --- independent layer switches -----------------------------------------
        page.get_by_role('button', name='图层', exact=True).click()
        fly(page, 104.5, 35.5, 2.9, 44)
        page.get_by_label('省级行政边界', exact=True).uncheck()
        page.wait_for_timeout(900)
        shot(page, '09_关闭省界后的地形对比', 'map')
        groups = (hud(page).get('vectorGroups') or '').split(',')
        assert 'province' in groups  # geometry stays built, only visibility changes
        checks.append('关闭省界：地形与国界保持，省界单独隐藏')

        page.get_by_label('省级行政边界', exact=True).check()
        page.get_by_label('中国国界', exact=True).uncheck()
        page.wait_for_timeout(900)
        shot(page, '10_关闭国界后的图层对比', 'map')
        checks.append('关闭国界：省界仍显示，证明两层互不影响')

        page.get_by_label('中国国界', exact=True).check()
        page.wait_for_timeout(700)
        page.get_by_role('button', name='图层', exact=True).click()
        checks.append('国界 / 省界开关互不干扰，且不误关其他图层')

        # --- 2D parity -----------------------------------------------------------
        fly(page, 104.5, 35.5, 2.9, 0)
        page.get_by_role('button', name='二维地图', exact=True).click()
        page.wait_for_timeout(2000)
        expect(map_el).to_have_attribute('data-terrain', '2d')
        shot(page, '02_全国二维地图优化后', 'page')
        groups = (hud(page).get('vectorGroups') or '').split(',')
        assert 'province' in groups and 'national' in groups
        checks.append('二维模式沿用同一边界层级（省界可见、国界仍最强）')
        page.get_by_role('button', name='三维地形', exact=True).click()
        page.wait_for_timeout(1800)

        # --- runtime elevation probes -------------------------------------------
        probes = []
        for label, lng, lat, low, high in PROBES:
            value = page.evaluate('([lng, lat]) => window.__terrain3d.heightAt(lng, lat)', [lng, lat])
            probes.append({'label': label, 'lng': lng, 'lat': lat, 'height': round(value, 1)})
            assert low <= value <= high, f'{label} {value}'
        report['elevationProbes'] = probes
        checks.append('运行时高程核验：' + '、'.join(f"{p['label']} {p['height']:.0f} m" for p in probes))

        # --- label collision -----------------------------------------------------
        fly(page, 104.5, 35.5, 2.9, 44)
        page.wait_for_timeout(1200)
        labels = page.evaluate(
            """() => {
              const out = [];
              document.querySelectorAll('.province-label').forEach(el => {
                if (el.style.visibility === 'hidden') return;
                const r = el.getBoundingClientRect();
                out.push([el.textContent, Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]);
              });
              return out;
            }"""
        )
        overlaps = 0
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                a, b = labels[i], labels[j]
                if a[1] < b[1] + b[3] and a[1] + a[3] > b[1] and a[2] < b[2] + b[4] and a[2] + a[4] > b[2]:
                    overlaps += 1
        report['visibleProvinceLabels'] = len(labels)
        report['labelOverlaps'] = overlaps
        assert overlaps == 0, f'仍有 {overlaps} 组省名重叠'
        assert 20 <= len(labels) <= 34, len(labels)
        checks.append(f'省名避让：全国视图显示 {len(labels)}/34 个，重叠 0 组')

        # --- performance ---------------------------------------------------------
        fly(page, 105, 34, 4.4, 44)
        before = int(hud(page).get('frames') or 0)
        started = time.time()
        box = page.locator('.map-region canvas').first.bounding_box()
        for index in range(6):
            page.mouse.move(box['x'] + box['width'] * 0.5, box['y'] + box['height'] * 0.55)
            page.mouse.down()
            page.mouse.move(box['x'] + box['width'] * 0.5 + (90 if index % 2 == 0 else -90), box['y'] + box['height'] * 0.55 + 45, steps=8)
            page.mouse.up()
            page.mouse.wheel(0, -120 if index % 2 == 0 else 120)
        page.wait_for_timeout(200)
        elapsed = time.time() - started
        after = int(hud(page).get('frames') or 0)
        fps = (after - before) / max(elapsed, 0.001)
        stats = hud(page)
        report['performance'] = {
            'interactiveFps': round(fps, 1),
            'frames': after - before,
            'seconds': round(elapsed, 2),
            'vertices': int(stats.get('vertices') or 0),
            'buildMs': stats.get('buildMs'),
            'drapedGroups': stats.get('vectorGroups'),
        }
        assert fps > 24, fps
        checks.append(f'交互实测 {fps:.0f} FPS（{after - before} 帧 / {elapsed:.1f} s）')

        browser.close()

    report['status'] = 'passed' if not errors else 'failed'
    (OUT / 'v22-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert not errors, errors
    return 0


if __name__ == '__main__':
    sys.exit(main())
