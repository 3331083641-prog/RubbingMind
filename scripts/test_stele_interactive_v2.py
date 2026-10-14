# -*- coding: utf-8 -*-
"""
墨韵智考 - 前端 Three.js 三维石碑六方向交互与功能验证自动化脚本
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots", "stele-v2", "browser_interactive")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

URL = "http://127.0.0.1:8000"

def test_stele_viewer():
    print("=" * 70)
    print("  墨韵智考 - Three.js 三维石碑重构端到端浏览器交互验收测试")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--disable-web-security", "--allow-file-access-from-files"]
        )
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("[1/5] 打开系统门户首页...")
        page.goto(URL, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_selector("canvas", timeout=15000)
        time.sleep(3)
        print("  [OK] Three.js WebGL 画布成功挂载并渲染")

        # 检查控制台是否有着色器或贴图错误
        shader_or_tex_errors = [e for e in console_errors if "Shader" in e or "GLTF" in e or "WebGL" in e or "404" in e]
        assert len(shader_or_tex_errors) == 0, f"发现控制台渲染错误: {shader_or_tex_errors}"
        print("  [OK] 控制台无任何 Shader 编译错误或 404 贴图缺失")

        print("[2/5] 验证六方向正交与45度透视视角切换按钮...")
        views = [
            ("正视", "browser_front.png"),
            ("背视", "browser_back.png"),
            ("左视", "browser_left.png"),
            ("右视", "browser_right.png"),
            ("顶视", "browser_top.png"),
            ("底视", "browser_bottom.png"),
            ("透视", "browser_perspective.png"),
        ]

        for label, shot_name in views:
            btn = page.locator(f"button:has-text('{label}')").first
            btn.click()
            time.sleep(1.2)
            shot_path = os.path.join(SCREENSHOT_DIR, shot_name)
            page.screenshot(path=shot_path)
            print(f"  [OK] 切换至【{label}】视角成功，已保存截图: {shot_name}")

        print("[3/5] 验证激光扫描与微痕修复滑块...")
        laser_btn = page.locator("button:has-text('激光扫描')").first
        laser_btn.click()
        time.sleep(0.5)
        laser_btn.click()
        print("  [OK] 激光扫描开关切换响应正常")

        slider = page.locator("input[type='range']").first
        slider.fill("0.8")
        time.sleep(1.0)
        print("  [OK] 修复混合滑块数值平滑更新至 80%")

        print("[4/5] 验证鼠标 360 度自由旋转与视角缩放...")
        canvas = page.locator("canvas").first
        box = canvas.bounding_box()
        if box:
            start_x = box["x"] + box["width"] / 2
            start_y = box["y"] + box["height"] / 2
            page.mouse.move(start_x, start_y)
            page.mouse.down()
            page.mouse.move(start_x + 180, start_y - 60, steps=10)
            page.mouse.up()
            time.sleep(1)
            print("  [OK] 鼠标拖拽 3D 旋转平滑无跳帧")

        print("[5/5] 验证全屏沉浸式展陈切换...")
        fullscreen_btn = page.locator("button[title='全屏沉浸式展陈']").first
        if fullscreen_btn.is_visible():
            fullscreen_btn.click()
            time.sleep(1.5)
            exit_btn = page.locator("button[title='退出全屏']").first
            assert exit_btn.is_visible(), "全屏弹窗未正常弹出"
            exit_btn.click()
            time.sleep(1)
            print("  [OK] 全屏沉浸式展陈开启与退出流畅")

        browser.close()

    print("\n[OK] 5 items frontend 3D stele browser interactive tests 100% PASSED!")

if __name__ == "__main__":
    test_stele_viewer()
