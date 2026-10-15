"""Browser acceptance of upload, real processing, inference selection and report linkage."""
import argparse
import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'screenshots/remediation-2026-10-15/workflow'
OUT.mkdir(parents=True, exist_ok=True)


def run(url):
    test_image = ROOT / 'data/runtime/browser-acceptance-upload.png'
    test_image.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGB', (160, 160), '#e5dfcb')
    draw = ImageDraw.Draw(image)
    for x in range(24, 137, 34):
        draw.rectangle((x, 18, x + 9, 140), fill='#332d29')
    image.save(test_image)
    result = {'errors': [], 'screenshots': [], 'uploadId': None, 'runId': None, 'inferenceId': None}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='msedge', headless=True, args=['--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width': 1440, 'height': 900}, accept_downloads=True)
        page.on('pageerror', lambda error: result['errors'].append(str(error)))
        page.goto(url, wait_until='domcontentloaded')
        expect(page.get_by_role('button', name='首页门户')).to_be_visible()
        home = OUT / '01-home.png'; page.screenshot(path=str(home), full_page=True); result['screenshots'].append(str(home))
        page.get_by_role('button', name='上传拓片').click()
        page.locator('input[type=file]').set_input_files(str(test_image))
        page.get_by_placeholder('例如：唐·多宝塔感应碑').fill('浏览器验收私有样本')
        with page.expect_response(lambda r: r.url.endswith('/api/upload') and r.request.method == 'POST') as response_info:
            page.get_by_role('button', name='立即录入并开启智能考据').click()
        upload_response = response_info.value
        assert upload_response.status == 200, upload_response.text()
        uploaded = upload_response.json()['stele']
        result['uploadId'] = uploaded['id']
        expect(page.locator('header select').first).to_have_value(uploaded['id'])
        page.reload()
        page.get_by_role('button', name='智考工作台').click()
        page.locator('header select').first.select_option(uploaded['id'])
        expect(page.locator('header select').first).to_have_value(uploaded['id'])
        with page.expect_response(lambda r: r.url.endswith('/api/process') and r.request.method == 'POST', timeout=60000) as process_info:
            page.get_by_role('button', name='执行频空域联合去噪').click()
        processed = process_info.value
        assert processed.status == 200, processed.text()
        process = processed.json()
        assert process['stele_id'] == uploaded['id'] and process['psnr'] is None
        result['runId'] = process['runId']
        expect(page.get_by_role('combobox', name='选择运行记录')).to_have_value(process['runId'])
        workbench = OUT / '02-real-processing.png'; page.screenshot(path=str(workbench), full_page=True); result['screenshots'].append(str(workbench))

        page.get_by_role('button', name='框选残字区域').click()
        crop_image = page.get_by_role('dialog', name='框选残字').locator('img')
        expect(crop_image).to_be_visible()
        box = crop_image.bounding_box()
        page.mouse.move(box['x'] + 25, box['y'] + 25)
        page.mouse.down(); page.mouse.move(box['x'] + 80, box['y'] + 80); page.mouse.up()
        page.get_by_role('dialog', name='框选残字').locator('textarea').fill('未核实')
        with page.expect_response(lambda r: '/inferences' in r.url and r.request.method == 'POST') as infer_info:
            page.get_by_role('button', name='提交实际选区').click()
        inference = infer_info.value
        assert inference.status == 200, inference.text()
        result['inferenceId'] = inference.json()['inferenceId']
        expect(page.get_by_text('候选未经过概率校准。', exact=False)).to_be_visible()
        inferred = OUT / '03-real-crop.png'; page.screenshot(path=str(inferred), full_page=True); result['screenshots'].append(str(inferred))

        page.get_by_role('button', name='算法评测报告').click()
        expect(page.get_by_role('combobox', name='选择报告运行记录')).to_have_value(process['runId'])
        expect(page.get_by_text(process['runId'], exact=False).last).to_be_visible()
        with page.expect_download() as download_info:
            page.get_by_role('button', name='导出 JSON').click()
        report_path = OUT / 'actual-report.json'; download_info.value.save_as(report_path)
        report = json.loads(report_path.read_text('utf-8'))
        assert report['runId'] == process['runId'] and report['stele']['id'] == uploaded['id']
        assert report['evaluationStatus'] == 'unassessed'
        assert any(item['inferenceId'] == result['inferenceId'] for item in report['inferenceRecords'])
        page.pdf(path=str(OUT / 'actual-report.pdf'), format='A4', print_background=True)
        report_shot = OUT / '04-report.png'; page.screenshot(path=str(report_shot), full_page=True); result['screenshots'].append(str(report_shot))
        page.get_by_role('button', name='时空图谱中心').click()
        graph_shot = OUT / '05-graph.png'; page.screenshot(path=str(graph_shot), full_page=True); result['screenshots'].append(str(graph_shot))
        browser.close()
    assert not result['errors'], result['errors']
    (OUT / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), 'utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:5174')
    args = parser.parse_args()
    print(json.dumps(run(args.url), ensure_ascii=False, indent=2))
