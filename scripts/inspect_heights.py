import os
from playwright.sync_api import sync_playwright

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=os.getenv('RUBBINGMIND_BROWSER_CHANNEL', 'msedge'), headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.goto('http://127.0.0.1:8740/?tab=reports&view=global')
        page.wait_for_timeout(1000)
        info = page.evaluate('''() => {
            const bodyH = document.body.scrollHeight;
            const htmlH = document.documentElement.scrollHeight;
            const mainH = document.querySelector('main')?.scrollHeight;
            const reportPageH = document.querySelector('.report-page')?.scrollHeight;
            const stageH = document.querySelector('#report-analysis-stage')?.getBoundingClientRect().height;
            const navH = document.querySelector('.studio-navigator')?.getBoundingClientRect().height;
            const footerH = document.querySelector('footer')?.getBoundingClientRect().height;
            const layoutH = document.querySelector('.studio-layout')?.getBoundingClientRect().height;
            const windowH = window.innerHeight;
            return { bodyH, htmlH, mainH, reportPageH, stageH, navH, layoutH, footerH, windowH };
        }''')
        print('Global view measurements:', info)

        page.goto('http://127.0.0.1:8740/?tab=reports&view=artifact')
        page.wait_for_timeout(1000)
        info_art = page.evaluate('''() => {
            const bodyH = document.body.scrollHeight;
            const htmlH = document.documentElement.scrollHeight;
            const reportPageH = document.querySelector('.report-page')?.scrollHeight;
            const artifactH = document.querySelector('[data-testid="artifact-report"]')?.getBoundingClientRect().height;
            const footerH = document.querySelector('footer')?.getBoundingClientRect().height;
            const windowH = window.innerHeight;
            return { bodyH, htmlH, reportPageH, artifactH, footerH, windowH };
        }''')
        print('Artifact view measurements:', info_art)
        browser.close()

if __name__ == '__main__':
    inspect()
