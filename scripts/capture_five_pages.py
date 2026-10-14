# -*- coding: utf-8 -*-
"""
墨韵智考 - 自动化高清五大模块界面截图脚本 (用于 README 与赛事评审答辩)
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)

TARGETS = [
    {
        "url": "http://127.0.0.1:8000/#/",
        "output": "01_home_portal_3d.png",
        "wait_selector": "canvas",
        "delay": 3.0,
        "name": "首页三维数字展陈门户"
    },
    {
        "url": "http://127.0.0.1:8000/#/museum",
        "output": "02_digital_museum.png",
        "wait_selector": "text=中华贞石数字典藏馆",
        "delay": 2.5,
        "name": "中华贞石数字典藏馆"
    },
    {
        "url": "http://127.0.0.1:8000/#/workbench",
        "output": "03_restoration_workbench.png",
        "wait_selector": "text=频空域微痕修复工作台",
        "delay": 2.5,
        "name": "频空域微痕修复工作台"
    },
    {
        "url": "http://127.0.0.1:8000/#/graph",
        "output": "04_graphrag_gis.png",
        "wait_selector": "text=时空考据",
        "delay": 3.0,
        "name": "GraphRAG 与 GIS 时空图谱"
    },
    {
        "url": "http://127.0.0.1:8000/#/reports",
        "output": "05_ablation_reports.png",
        "wait_selector": "text=算法评测",
        "delay": 2.5,
        "name": "算法评测及考据报告"
    }
]

def capture_all():
    print(f"[*] 开始自动化采集系统 5 大核心模块高清真实截图...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--disable-web-security", "--allow-file-access-from-files"]
        )
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        for item in TARGETS:
            out_path = os.path.join(OUT_DIR, item["output"])
            print(f"[*] 正在捕获: {item['name']} -> {item['output']}")
            try:
                page.goto(item["url"], wait_until="domcontentloaded", timeout=30000)
                try:
                    page.wait_for_selector(item["wait_selector"], timeout=10000)
                except Exception:
                    pass
                time.sleep(item["delay"])
                page.screenshot(path=out_path, full_page=False)
                size_kb = os.path.getsize(out_path) // 1024
                print(f"[OK] 成功捕获 {item['name']} ({size_kb} KB)")
            except Exception as e:
                print(f"[!] 捕获失败 {item['name']}: {e}")

        browser.close()
    print("[OK] 五大页面真实运行截图采集完毕！")

if __name__ == "__main__":
    capture_all()
