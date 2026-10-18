"""Browser check for the 28-work authorship and image-condition release."""
import argparse
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'screenshots/museum-assessment-v3'


def run(url):
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel='msedge', headless=True, args=['--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.goto(url, wait_until='domcontentloaded')
        header = page.locator('header').first
        expect(header.get_by_role('button', name='贞石典藏馆')).to_be_visible()
        page.screenshot(path=str(OUT / '01-home.png'), full_page=True)
        header.get_by_role('button', name='贞石典藏馆').click()
        expect(page.get_by_test_id('museum-card')).to_have_count(28)
        expect(page.get_by_text('拓本影像损伤状况')).to_be_visible()
        page.screenshot(path=str(OUT / '02-museum-28.png'), full_page=True)
        checks.append('28 museum cards')
        for dynasty in ['东汉', '北魏', '唐代', '宋代', '元代', '明代', '清代']:
            page.get_by_role('button', name=re.compile('^' + dynasty + r'\s*4$')).click()
            expect(page.get_by_test_id('museum-card')).to_have_count(4)
            page.screenshot(path=str(OUT / f'03-dynasty-{dynasty}.png'), full_page=True)
        page.get_by_role('button', name=re.compile(r'^全部\s*28$')).click()
        moderate = page.get_by_role('button', name='中度影像损伤', exact=True)
        moderate.click()
        expect(page.get_by_test_id('museum-card')).not_to_have_count(0)
        expect(page.get_by_test_id('museum-card')).not_to_have_count(28)
        page.screenshot(path=str(OUT / '04-image-condition.png'), full_page=True)
        page.get_by_role('button', name='严重漫漶', exact=True).click()
        expect(page.get_by_test_id('museum-card')).to_have_count(0)
        page.get_by_role('button', name='重置所有筛选条件').click()
        expect(page.get_by_test_id('museum-card')).to_have_count(28)
        checks.append('dynasty and image-condition filters')
        duobao = page.locator('[data-stele-id="tang_01_duobao"]')
        duobao_text = duobao.inner_text()
        assert '岑勋' in duobao_text and '颜真卿' in duobao_text and '徐浩' in duobao_text and '史华' in duobao_text
        duobao.screenshot(path=str(OUT / '05-duobao-authorship.png'))
        caoquan = page.locator('[data-stele-id="han_01_caoquan"]')
        assert '未核定' in caoquan.inner_text() and '曹全' in caoquan.inner_text()
        ming = page.locator('[data-stele-id="ming_04_tongdian"]')
        ming_text = ming.inner_text()
        assert '王毓宗' in ming_text and '存在争议' in ming_text and '王羲之' not in ming_text
        qing = page.locator('[data-stele-id="qing_02_wushi_reerection"]')
        assert '翁方纲（待复核）' in qing.inner_text()
        yuan = page.locator('[data-stele-id="yuan_04_jingyuanchang"]')
        assert '敬元长（待复核）' in yuan.inner_text()
        assert '撰文' in yuan.inner_text() and '未核定' in yuan.inner_text()
        page.screenshot(path=str(OUT / '06-unverified-and-disputed.png'), full_page=True)
        checks.append('authorship roles, dispute and pending review')
        duobao.get_by_role('button', name='查看高清拓本', exact=True).click()
        dialog = page.get_by_role('dialog')
        expect(dialog.get_by_test_id('archive-image')).to_be_visible()
        page.screenshot(path=str(OUT / '07-readable-rubbing.png'))
        dialog.get_by_role('button', name='关闭档案').click()
        duobao.get_by_role('button', name='微痕修复').click()
        expect(header.locator('select')).to_have_value('tang_01_duobao')
        expect(page.get_by_text('撰文 岑勋')).to_be_visible()
        with page.expect_response(lambda response: response.url.endswith('/api/process') and response.request.method == 'POST', timeout=60000) as captured:
            page.get_by_role('button', name='执行频空域联合去噪').click()
        assert captured.value.ok
        run = captured.value.json()
        assert run['psnr'] is None and run.get('runId') and run.get('adaptiveDiagnostics')
        page.screenshot(path=str(OUT / '08-adaptive-result.png'), full_page=True)
        checks.append('workbench adaptive run without fake PSNR')
        page.get_by_role('button', name='框选残字区域').click()
        glyph = page.get_by_role('dialog', name='框选残字')
        image = glyph.locator('img')
        expect(image).to_be_visible()
        image.evaluate('(node) => node.decode()')
        box = image.bounding_box()
        page.mouse.move(box['x'] + box['width'] * 0.3, box['y'] + box['height'] * 0.3)
        page.mouse.down()
        page.mouse.move(box['x'] + box['width'] * 0.46, box['y'] + box['height'] * 0.48)
        page.mouse.up()
        with page.expect_response(lambda response: response.url.endswith('/inferences') and response.request.method == 'POST') as inferred:
            page.get_by_role('button', name='提交实际选区').click()
        assert inferred.value.ok
        body = inferred.value.json()
        assert body['imageProvenance']['imageSource'] == 'restored' and body['imageProvenance']['runOwnership'] == 'verified'
        page.screenshot(path=str(OUT / '09-glyph-roi.png'), full_page=True)
        checks.append('restored-run glyph crop')
        header.get_by_role('button', name='时空图谱中心').click()
        header.locator('select').select_option('qing_02_wushi_reerection')
        expect(page.get_by_role('heading', name='重立武氏祠石记 · 馆藏资料关联')).to_be_visible()
        assert '翁方纲（待复核）' in page.locator('main').inner_text()
        page.screenshot(path=str(OUT / '10-pending-authorship-graph.png'), full_page=True)
        panel = page.get_by_role('region', name='史料智能检索')
        panel.get_by_label('史料问题').fill('《多宝塔碑》的撰文者是不是岑勋？')
        with page.expect_response(lambda response: response.url.endswith('/api/research/query')) as refused:
            panel.get_by_role('button', name='检索史料').click()
        assert refused.value.ok
        expect(page.get_by_test_id('research-answer')).to_contain_text('不足以')
        header.locator('select').select_option('tang_01_duobao')
        panel = page.get_by_role('region', name='史料智能检索')
        expect(panel).to_be_visible()
        panel.get_by_label('史料问题').fill('《多宝塔碑》的撰文者与书丹者是谁？')
        with page.expect_response(lambda response: response.url.endswith('/api/research/query')) as research:
            panel.get_by_role('button', name='检索史料').click()
        assert research.value.ok
        answer = page.get_by_test_id('research-answer')
        expect(answer).to_contain_text('岑勋')
        expect(answer).to_contain_text('颜真卿')
        page.screenshot(path=str(OUT / '11-graphrag.png'), full_page=True)
        checks.append('graph and evidence answer')
        header.get_by_role('button', name='算法评测报告').click()
        expect(page.get_by_role('heading', name='墨韵智考·金石数字化实验报告').last).to_be_visible()
        page.screenshot(path=str(OUT / '12-report.png'), full_page=True)
        checks.append('report page')
        browser.close()
    return checks


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:5180/')
    args = parser.parse_args()
    print('\n'.join(run(args.url)))
