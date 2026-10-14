# -*- coding: utf-8 -*-
import json
import os
import sys

def main():
    json_path = r"D:\RubbingMind\data\museum-import\merged_28_steles.json"
    with open(json_path, "r", encoding="utf-8") as f:
        steles = json.load(f)

    print("=" * 80)
    print(f"28 件真实馆藏来源与图像状态全景分析 (总数: {len(steles)})")
    print("=" * 80)

    has_commons = 0
    catalog_only = 0
    dynasty_counts = {}

    for i, s in enumerate(steles):
        d = s.get("dynasty", "未知")
        dynasty_counts[d] = dynasty_counts.get(d, 0) + 1
        cf = s.get("commons_filename")
        if cf:
            has_commons += 1
            status_tag = "[Commons 可下载]"
        else:
            catalog_only += 1
            status_tag = "[馆藏著录/待授权获取]"
        
        print(f"[{i+1:02d}] {d:4s} | {s['id']:25s} | {s['title'][:16]:16s} | {status_tag} | 机构: {s.get('repository')}")
        if cf:
            print(f"     -> Commons文件: {cf}")
        print(f"     -> 来源页面: {s.get('file_page_url') or s.get('web_museum_record_url')}")
        print(f"     -> 许可协议: {s.get('license')} | 署名: {s.get('attribution')}")

    print("\n" + "=" * 80)
    print(f"统计汇总:")
    print(f"  - 具备 Commons 公开数字化影像文件名: {has_commons} 件")
    print(f"  - 仅馆藏著录/待授权获取: {catalog_only} 件")
    print(f"  - 各朝代分布: {dynasty_counts}")
    print("=" * 80)

if __name__ == "__main__":
    main()
