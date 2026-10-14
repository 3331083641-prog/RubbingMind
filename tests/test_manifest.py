# -*- coding: utf-8 -*-
"""
墨韵智考 - 28件真实馆藏碑拓元数据完整性与合规性测试
"""
import os
import json
import pytest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_JSON = os.path.join(BASE_DIR, "data", "museum_database.json")


def test_museum_database_file_exists():
    assert os.path.exists(DB_JSON), "museum_database.json 文件缺失"


def test_exact_28_steles_count():
    with open(DB_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 28, f"期望28件碑拓，实际为 {len(data)}"


def test_seven_dynasties_balance():
    with open(DB_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    dynasty_counts = {}
    for item in data:
        dyn = item.get("dynasty")
        dynasty_counts[dyn] = dynasty_counts.get(dyn, 0) + 1

    expected = {"东汉": 4, "北魏": 4, "唐代": 4, "宋代": 4, "元代": 4, "明代": 4, "清代": 4}
    for dyn, expected_count in expected.items():
        assert dynasty_counts.get(dyn) == expected_count, f"{dyn} 数量异常: {dynasty_counts.get(dyn)} != {expected_count}"


def test_required_metadata_fields():
    with open(DB_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    required_fields = [
        "id", "title", "dynasty", "dynasty_value", "author", "script_type",
        "weathering_level", "year", "location", "museum", "dimensions",
        "summary", "raw_image", "clean_image", "license", "attribution",
        "imageStatus"
    ]

    for item in data:
        for rf in required_fields:
            assert rf in item, f"碑拓 {item.get('id')} 缺少必要字段 {rf}"
            assert item[rf] is not None, f"碑拓 {item.get('id')} 字段 {rf} 不能为空"
