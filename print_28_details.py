# -*- coding: utf-8 -*-
import json
import os
import glob
import sys

# Ensure UTF-8 stdout
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def main():
    import_dir = r"D:\RubbingMind\data\museum-import"
    f28 = glob.glob(os.path.join(import_dir, "*28*.json"))[0]
    with open(f28, "r", encoding="utf-8") as fp:
        doc = json.load(fp)

    print("Project:", doc.get("project"))
    print("Scope:", doc.get("scope"))
    print("Collection Count:", doc.get("collection_count"))
    print("License Notes:", doc.get("license_notes"))
    
    assets = doc.get("assets", [])
    print(f"\nLoaded {len(assets)} assets:")
    
    # Save a clean copy
    clean_path = os.path.join(r"D:\RubbingMind\data\museum-import", "merged_28_steles.json")
    with open(clean_path, "w", encoding="utf-8") as out_fp:
        json.dump(assets, out_fp, ensure_ascii=False, indent=2)
    print(f"Saved clean JSON to {clean_path}")

    dynasty_map = {}
    for i, a in enumerate(assets):
        d = a.get("dynasty")
        dynasty_map.setdefault(d, []).append(a)
        print(f"[{i+1:02d}] 朝代: {d} | 题名: {a.get('title')} | 机构: {a.get('repository')} | 馆藏号: {a.get('accession_number')} | 状态: {a.get('image_status')} | 来源: {a.get('source_type')}")

    print("\n朝代分组统计:")
    for d, items in dynasty_map.items():
        print(f"  朝代【{d}】: {len(items)} 件")
        for item in items:
            print(f"    - {item.get('id')}: {item.get('title')} ({item.get('stele_year_ce')}年, 馆藏号: {item.get('accession_number')})")

if __name__ == "__main__":
    main()
