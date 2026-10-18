"""Extract the true national boundary from the province polygons.

The `china-provinces` file only carries province geometries plus a handful of
maritime line features; there is no separate "national border" layer. Drawing
every province ring in one golden style therefore makes the national border look
exactly like an internal one.

This script dissolves the 34 province multi-polygons into a single union and
keeps only its boundary. Interior province edges disappear in the dissolve, so
the remaining lines are the real national land border plus the coastline and
every island ring. Geometry is not edited: the output reuses the upstream
coordinates, with a configurable topology-preserving simplification.

    python scripts/build_national_boundary.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from shapely.geometry import MultiLineString, Polygon, MultiPolygon, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'apps/web/public/assets/gis/china-provinces.cgcs2000.geojson'
DST = ROOT / 'apps/web/public/assets/gis/china-national-boundary.geojson'
# 0.002 degrees ~ 200 m: far below the 2.2 km DEM spacing, keeps the outline crisp
# without carrying duplicate vertices that the province data already repeats.
SIMPLIFY = 0.002


def main() -> int:
    source = json.loads(SRC.read_text(encoding='utf-8'))
    polygons = [shape(feature['geometry']) for feature in source['features']
                if feature['geometry']['type'] in ('Polygon', 'MultiPolygon')]
    assert len(polygons) == 34, len(polygons)

    union = unary_union(polygons)
    assert union.is_valid, 'province union is not valid — refusing to publish an edited border'
    simplified = union.simplify(SIMPLIFY, preserve_topology=True)
    boundary = simplified.boundary

    if isinstance(boundary, MultiLineString):
        lines = [list(line.coords) for line in boundary.geoms]
    else:
        lines = [list(boundary.coords)]

    # Keep every ring, including the smallest islets and reefs: the official map
    # expression of the South China Sea islands depends on them, and 517 rings is
    # a trivial rendering cost. Performance is handled by LOD, not by deleting
    # geographic features.
    kept = lines
    dropped = 0

    feature = {
        'type': 'Feature',
        'properties': {
            'name': '中国国界与海岸线',
            'kind': 'national_boundary',
            'method': '34 个省级面做拓扑并集后取边界；内部省界在并集中消失',
            'sourceFeatureCount': len(polygons),
            'simplifyDegrees': SIMPLIFY,
            'crs': 'EPSG:4490 / CGCS2000（沿用上游坐标，未重投影）',
            'upstreamApprovalClaim': 'GS(2024)0650（镜像仓库声明，非本应用审图证明）',
            'generated': date.today().isoformat(),
            'rings': len(kept),
            'droppedRings': dropped,
            'points': sum(len(line) for line in kept),
        },
        'geometry': {'type': 'MultiLineString', 'coordinates': kept},
    }
    DST.write_text(json.dumps({'type': 'FeatureCollection', 'features': [feature]}, ensure_ascii=False), encoding='utf-8')
    print(f'rings={len(kept)} dropped={dropped} points={feature["properties"]["points"]} '
          f'bytes={DST.stat().st_size}')
    print('bbox', [round(v, 3) for v in union.bounds])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
