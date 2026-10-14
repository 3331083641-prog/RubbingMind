#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真实馆藏碑拓批量下载与 JPEG 提取。需在联网的本地 Windows 电脑运行。"""
import argparse, hashlib, json, math, pathlib, sys, time, urllib.parse

try:
    import requests
    import fitz
    from PIL import Image
except ImportError:
    sys.exit('缺少依赖，请运行：python -m pip install requests pymupdf Pillow')

HERE=pathlib.Path(__file__).resolve().parent.parent
DATA=json.loads((HERE/'宋元明清_16件馆藏清单.json').read_text(encoding='utf-8'))
UA='MoyunZhikaoMuseumResearch/1.0 (educational collection downloader; include attribution; contact: project-local)'
S=requests.Session()
S.headers.update({'User-Agent':UA,'Accept':'application/json,application/pdf,image/jpeg,*/*'})


def lookup_original(filename):
    api='https://commons.wikimedia.org/w/api.php'
    res=S.get(api,params={'action':'query','prop':'imageinfo','iiprop':'url|size|mime','titles':'File:'+filename,'format':'json','formatversion':'2'},timeout=45)
    res.raise_for_status()
    pages=res.json().get('query',{}).get('pages',[])
    if not pages or 'missing' in pages[0]:
        raise RuntimeError('Wikimedia Commons 未找到文件')
    infos=pages[0].get('imageinfo',[])
    if not infos:raise RuntimeError('没有原始图片链接')
    return infos[0]['url'],infos[0].get('size',0)


def download_original(url,path,max_bytes=100*1024*1024):
    temp=path.with_suffix(path.suffix+'.part')
    for attempt in range(3):
        try:
            with S.get(url,timeout=(15,90),stream=True) as r:
                r.raise_for_status()
                if int(r.headers.get('Content-Length','0'))>max_bytes:raise ValueError('原文件超出100 MB大小限制')
                total=0
                with temp.open('wb') as f:
                    for part in r.iter_content(chunk_size=256*1024):
                        if not part:continue
                        total+=len(part)
                        if total>max_bytes:raise ValueError('下载中超出文件大小限制')
                        f.write(part)
            temp.replace(path)
            return hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception as e:
            temp.unlink(missing_ok=True)
            if attempt==2:raise
            print('  重试：',str(e)[:120]);time.sleep(2+attempt*3)


def extract_pdf_images(pdf_path,out_dir,id,number_of_scan_pages=1,limit=4):
    doc=fitz.open(pdf_path)
    maxpages=min(len(doc),max(1,number_of_scan_pages),limit)
    exports=[]
    for p in range(maxpages):
        page=doc[p]
        images=page.get_images(full=True)
        scored=[]
        for it in images:
            try:
                i=doc.extract_image(it[0]);scored.append((i['width']*i['height'],i))
            except Exception:pass
        scored.sort(key=lambda pair:pair[0],reverse=True)
        if scored and scored[0][0]>=250000:
            img=scored[0][1]
            suffix=img.get('ext','png').lower()
            if suffix=='jpx':suffix='jp2'
            original=out_dir / f'{id}_scan_p{p+1:02d}.{suffix}'
            original.write_bytes(img['image'])
            # 统一的网页预览图，不改变馆藏主图
            try:
                with Image.open(original) as im:
                    im=im.convert('RGB');im.thumbnail((1500,1900))
                    thumb=out_dir / f'{id}_preview_p{p+1:02d}.jpg'
                    im.save(thumb,quality=88,optimize=True)
            except Exception as e:
                print('  无法转换预览，保留原始图：',e)
                thumb=original
        else:
            # PDF 绘制了矢量/其他图像时采用渲染兜底；不生成或伪造字形
            pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False)
            original=out_dir / f'{id}_scan_p{p+1:02d}.png'
            pix.save(original)
            thumb=original
        exports.append({'pdf_page_1based':p+1,'scan_file':str(original.relative_to(HERE)).replace('\\','/'),'preview_file':str(thumb.relative_to(HERE)).replace('\\','/')})
    doc.close()
    return exports


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--dry-run',action='store_true',help='仅输出下载计划，不访问互联网')
    parser.add_argument('--album-pages',type=int,default=4,help='每件拓本最多导出前多少幅馆藏图像（默认4）')
    parser.add_argument('--only',nargs='*',default=[],help='可选：指定碑拓id')
    args=parser.parse_args()
    selected=[a for a in DATA['assets'] if a['source_kind']=='commons_pdf' and (not args.only or a['id'] in args.only)]
    print('仅自动下载已核实 Commons PDF 的11件，其余5件须人工确认图像许可。')
    success,errors=[],[]
    for i,asset in enumerate(selected,1):
        id=asset['id'];p=HERE/'downloads'/asset['dynasty']/id;p.mkdir(parents=True,exist_ok=True)
        suffix='.jpg' if asset.get('original_format', 'PDF').upper()=='JPG' else '.pdf'
        original=p/(id+'_archive'+suffix)
        print(f'[{i}/{len(selected)}] {asset["dynasty"]} · {asset["title"]}  {asset["file_page_url"]}')
        if args.dry_run:continue
        try:
            if not original.exists() or original.stat().st_size<1024:
                url,size=lookup_original(asset['commons_filename'])
                sha=download_original(url,original)
            else:
                sha=hashlib.sha256(original.read_bytes()).hexdigest()
            if suffix=='.pdf':exports=extract_pdf_images(original,p,id,asset['source_image_count'],args.album_pages)
            else:
                dest=p/(id+'_preview_p01.jpg')
                with Image.open(original) as im:
                    im=im.convert('RGB');im.thumbnail((1500,1900));im.save(dest,quality=88,optimize=True)
                exports=[{'pdf_page_1based':None,'scan_file':str(original.relative_to(HERE)).replace('\\','/'),'preview_file':str(dest.relative_to(HERE)).replace('\\','/')}]
            success.append({'id':id,'title':asset['title'],'dynasty':asset['dynasty'],'sha256':sha,'image_sources':exports,'archive_path':str(original.relative_to(HERE)).replace('\\','/'),'license':asset['license'],'attribution':asset['attribution'],'source_url':asset['file_page_url']})
            print('  已下载及提取图像：',len(exports))
        except Exception as e:
            errors.append({'id':id,'error':str(e)})
            print('  下载失败：',str(e))
        time.sleep(0.3)
    if not args.dry_run:
        (HERE/'download_result_song_yuan_ming_qing.json').write_text(json.dumps({'success':success,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
        print(f'\n完成：{len(success)}件；失败：{len(errors)}件。结果见 download_result_song_yuan_ming_qing.json')
        if errors:print('请核查网络连接、Commons API 及具体文件页面链接；不要以占位图代替。')

if __name__=='__main__':main()
