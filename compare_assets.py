# -*- coding: utf-8 -*-
import json
import glob
import os

def main():
    f28 = [p for p in glob.glob(r"D:\RubbingMind\data\museum-import\*28*.json") if "merged" not in p][0]
    with open(f28, "r", encoding="utf-8") as fp:
        d28 = json.load(fp)
    assets28 = d28.get("assets", []) if isinstance(d28, dict) else d28

    f16 = glob.glob(r"D:\RubbingMind\data\museum-import\*16*.json")[0]
    with open(f16, "r", encoding="utf-8") as fp:
        d16 = json.load(fp)
    assets16 = d16.get("assets", []) if isinstance(d16, dict) else d16

    print(f"28 items count: {len(assets28)}")
    print(f"16 items count: {len(assets16)}")

    # Check IDs in 16 vs 28
    ids_16 = {a["id"]: a for a in assets16}
    ids_28 = {a["id"]: a for a in assets28}

    print("\nOverlap of IDs:")
    common = set(ids_16.keys()).intersection(set(ids_28.keys()))
    print(f"Common IDs count: {len(common)}")

    # Inspect fields across both
    keys_28 = set().union(*(a.keys() for a in assets28))
    keys_16 = set().union(*(a.keys() for a in assets16))
    print(f"Keys in 28: {sorted(list(keys_28))}")
    print(f"Keys in 16: {sorted(list(keys_16))}")

    # Inspect each asset in 28
    print("\n--- Summary of 28 assets ---")
    for i, a in enumerate(assets28):
        aid = a["id"]
        extra = ids_16.get(aid, {})
        print(f"[{i+1:02d}] {aid:25s} | 朝代:{a.get('dynasty')} | 题目:{a.get('title')} | 馆藏:{a.get('repository')} | 馆藏号:{a.get('accession_number')} | 纪年:{a.get('stele_year_ce')} | 书体:{a.get('script')} | 图像状态:{a.get('image_status')} | Commons:{a.get('commons_filename') or extra.get('commons_filename')}")

if __name__ == "__main__":
    main()
