# -*- coding: utf-8 -*-
"""
真实馆藏碑拓高清封面与扫描图自动化批量获取器 (基于 Wikimedia Commons 官方影像 API)
自动处理已授权的 23 件 Commons 数字化母本，精确区分 5 件待授权著录记录
"""
import os
import json
import time
import requests
from PIL import Image

OUT_DIR = r"D:\RubbingMind\data\museum-images"
WEB_ASSETS_DIR = r"D:\RubbingMind\apps\web\public\assets\stele\museum-rubbings"
DIST_ASSETS_DIR = r"D:\RubbingMind\apps\web\dist\assets\stele\museum-rubbings"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(WEB_ASSETS_DIR, exist_ok=True)
os.makedirs(DIST_ASSETS_DIR, exist_ok=True)

UA = "MoyunZhikaoMuseumResearch/1.0 (educational research and cultural digitization; contact: local)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept": "application/json,image/jpeg,image/png,*/*"})


def lookup_commons_thumb(filename, width=1200):
    """通过 Wikimedia API 查询指定宽度的高清渲染图 URL，避免触发大文件 429 频控"""
    api = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "prop": "imageinfo",
        "iiprop": "url|size|mime",
        "iiurlwidth": str(width),
        "titles": "File:" + filename,
        "format": "json",
        "formatversion": "2"
    }
    r = SESSION.get(api, params=params, timeout=25)
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        raise RuntimeError(f"Commons未找到文件: {filename}")
    infos = pages[0].get("imageinfo", [])
    if not infos:
        raise RuntimeError(f"无图片信息: {filename}")
    
    thumb_url = infos[0].get("thumburl") or infos[0].get("url")
    return thumb_url


def download_image(url, target_path):
    temp_path = target_path + ".part"
    for attempt in range(3):
        try:
            with SESSION.get(url, timeout=(10, 40), stream=True) as r:
                r.raise_for_status()
                with open(temp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=64 * 1024):
                        if chunk:
                            f.write(chunk)
            if os.path.exists(temp_path):
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(temp_path, target_path)
                return True
        except Exception as e:
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
            if attempt == 2:
                raise e
            time.sleep(1.5 + attempt * 2)
    return False


def sync_to_web(local_cover_path, stele_id):
    """优化并同步至前端静态目录"""
    web_file = os.path.join(WEB_ASSETS_DIR, f"{stele_id}_cover.jpg")
    dist_file = os.path.join(DIST_ASSETS_DIR, f"{stele_id}_cover.jpg")
    
    with Image.open(local_cover_path) as im:
        im_rgb = im.convert("RGB")
        im_rgb.thumbnail((1200, 1600), Image.Resampling.LANCZOS)
        im_rgb.save(web_file, quality=88, optimize=True)
        im_rgb.save(dist_file, quality=88, optimize=True)


def main():
    json_path = r"D:\RubbingMind\data\museum-import\merged_28_steles.json"
    with open(json_path, "r", encoding="utf-8") as f:
        steles = json.load(f)

    print(f"============================================================")
    print(f"  墨韵智考 - 28 件真实馆藏数字化母本影像智能获取系统")
    print(f"============================================================")

    results = {}
    success_count = 0
    catalog_count = 0

    for i, s in enumerate(steles):
        stele_id = s["id"]
        title = s["title"]
        dynasty = s["dynasty"]
        cf = s.get("commons_filename")
        cover_path = os.path.join(OUT_DIR, f"{stele_id}_cover.jpg")

        if not cf:
            catalog_count += 1
            print(f"[{i+1:02d}/28] {dynasty} · {title} -> [馆藏著录] 严格按规范保留待获取/待授权状态")
            results[stele_id] = {
                "status": "catalog_record",
                "image_status": "原图待授权或待获取",
                "cover_url": None,
                "notes": "符合馆藏著录规范，未私自捏造图像"
            }
            continue

        # 检查本地是否已有提取好的 cover
        if os.path.exists(cover_path) and os.path.getsize(cover_path) > 1024:
            print(f"[{i+1:02d}/28] {dynasty} · {title} -> [已存在本地母本] ({os.path.getsize(cover_path) / 1024:.1f} KB)")
            sync_to_web(cover_path, stele_id)
            success_count += 1
            results[stele_id] = {
                "status": "downloaded",
                "image_status": "高清图像已获取",
                "cover_url": f"/assets/stele/museum-rubbings/{stele_id}_cover.jpg"
            }
            continue

        print(f"[{i+1:02d}/28] {dynasty} · {title} -> 正在获取官方数字化母本...")
        try:
            thumb_url = lookup_commons_thumb(cf, width=1200)
            download_image(thumb_url, cover_path)
            sync_to_web(cover_path, stele_id)
            success_count += 1
            print(f"   [OK] 成功获取并生成高清封面: {os.path.getsize(cover_path) / 1024:.1f} KB")
            results[stele_id] = {
                "status": "downloaded",
                "image_status": "高清图像已获取",
                "cover_url": f"/assets/stele/museum-rubbings/{stele_id}_cover.jpg"
            }
        except Exception as e:
            print(f"   [WARN] 获取失败: {e}")
            results[stele_id] = {
                "status": "error",
                "image_status": "原图待授权或待获取",
                "error": str(e)
            }
        time.sleep(1.0)

    # 保存状态清单
    status_file = os.path.join(OUT_DIR, "import_image_status.json")
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n============================================================")
    print(f"  获取结果汇总:")
    print(f"  - 真实馆藏高清图像已获取: {success_count} 件")
    print(f"  - 馆藏著录/待授权获取状态: {catalog_count} 件")
    print(f"  - 状态结果已写入: {status_file}")
    print(f"============================================================")

    # 触发 museum_manager 重新刷新状态
    try:
        from museum_manager import museum_manager
        updated = museum_manager.refresh_images_status()
        print(f"  [OK] 已同步更新 museum_manager 数据库记录 ({updated} 件已关联图片)")
    except Exception as e:
        print(f"  [WARN] 同步数据库异常: {e}")


if __name__ == "__main__":
    main()
