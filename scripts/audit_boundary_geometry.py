"""Audit the derived boundary geometry (national outline + province internals).

Reports facts rather than assumptions:

* how much of the province-internal network lies on the national outline
  (should only be junction points, never a shared run);
* whether the national outline still contains Taiwan, Hainan and the South China
  Sea island groups after the dissolve / simplify / small-ring filter;
* how many rings the small-ring filter would drop and whether any of them is a
  named island.

    python scripts/audit_boundary_geometry.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from shapely.geometry import LineString, MultiLineString, shape
from shapely.ops import unary_union

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
GEO = ROOT / 'apps/web/public/assets/gis'
PROVINCES = GEO / 'china-provinces.cgcs2000.geojson'
NATIONAL = GEO / 'china-national-boundary.geojson'
INTERNAL = GEO / 'china-province-internal-boundaries.geojson'

# Reference boxes for elements that must survive the pipeline.
KEY_ISLANDS = {
    '台湾岛': (119.3, 21.8, 122.1, 25.4),
    '海南岛': (108.5, 18.0, 111.1, 20.2),
    '崇明岛': (121.0, 31.3, 122.0, 31.9),
    '舟山群岛': (121.8, 29.7, 122.6, 30.4),
    '南海诸岛（西沙/南沙）': (109.0, 3.0, 118.0, 12.0),
    '中沙黄岩岛': (117.0, 14.5, 118.5, 16.0),
}


def load_lines(path: Path):
    data = json.loads(path.read_text(encoding='utf-8'))
    geometries = [shape(feature['geometry']) for feature in data['features']]
    merged = unary_union(geometries)
    if isinstance(merged, MultiLineString):
        return list(merged.geoms)
    if isinstance(merged, LineString):
        return [merged]
    return [g for g in getattr(merged, 'geoms', []) if isinstance(g, LineString)]


def overlaps_box(line: LineString, box) -> bool:
    minx, miny, maxx, maxy = box
    bx0, by0, bx1, by1 = line.bounds
    return not (bx1 < minx or bx0 > maxx or by1 < miny or by0 > maxy)


def main() -> None:
    provinces = json.loads(PROVINCES.read_text(encoding='utf-8'))
    polygons = [shape(f['geometry']) for f in provinces['features']
                if f['geometry']['type'] in ('Polygon', 'MultiPolygon')]
    union = unary_union(polygons)

    national_lines = load_lines(NATIONAL)
    internal_lines = load_lines(INTERNAL)

    print('== 省级面并集 ==')
    print(f'  polygons={len(polygons)} parts={len(getattr(union, "geoms", [union]))} bounds={[round(v, 3) for v in union.bounds]}')

    print('== 国界/海岸线 ==')
    total_national = sum(line.length for line in national_lines)
    print(f'  lines={len(national_lines)} points={sum(len(l.coords) for l in national_lines)} length≈{total_national * 111:.0f} km')

    print('== 省际边界 ==')
    total_internal = sum(line.length for line in internal_lines)
    print(f'  lines={len(internal_lines)} points={sum(len(l.coords) for l in internal_lines)} length≈{total_internal * 111:.0f} km')

    # 1. Does any internal run sit on the national outline?
    national_union = unary_union(national_lines)
    on_border = total_internal * 0 - 0.0
    for line in internal_lines:
        piece = line.intersection(national_union.buffer(0.0005, join_style=2))
        on_border += piece.length
    print(f'  落在国界 50 m 缓冲内的长度：{on_border * 111:.1f} km ({on_border / max(total_internal, 1e-9) * 100:.3f}%)')

    # 2. Island coverage in the national outline.
    print('== 关键岛屿覆盖 ==')
    for name, box in KEY_ISLANDS.items():
        hits = [line for line in national_lines if overlaps_box(line, box)]
        inside = [line for line in hits if box[0] <= line.centroid.x <= box[2] and box[1] <= line.centroid.y <= box[3]]
        print(f'  {name}: 外接框相交环 {len(hits)}，重心在框内 {len(inside)}')

    # 3. What would a small-ring filter drop, measured on the *unfiltered* union?
    raw_lines = list(union.boundary.geoms) if isinstance(union.boundary, MultiLineString) else [union.boundary]
    dropped = []
    kept = []
    for line in raw_lines:
        minx, miny, maxx, maxy = line.bounds
        span = (maxx - minx) + (maxy - miny)
        (dropped if span < 0.02 else kept).append((span, line))
    print('== 小环过滤审计（阈值 0.02°，基于未过滤并集）==')
    print(f'  原始环：{len(raw_lines)}；会被删除：{len(dropped)}；保留：{len(kept)}')
    for name, box in KEY_ISLANDS.items():
        hit = [line for _, line in dropped if overlaps_box(line, box)]
        if hit:
            print(f'  [注意] 小环过滤会触碰 {name}：{len(hit)} 环')
    biggest = sorted(dropped, key=lambda item: item[0], reverse=True)[:10]
    for span, line in biggest:
        cx, cy = line.centroid.x, line.centroid.y
        print(f'  最大待删环 span={span:.4f}° 中心=({cx:.2f}, {cy:.2f}) 周长≈{line.length * 111:.1f} km')


if __name__ == '__main__':
    main()
