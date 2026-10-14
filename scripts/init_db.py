# -*- coding: utf-8 -*-
"""
墨韵智考 - 数据库初始化与种子数据迁移脚本
执行命令：python scripts/init_db.py
"""
import os
import sys

# 保证能加载项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import init_database, query_steles, DB_PATH

def main():
    print(f"[*] 正在初始化墨韵智考 SQLite 数据库: {DB_PATH}")
    init_database()
    steles = query_steles()
    print(f"[OK] 数据库表结构创建成功，已加载 {len(steles)} 件真实馆藏档案记录。")

if __name__ == "__main__":
    main()
