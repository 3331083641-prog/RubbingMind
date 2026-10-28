import os
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel=os.getenv('RUBBINGMIND_BROWSER_CHANNEL', 'msedge'), headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto('http://127.0.0.1:8740/?tab=reports&view=global')
    page.wait_for_timeout(800)
    for width, height in [(1920, 1080), (1440, 900), (1366, 768), (390, 844)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.wait_for_timeout(650)
        box = page.get_by_test_id('method-comparison-chart').bounding_box()
        cond = box['y'] < height and box['height'] >= 260
        print(f"Viewport {width}x{height}: y={box['y']}, h={box['height']}, pass={cond}")
    browser.close()
