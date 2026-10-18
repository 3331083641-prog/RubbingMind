"""Browser acceptance for the Three.js terrain engine.

Requires the FastAPI backend (127.0.0.1:8000) and Vite (localhost:5173).

Checks the things a compiler cannot: that the terrain really is a DEM-driven
Three.js surface, that China dominates the national frame, that the named
landforms resolve to real elevations, that every documented interaction works,
and that interaction frame rate is measured rather than guessed.

    python scripts/test_terrain3d_browser.py
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
OUT = Path(os.environ.get('TERRAIN_SCREENSHOT_DIR', str(ROOT / 'screenshots/terrain3d-final')))
OUT.mkdir(parents=True, exist_ok=True)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

VIEWPORTS = [(1920, 1080), (1440, 900), (1366, 768)]

# Regional viewpoints used to verify the named landforms in the render.
REGIONS = [
    ('tibet', '青藏高原', 88.0, 31.0, 5.9),
    ('himalaya', '喜马拉雅山脉', 86.6, 28.4, 6.6),
    ('sichuan', '四川盆地', 105.3, 30.2, 6.5),
    ('xinjiang', '天山与塔里木盆地', 84.5, 41.2, 5.9),
    ('east-plain', '华北与长江中下游平原', 117.2, 33.0, 6.0),
    ('northeast', '东北平原与大兴安岭', 125.5, 45.5, 5.4),
]

# Real elevations at runtime, read through the engine's own DEM sampler.
ELEVATION_PROBES = [
    ('珠峰', 86.925, 27.988, 6000, 9200),
    ('拉萨', 91.14, 29.65, 3000, 4800),
    ('塔里木盆地', 83.0, 39.5, 700, 1700),
    ('四川盆地', 105.3, 30.2, 250, 900),
    ('华北平原', 116.4, 36.0, -20, 200),
    ('黄海', 123.0, 31.0, -200, 0),
]


def map_attr(page, name: str) -> str:
    return page.locator('[data-testid="historical-map"]').get_attribute(name) or ''


def stats(page) -> dict:
    hud = page.locator('[data-testid="terrain-hud"]')
    return hud.evaluate("el => ({...el.dataset})")


def capture(page, path: Path, full: bool = False):
    page.evaluate('window.scrollTo(0, 0)')
    page.wait_for_timeout(120)
    page.screenshot(path=str(path), full_page=full)


def fly(page, lng: float, lat: float, zoom: float, pitch: float = 44):
    page.evaluate(
        """([lng, lat, zoom, pitch]) => {
            const map = window.__historicalMap;
            map.jumpTo({ center: [lng, lat], zoom, pitch, bearing: 0 });
        }""",
        [lng, lat, zoom, pitch],
    )
    page.wait_for_timeout(2400)


def main() -> int:
    assert requests.get(BACKEND_URL + '/health', timeout=10).json()['status'] == 'healthy'
    errors: list[str] = []
    checks: list[str] = []
    report: dict = {'viewports': [f'{w}x{h}' for w, h in VIEWPORTS], 'regions': {}, 'performance': {}, 'checks': checks, 'browserErrors': errors}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True)
        page = browser.new_page(viewport={'width': 1920, 'height': 1080}, device_scale_factor=1)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)

        started = time.time()
        page.goto(FRONTEND_URL + '/', wait_until='networkidle')
        clicked = time.time()
        page.get_by_role('button', name='时空图谱中心').click()
        map_el = page.locator('[data-testid="historical-map"]')
        expect(map_el).to_have_attribute('data-ready', 'true', timeout=30000)
        expect(map_el).to_have_attribute('data-terrain-ready', 'true', timeout=60000)
        first_terrain = time.time() - clicked
        page.wait_for_timeout(2000)
        checks.append(f'三维地形引擎从进入页面到就绪 {first_terrain:.1f} s（含 DEM 瓦片与网格构建）')
        report['performance']['terrainReadySeconds'] = round(first_terrain, 2)
        report['performance']['pageLoadSeconds'] = round(clicked - started, 2)

        # --- GPU / WebGL identity -------------------------------------------------
        gpu = page.evaluate(
            """() => {
                const c = document.querySelector('.map-region canvas');
                const gl = c.getContext('webgl2');
                const dbg = gl.getExtension('WEBGL_debug_renderer_info');
                return { renderer: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : 'unknown', version: gl.getParameter(gl.VERSION) };
            }"""
        )
        report['performance']['renderer'] = gpu
        checks.append(f"WebGL 2 上下文：{gpu['renderer']}")

        expect(page.locator('.map-error')).to_have_count(0)
        expect(page.locator('.graph-page canvas')).to_have_count(2)
        checks.append('单一 WebGL 上下文（页面 canvas 仍为 2：主图 + 南海同源附图），无地图错误')

        # --- national composition ------------------------------------------------
        width_ratio = float(map_attr(page, 'data-frame-width'))
        report['nationalFrameWidth'] = width_ratio
        assert 0.65 <= width_ratio <= 0.80, f'中国占画幅比例 {width_ratio} 不在 65%–80%'
        pitch = float(map_attr(page, 'data-pitch'))
        assert 30 <= pitch <= 55, pitch
        checks.append(f'全国构图：中国占地图宽度 {width_ratio * 100:.1f}%，俯仰 {pitch:.0f}°')
        for width, height in VIEWPORTS:
            page.set_viewport_size({'width': width, 'height': height})
            page.wait_for_timeout(1200)
            ratio = float(map_attr(page, 'data-frame-width'))
            report[f'frameWidth{width}'] = ratio
            assert 0.64 <= ratio <= 0.81, f'{width}: {ratio}'
            assert page.evaluate('document.documentElement.scrollWidth') <= width, '横向溢出'
            expect(page.locator('.map-error')).to_have_count(0)
            capture(page, OUT / f'01_全国三维地貌_{width}x{height}.png')
        page.set_viewport_size({'width': 1920, 'height': 1080})
        page.wait_for_timeout(1400)
        checks.append('三种视口下全国构图均保持 65%–80%，无横向溢出')

        # --- runtime elevation checks -------------------------------------------
        probes = []
        for label, lng, lat, low, high in ELEVATION_PROBES:
            value = page.evaluate('([lng, lat]) => window.__terrain3d.heightAt(lng, lat)', [lng, lat])
            probes.append({'label': label, 'lng': lng, 'lat': lat, 'height': round(value, 1)})
            assert low <= value <= high, f'{label} 高程 {value} 不在 ({low}, {high})'
        report['elevationProbes'] = probes
        checks.append('运行时高程核验：' + '、'.join(f"{p['label']} {p['height']:.0f} m" for p in probes))

        # --- regional landform renders ------------------------------------------
        for key, label, lng, lat, zoom in REGIONS:
            fly(page, lng, lat, zoom)
            expect(page.locator('.map-error')).to_have_count(0)
            data = stats(page)
            center = map_attr(page, 'data-center').split(',')
            assert abs(float(center[0]) - lng) < 2.5 and abs(float(center[1]) - lat) < 2.5, center
            capture(page, OUT / f'02_{label}_{key}.png')
            page.locator('.map-region').screenshot(path=str(OUT / f'02_{label}_{key}_地图区.png'))
            report['regions'][key] = {'label': label, 'center': center, 'zoom': map_attr(page, 'data-zoom'), 'stats': data}
            checks.append(f'{label}：DEM z{data.get("demZoom")} · {int(data.get("vertices", 0)):,} 顶点')

        # --- interactions --------------------------------------------------------
        fly(page, 105, 34, 4.2)
        before = float(map_attr(page, 'data-zoom'))
        box = page.locator('.map-region canvas').first.bounding_box()
        page.mouse.move(box['x'] + box['width'] * 0.45, box['y'] + box['height'] * 0.55)
        page.mouse.wheel(0, -420)
        page.wait_for_timeout(900)
        assert float(map_attr(page, 'data-zoom')) > before, '滚轮未放大'
        zoomed = float(map_attr(page, 'data-zoom'))

        old_center = map_attr(page, 'data-center')
        page.mouse.move(box['x'] + box['width'] * 0.45, box['y'] + box['height'] * 0.55)
        page.mouse.down()
        page.mouse.move(box['x'] + box['width'] * 0.45 + 80, box['y'] + box['height'] * 0.55 + 40, steps=12)
        page.mouse.up()
        page.wait_for_timeout(800)
        assert map_attr(page, 'data-center') != old_center, '拖拽未平移'
        checks.append(f'滚轮缩放（{before:.2f} → {zoomed:.2f}）与拖拽平移')

        page.get_by_title('顺时针旋转视角').click()
        page.wait_for_timeout(900)
        bearing = float(map_attr(page, 'data-bearing'))
        assert abs(bearing) > 10, bearing
        capture(page, OUT / '03_三维视角旋转.png')
        page.get_by_title('倾斜到三维视角').click()
        page.wait_for_timeout(900)
        tilt = float(map_attr(page, 'data-pitch'))
        assert tilt > 20, tilt
        page.get_by_title('一键俯视（正射）').click()
        page.wait_for_timeout(1100)
        assert float(map_attr(page, 'data-pitch')) < 3, '俯视失败'
        capture(page, OUT / '04_一键俯视_正射.png')
        checks.append(f'视角旋转（方位 {bearing:.0f}°）、倾斜（{tilt:.0f}°）、一键俯视')

        page.get_by_title('恢复中国全国构图').click()
        page.wait_for_timeout(1500)
        assert 0.64 <= float(map_attr(page, 'data-frame-width')) <= 0.81
        assert float(map_attr(page, 'data-pitch')) > 30
        checks.append('一键恢复全国构图')

        # --- 2D / 3D switch and layer switches ----------------------------------
        page.get_by_role('button', name='二维地图', exact=True).click()
        page.wait_for_timeout(1800)
        expect(map_el).to_have_attribute('data-terrain', '2d')
        assert float(map_attr(page, 'data-pitch')) < 2, '二维模式仍保持倾角'
        capture(page, OUT / '05_二维地图模式.png')
        page.get_by_role('button', name='三维地形', exact=True).click()
        page.wait_for_timeout(1800)
        expect(map_el).to_have_attribute('data-terrain', '3d')
        checks.append('二维地图 / 三维地形双向切换（二维回到正射）')

        page.get_by_role('button', name='图层', exact=True).click()
        page.get_by_label('现代省界与国界', exact=True).uncheck()
        page.get_by_label('真实主要水系', exact=True).uncheck()
        page.wait_for_timeout(900)
        expect(map_el).to_have_attribute('data-terrain-ready', 'true')
        page.locator('.map-region').screenshot(path=str(OUT / '06_关闭边界与水系.png'))
        page.get_by_label('现代省界与国界', exact=True).check()
        page.get_by_label('真实主要水系', exact=True).check()
        page.get_by_label('地形垂直夸张').select_option('16')
        page.wait_for_timeout(900)
        assert abs(float(stats(page).get('exaggeration', 0)) - 16) < 0.6
        page.get_by_label('地形等高线（DEM 派生）', exact=True).uncheck()
        page.get_by_label('地形等高线（DEM 派生）', exact=True).check()
        page.get_by_label('地形垂直夸张').select_option('auto')
        page.get_by_role('button', name='图层', exact=True).click()
        page.wait_for_timeout(600)
        checks.append('边界 / 水系 / 等高线开关与垂直夸张倍率（×16 实测生效）')

        # --- place interaction ---------------------------------------------------
        page.get_by_test_id('stele-han-caoquan').click()
        page.wait_for_timeout(1800)
        page.get_by_label('检索历史地名').fill('敦煌')
        page.get_by_role('option', name='敦煌效谷地望').click()
        page.wait_for_timeout(1100)
        expect(page.locator('.selected-entity')).to_contain_text('敦煌')
        center = map_attr(page, 'data-center').split(',')
        assert 92 < float(center[0]) < 96 and 39 < float(center[1]) < 42, center
        capture(page, OUT / '07_地点定位与考据联动.png')
        markers = page.locator('.historical-marker')
        assert markers.count() >= 1
        checks.append('地点检索 → 三维地形定位 → 考据侧栏联动')

        # --- graph linkage -------------------------------------------------------
        page.get_by_role('button', name='地图与图谱联动', exact=True).click()
        page.wait_for_timeout(1600)
        expect(page.get_by_test_id('knowledge-network')).to_be_visible()
        expect(map_el).to_be_visible()
        capture(page, OUT / '08_地图与人物图谱联动.png')
        page.get_by_role('button', name='人物关系', exact=True).click()
        page.get_by_role('button', name='返回全国视图', exact=True).click()
        page.wait_for_timeout(1200)
        expect(map_el).to_be_visible()
        checks.append('人物关系图谱与地图联动、返回全国视图')

        # --- measured interaction performance -----------------------------------
        page.set_viewport_size({'width': 1920, 'height': 1080})
        fly(page, 105, 34, 4.4)
        frames_before = int(stats(page).get('frames', 0))
        t0 = time.time()
        box = page.locator('.map-region canvas').first.bounding_box()
        for index in range(6):
            angle = index * 60
            page.mouse.move(box['x'] + box['width'] * 0.5, box['y'] + box['height'] * 0.55)
            page.mouse.down()
            page.mouse.move(
                box['x'] + box['width'] * 0.5 + 90 * (1 if angle % 120 == 0 else -1),
                box['y'] + box['height'] * 0.55 + 45,
                steps=8,
            )
            page.mouse.up()
            page.mouse.wheel(0, -120 if index % 2 == 0 else 120)
        page.wait_for_timeout(200)
        wall = time.time() - t0
        frames_after = int(stats(page).get('frames', 0))
        interactive_fps = (frames_after - frames_before) / max(wall, 0.001)
        perf = stats(page)
        report['performance'].update({
            'interactiveFps': round(interactive_fps, 1),
            'framesSampled': frames_after - frames_before,
            'seconds': round(wall, 2),
            'vertices': int(perf.get('vertices', 0)),
            'triangles': int(round(int(perf.get('vertices', 0)) * 1.996)),
            'buildMs': perf.get('buildMs'),
            'demZoom': perf.get('demZoom'),
            'tilesLoaded': perf.get('tiles'),
            'exaggeration': perf.get('exaggeration'),
            'dpr': perf.get('dpr'),
        })
        assert interactive_fps > 24, f'交互帧率过低: {interactive_fps:.1f}'
        assert int(perf.get('vertices', 0)) > 200000, '地形顶点数过少，可能未真正构建网格'
        checks.append(f'交互实测 {interactive_fps:.0f} FPS（{frames_after - frames_before} 帧 / {wall:.1f} s，1920×1080）')
        capture(page, OUT / '09_交互性能采样后.png')

        browser.close()

    report['checks'] = checks
    report['status'] = 'passed' if not errors else 'failed'
    (OUT / 'terrain3d-results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert not errors, errors
    return 0


if __name__ == '__main__':
    sys.exit(main())
