# -*- coding: utf-8 -*-
import zipfile
import os
import sys

def main():
    zip_path = r"D:\RubbingMind\28 件合并馆藏清单.zip"
    dest_dir = r"D:\RubbingMind\data\museum-import"
    os.makedirs(dest_dir, exist_ok=True)

    print(f"Reading zip: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        infolist = zf.infolist()
        print(f"Total entries in zip: {len(infolist)}")
        for info in infolist:
            raw_name = info.filename
            name = raw_name
            # Try to decode correctly
            for enc in ["utf-8", "gbk", "gb18030", "cp936"]:
                try:
                    name = raw_name.encode("cp437").decode(enc)
                    break
                except Exception:
                    pass

            # Sanitize path for Windows
            parts = name.replace("\\", "/").split("/")
            clean_parts = []
            for part in parts:
                for bad_c in '<>:"|?*':
                    part = part.replace(bad_c, "_")
                part = part.strip()
                if part and part != ".":
                    clean_parts.append(part)

            if not clean_parts:
                continue

            target_path = os.path.join(dest_dir, *clean_parts)
            if info.is_dir() or raw_name.endswith("/"):
                os.makedirs(target_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zf.open(info) as src, open(target_path, "wb") as dst:
                    dst.write(src.read())
            print(f"  [OK] Extracted: {os.path.relpath(target_path, dest_dir)} ({info.file_size} bytes)")

    print("\nExtraction complete! Files inside D:\\RubbingMind\\data\\museum-import:")
    for root, dirs, files in os.walk(dest_dir):
        for f in files:
            full_path = os.path.join(root, f)
            print(f"  - {os.path.relpath(full_path, dest_dir)} ({os.path.getsize(full_path)} bytes)")

if __name__ == "__main__":
    main()
