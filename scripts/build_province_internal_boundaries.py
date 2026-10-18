"""Extract the province-to-province boundaries (neighbouring province borders).

Why this exists
---------------
The upstream `china-provinces` file holds 34 province polygons. Every shared
province border therefore appears **twice** (once in each polygon ring), and the
national land border / coastline / island rings appear a second time on top of
the dedicated national outline layer. Drawing those rings as "province borders"
made coastlines double-stroked and made shared borders render twice as opaque.

This script removes the duplication with topology:

1. dissolve all provinces -> union, take its boundary = national border + coastline;
2. take every province boundary, subtract the union boundary (small tolerance);
3. union the remainders: a shared border now collapses into a single line.

No distance-based pruning of real administrative borders is performed: the only
removal is exact overlap with the national outline.

    python scripts/build_province_internal_boundaries.py
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from shapely.geometry import LineString, MultiLineString, Polygon, MultiPolygon, mapping, shape
from shapely.ops import linemerge, unary_union

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'apps/web/public/assets/gis/china-provinces.cgcs2000.geojson'
DST = ROOT / 'apps/web/public/assets/gis/china-province-internal-boundaries.geojson'

# ~50 m: enough to drop vertices that sit exactly on the national outline,
# far below the 2.2 km DEM spacing, so no real inter-province border is removed.
NATIONAL_TOLERANCE = 0.0005
# Same simplification as the national outline to keep both files consistent.
SIMPLIFY = 0.002


def as_lines(geometry) -> list[LineString]:
    if geometry.is_empty:
        return []
    if isinstance(geometry, LineString):
        return [geometry]
    if isinstance(geometry, MultiLineString):
        return list(geometry.geoms)
    return [line for line in getattr(geometry, 'geoms', []) if isinstance(line, LineString)]


def main() -> int:
    source = json.loads(SRC.read_text(encoding='utf-8'))
    polygons = [shape(feature['geometry']) for feature in source['features']
                if feature['geometry']['type'] in ('Polygon', 'MultiPolygon')]
    assert len(polygons) == 34, len(polygons)

    union = unary_union(polygons)
    national_boundary = union.boundary

    internal_parts = []
    for province in polygons:
        remainder = province.boundary.difference(national_boundary.buffer(NATIONAL_TOLERANCE, join_style=2))
        internal_parts.extend(as_lines(remainder))

    merged = unary_union(internal_parts)
    merged = linemerge(merged) if isinstance(merged, MultiLineString) else merged
    simplified = merged.simplify(SIMPLIFY, preserve_topology=True)
    lines = as_lines(simplified)

    # Keep every internal segment; only zero-length fragments are dropped.
    kept = [line for line in lines if line.length > 1e-6]
    coordinates = [list(line.coords) for line in kept]
    total_km = sum(LineString(line).length for line in coordinates) * 111.0
    points = sum(len(line) for line in coordinates)

    feature = {
        'type': 'Feature',
        'properties': {
            'name': '省际行政边界',
            'kind': 'province_internal_boundary',
            'method': '省级面边界减去国界并集边界后取并集；相邻省份共享边界只保留一次',
            'sourceFeatureCount': len(polygons),
            'nationalToleranceDegrees': NATIONAL_TOLERANCE,
            'simplifyDegrees': SIMPLIFY,
            'crs': 'EPSG:4490 / CGCS2000（沿用上游坐标，未重投影）',
            'upstreamApprovalClaim': 'GS(2024)0650（镜像仓库声明，非本应用审图证明）',
            'generated': date.today().isoformat(),
            'lines': len(kept),
            'points': points,
            'lengthKm': round(total_km, 1),
        },
        'geometry': {'type': 'MultiLineString', 'coordinates': coordinates},
    }
    DST.write_text(json.dumps({'type': 'FeatureCollection', 'features': [feature]}, ensure_ascii=False), encoding='utf-8')
    print(f'lines={len(kept)} points={points} length≈{total_km:.0f} km bytes={DST.stat().st_size}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
