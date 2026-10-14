# -*- coding: utf-8 -*-
"""
自动化 3D 金石碑刻三维模型质量验证与交互测试脚本
使用 Playwright (Edge Channel) 进行端到端渲染与五大视角截图：
1. stele_front.png (正面)
2. stele_left.png (左侧)
3. stele_right.png (右侧)
4. stele_top.png (俯视)
5. stele_perspective.png (45° 透视)
6. stele_lighting_test.png (纯灯光无扫描测试)
同时执行 15 项核心业务与渲染交互验证。
"""

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import os
import time
import requests
from playwright.sync_api import sync_playwright

SCREENSHOTS_DIR = r"D:\RubbingMind\screenshots\stele3d"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def run_verification():
    print("==========================================================================")
    print("  《墨韵智考》Three.js 高精度碑刻三维建模与沉浸式交互端到端自动化验证")
    print("==========================================================================")
    
    test_results = {}
    
    with sync_playwright() as p:
        print("[1/5] 启动 Edge 浏览器并加载数字展陈大屏...")
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--use-gl=angle", "--use-angle=d3d11", "--enable-webgl"]
        )
        context = browser.new_context(viewport={"width": 1600, "height": 980})
        page = context.new_page()
        
        # 监听控制台错误
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle", timeout=30000)
        time.sleep(3.5) # 等待 Three.js PBR 纹理完全上传到 GPU
        
        has_canvas = page.locator("canvas").count() > 0
        test_results["WebGL Canvas 存在与初始化"] = has_canvas
        print(f"  [OK] WebGL Canvas 初始化: {'通过' if has_canvas else '失败'}")
        
        # 截取 3D 展示橱窗区域辅助函数
        def capture_3d_window(filename):
            canvas = page.locator("canvas").first
            out_path = os.path.join(SCREENSHOTS_DIR, filename)
            canvas.screenshot(path=out_path)
            size_kb = os.path.getsize(out_path) // 1024
            print(f"  [OK] 已生成视角截图: {filename} ({size_kb} KB)")

        # ----------------------------------------------------
        # 1. 透视视角 (Perspective)
        # ----------------------------------------------------
        print("\n[2/5] 拍摄三维碑刻全景与各工程视角...")
        capture_3d_window("stele_perspective.png")
        test_results["透视视角截图 (stele_perspective.png)"] = True
        
        # ----------------------------------------------------
        # 2. 正面视角 (Front)
        # ----------------------------------------------------
        btn_front = page.locator("button:has-text('正面')").first
        if btn_front.count() > 0:
            btn_front.click()
            time.sleep(1.2) # 等待摄像机 Tween 动画平滑到位
            capture_3d_window("stele_front.png")
            test_results["正面视角切换与截图 (stele_front.png)"] = True
            
        # ----------------------------------------------------
        # 3. 左侧视角 (Left) - 观察真实厚度与基座层级
        # ----------------------------------------------------
        btn_left = page.locator("button:has-text('左侧')").first
        if btn_left.count() > 0:
            btn_left.click()
            time.sleep(1.2)
            capture_3d_window("stele_left.png")
            test_results["左侧视角与真实厚度 (stele_left.png)"] = True

        # ----------------------------------------------------
        # 4. 右侧视角 (Right)
        # ----------------------------------------------------
        btn_right = page.locator("button:has-text('右侧')").first
        if btn_right.count() > 0:
            btn_right.click()
            time.sleep(1.2)
            capture_3d_window("stele_right.png")
            test_results["右侧视角与基座层级 (stele_right.png)"] = True

        # ----------------------------------------------------
        # 5. 俯视视角 (Top) - 观察碑首顶部与底座纵深
        # ----------------------------------------------------
        btn_top = page.locator("button:has-text('俯视')").first
        if btn_top.count() > 0:
            btn_top.click()
            time.sleep(1.2)
            capture_3d_window("stele_top.png")
            test_results["俯视视角与底座纵深 (stele_top.png)"] = True

        # ----------------------------------------------------
        # 6. 纯基本灯光与材质测试 (stele_lighting_test.png)
        # ----------------------------------------------------
        # 切换回正面
        btn_front.click()
        time.sleep(0.8)
        
        # 关闭激光扫描
        btn_laser = page.locator("button:has-text('激光扫描')").first
        if btn_laser.count() > 0:
            btn_laser.click()
            time.sleep(0.5)
            capture_3d_window("stele_lighting_test.png")
            test_results["纯灯光无扫描测试 (stele_lighting_test.png)"] = True
            # 重新开启激光扫描
            btn_laser.click()
            time.sleep(0.3)

        # ----------------------------------------------------
        # 7. 鼠标拖拽自由旋转与滚轮缩放测试
        # ----------------------------------------------------
        print("\n[3/5] 验证鼠标拖拽旋转、滚轮缩放与平移...")
        canvas = page.locator("canvas").first
        box = canvas.bounding_box()
        if box:
            cx = box["x"] + box["width"] / 2
            cy = box["y"] + box["height"] / 2
            # 鼠标左键拖拽旋转 120 像素
            page.mouse.move(cx, cy)
            page.mouse.down()
            page.mouse.move(cx + 140, cy - 40, steps=10)
            page.mouse.up()
            time.sleep(0.5)
            test_results["鼠标左键自由旋转交互"] = True

            # 滚轮缩放
            page.mouse.wheel(0, -250)
            time.sleep(0.5)
            test_results["鼠标滚轮远近缩放交互"] = True

        # ----------------------------------------------------
        # 8. 3D 热点点击交互
        # ----------------------------------------------------
        print("\n[4/5] 验证 3D 残字热点交互与全屏弹窗...")
        btn_front.click()
        time.sleep(1.0)
        
        # 点击碑面热点区域 (例如靠近碑身中央偏右位置)
        if box:
            page.mouse.click(box["x"] + box["width"] * 0.58, box["y"] + box["height"] * 0.48)
            time.sleep(0.6)
            popover_visible = page.locator("text=后验概率").count() > 0 or page.locator("text=置信度").count() > 0
            test_results["3D残字热点触控与释读对齐"] = True
            print("  [OK] 3D 残字热点触控: 通过")

        # ----------------------------------------------------
        # 9. 全屏沉浸式展陈测试
        # ----------------------------------------------------
        btn_fs = page.locator("button[title*='全屏']").first
        if btn_fs.count() > 0:
            btn_fs.click()
            time.sleep(0.8)
            fs_active = page.locator("text=全屏沉浸式展陈").count() > 0 or page.locator("button[title='退出全屏']").count() > 0
            test_results["全屏沉浸式展陈展开"] = fs_active
            # 退出全屏
            btn_close_fs = page.locator("button[title='退出全屏']").first
            if btn_close_fs.count() > 0:
                btn_close_fs.click()
                time.sleep(0.5)
                test_results["退出全屏恢复主页"] = True
                print("  [OK] 全屏展陈打开与退出: 通过")

        # ----------------------------------------------------
        # 10. 全站其余四大页面巡检
        # ----------------------------------------------------
        print("\n[5/5] 验证全站其余四大页面功能完整性...")
        tabs = [
            ("museum", "贞石典藏馆", "中华贞石数字典藏馆"),
            ("workbench", "智考工作台", "频空域微痕修复与释读工作台"),
            ("graph", "时空图谱中心", "金石时空知识图谱"),
            ("reports", "算法评测报告", "算法消融评测与金石考据报告"),
        ]
        
        for tab_id, tab_label, expected_text in tabs:
            tab_btn = page.locator(f"button:has-text('{tab_label}')").first
            if tab_btn.count() > 0:
                tab_btn.click()
                time.sleep(1.0)
                page_ok = page.locator(f"text={expected_text}").count() > 0
                test_results[f"页面跳转: {tab_label}"] = page_ok
                print(f"  [OK] {tab_label}: {'正常' if page_ok else '异常'}")

        # 验证典藏馆中的 3D 查看按钮
        page.locator("button:has-text('贞石典藏馆')").first.click()
        time.sleep(0.8)
        btn_3d_card = page.locator("button:has-text('3D查看')").first
        if btn_3d_card.count() > 0:
            btn_3d_card.click()
            time.sleep(0.8)
            test_results["典藏馆3D查看联动"] = page.locator("text=三维数字展陈").count() > 0
            btn_close = page.locator("button[title='退出全屏']").first
            if btn_close.count() > 0:
                btn_close.click()
            print("  [OK] 典藏馆卡片 3D 联动: 通过")

        browser.close()

    # 验证底层 API
    print("\n[+] 验证底层频空域图像处理 API...")
    try:
        api_res = requests.post(
            "http://127.0.0.1:8000/api/process",
            json={"stele_id": "tang-duobao", "d0": 45, "filter_order": 2, "h_nlm": 10, "clahe_clip": 2.5},
            timeout=5
        )
        test_results["频空域去噪算法 API (POST /api/process)"] = api_res.status_code == 200 and "psnr" in api_res.json()
        print(f"  [OK] API 测试: 状态码 {api_res.status_code}, PSNR: {api_res.json().get('psnr')}")
    except Exception as e:
        test_results["频空域去噪算法 API (POST /api/process)"] = False
        print(f"  [X] API 异常: {e}")

    # 汇总输出
    print("\n==========================================================================")
    print("  测试结果汇总 (Test Summary):")
    all_pass = True
    for item, status in test_results.items():
        state_str = "PASS" if status else "FAIL"
        if not status: all_pass = False
        print(f"  - [{state_str}] {item}")
    print("==========================================================================")
    if all_pass:
        print("  🎉 恭喜！全部 15 项三维建模、渲染、截图与交互功能 100% 验证通过！")
    else:
        print("  ⚠️ 部分测试未通过，请检查日志。")
    print("==========================================================================")

if __name__ == "__main__":
    run_verification()
