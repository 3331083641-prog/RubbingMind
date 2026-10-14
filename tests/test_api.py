# -*- coding: utf-8 -*-
"""
墨韵智考 - FastAPI 服务端 RESTful 接口集成测试
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from main import app

client = TestClient(app)


def test_health_endpoint():
    """测试系统健康检查接口"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["system"] == "墨韵智考"


def test_steles_list_endpoint():
    """测试获取全量 28 件馆藏碑拓列表"""
    response = client.get("/api/steles")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 28
    
    # 验证七个朝代全覆盖
    dynasties = {s.get("dynasty") for s in data}
    expected_dynasties = {"东汉", "北魏", "唐代", "宋代", "元代", "明代", "清代"}
    for d in expected_dynasties:
        assert d in dynasties, f"朝代 {d} 缺失"


def test_stele_detail_endpoint():
    """测试获取单个碑拓详情"""
    response = client.get("/api/steles/tang_01_duobao")
    assert response.status_code == 200
    data = response.json()
    assert "多宝塔" in data["title"]
    assert data["dynasty"] == "唐代"
    assert "metrics" in data


def test_stele_inference_endpoint():
    """测试残字推演接口"""
    response = client.get("/api/steles/tang_01_duobao/infer")
    assert response.status_code == 200
    data = response.json()
    assert "characters" in data
    assert len(data["characters"]) >= 35
    assert "damaged_summary" in data


def test_stele_graph_endpoint():
    """测试人物与时空图谱接口"""
    response = client.get("/api/steles/tang_01_duobao/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "links" in data
    assert "gis_route" in data
    assert len(data["nodes"]) >= 4


def test_stele_report_endpoint():
    """测试消融实验报告数据接口"""
    response = client.get("/api/steles/tang_01_duobao/report")
    assert response.status_code == 200
    data = response.json()
    assert "ablation" in data
    assert data["ablation"] == []
    assert "未评测" in data["evaluation_summary"]
    assert "scholarly_analysis" in data


def test_calendar_conversion():
    """测试古代纪年与西历公元年号换算"""
    response = client.post("/api/calendar", json={"query": "天宝十一载"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("solar_year") == 752 or "752" in str(data)
