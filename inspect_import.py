# -*- coding: utf-8 -*-
import json
import os
import glob

def check_json(file_path):
    print("=" * 60)
    print(f"Checking: {file_path}")
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
    print(f"Type: {type(data)}")
    if isinstance(data, dict):
        print("Keys:", list(data.keys()))
        for k, v in data.items():
            if isinstance(v, list):
                print(f"  Field '{k}' has {len(v)} items")
                if len(v) > 0 and isinstance(v[0], dict):
                    print(f"    Sample item keys: {list(v[0].keys())}")
                    # Count by dynasty
                    dynasties = {}
                    for item in v:
                        d = item.get("dynasty") or item.get("dynasty_id") or item.get("era") or "Unknown"
                        dynasties[d] = dynasties.get(d, 0) + 1
                    print(f"    Dynasty distribution in '{k}': {dynasties}")
            else:
                print(f"  Field '{k}': {str(v)[:100]}")
    elif isinstance(data, list):
        print(f"List length: {len(data)}")
        if len(data) > 0:
            print("Sample item keys:", list(data[0].keys()))
            dynasties = {}
            for item in data:
                d = item.get("dynasty") or item.get("dynasty_id") or item.get("era") or "Unknown"
                dynasties[d] = dynasties.get(d, 0) + 1
            print(f"Dynasty distribution: {dynasties}")

def main():
    import_dir = r"D:\RubbingMind\data\museum-import"
    for f in glob.glob(os.path.join(import_dir, "**", "*.json"), recursive=True):
        check_json(f)

if __name__ == "__main__":
    main()
