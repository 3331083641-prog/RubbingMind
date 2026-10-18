"""Fetch Terrarium DEM tiles for the China terrain scene.

Source: AWS Open Data "Terrain Tiles" (s3://elevation-tiles-prod, Mapzen-derived).
No API key is required. Each tile is a 256x256 RGB PNG in Terrarium encoding:

    elevation_m = R * 256 + G + B / 256 - 32768

The command only downloads and verifies tiles; it never resamples, reprojects or
edits elevation values. ``terrain/manifest.json`` records which zoom levels and
tile ranges are actually present on disk, so the front end can fall back to a
coarser level instead of requesting 404s.

Usage
-----
Overview tiles committed to the repository (z4-z5, China and surroundings):

    python scripts/fetch_terrain_dem.py --zoom 4 5

Optional high-detail tiles (kept out of Git, see .gitignore):

    python scripts/fetch_terrain_dem.py --zoom 6 9 --bbox 73 17 135 54 --workers 12
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TILES = ROOT / 'apps/web/public/assets/gis/terrain'
MANIFEST = TILES / 'manifest.json'
PROVENANCE = TILES / 'provenance.json'
BASE_URL = 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
SOURCE = {
    'name': 'AWS Open Data — Terrain Tiles (Mapzen terrarium)',
    'officialUrl': 'https://registry.opendata.aws/terrain-tiles/',
    'tileUrl': 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',
    'encoding': 'terrarium (R*256 + G + B/256 - 32768)',
    'verticalDatum': 'EGM96 geoid (SRTM/GMTED/3DEP source mix)',
    'crs': 'EPSG:3857 tile grid / EPSG:4326 sample positions',
    'license': 'Open data; per-provider attribution required (see ATTRIBUTION.md)',
    'attribution': 'Mapzen / USGS 3DEP / SRTM (NASA-NGA) / GMTED2010 / NOAA ETOPO1',
}
# Default overview window: China plus a continental margin so the relief plate
# does not end on the national border.
DEFAULT_BBOX = (60.0, 0.0, 150.0, 60.0)


def lon_to_tile(lon: float, zoom: int) -> int:
    n = 2 ** zoom
    return max(0, min(n - 1, int(math.floor((lon + 180.0) / 360.0 * n))))


def lat_to_tile(lat: float, zoom: int) -> int:
    n = 2 ** zoom
    lat = max(-85.05112878, min(85.05112878, lat))
    rad = math.radians(lat)
    return max(0, min(n - 1, int(math.floor((1.0 - math.log(math.tan(rad) + 1.0 / math.cos(rad)) / math.pi) / 2.0 * n))))


def tile_range(bbox, zoom: int):
    west, south, east, north = bbox
    return (lon_to_tile(west, zoom), lat_to_tile(north, zoom),
            lon_to_tile(east, zoom), lat_to_tile(south, zoom))


def decode(rgb_bytes: bytes) -> None:
    """Verify a tile really is a 256x256 PNG before it is written to disk."""
    from PIL import Image
    image = Image.open(io.BytesIO(rgb_bytes))
    if image.size != (256, 256) or image.mode not in ('RGB', 'RGBA'):
        raise ValueError(f'unexpected tile format {image.size} {image.mode}')


def fetch_one(zoom: int, x: int, y: int, retries: int = 3) -> tuple[int, int, int, int, str]:
    target = TILES / str(zoom) / str(x) / f'{y}.png'
    if target.exists() and target.stat().st_size > 0:
        return zoom, x, y, target.stat().st_size, 'cached'
    url = BASE_URL.format(z=zoom, x=x, y=y)
    last = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'RubbingMind-terrain/1.0'})
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = response.read()
            decode(payload)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
            return zoom, x, y, len(payload), 'downloaded'
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError) as error:  # noqa: PERF203
            last = error
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f'{zoom}/{x}/{y} failed: {last}')


def scan_levels() -> dict[int, dict]:
    """Read what is really on disk, grouped by zoom."""
    levels: dict[int, dict] = {}
    for zoom_dir in sorted(p for p in TILES.iterdir() if p.is_dir() and p.name.isdigit()):
        zoom = int(zoom_dir.name)
        xs = []
        ys = []
        count = 0
        for x_dir in (p for p in zoom_dir.iterdir() if p.is_dir() and p.name.isdigit()):
            for tile in x_dir.glob('*.png'):
                xs.append(int(x_dir.name))
                ys.append(int(tile.stem))
                count += 1
        if not count:
            continue
        levels[zoom] = {
            'z': zoom,
            'tiles': count,
            'minX': min(xs), 'maxX': max(xs),
            'minY': min(ys), 'maxY': max(ys),
        }
    return levels


def write_manifest(levels: dict[int, dict], fetched: list[tuple[int, int, int, int, str]]) -> None:
    digest = hashlib.sha256()
    total = 0
    for zoom in sorted(levels):
        for x_dir in sorted((TILES / str(zoom)).iterdir()):
            for tile in sorted(x_dir.glob('*.png')):
                digest.update(tile.read_bytes())
                total += len(tile.read_bytes())
    manifest = {
        'format': 'terrarium-png',
        'levels': [levels[z] for z in sorted(levels)],
        'maxZoom': max(levels) if levels else 0,
        'totalTiles': sum(level['tiles'] for level in levels.values()),
        'totalBytes': total,
        'sha256': digest.hexdigest(),
        'generated': date.today().isoformat(),
        'note': 'manifest 由 scripts/fetch_terrain_dem.py 扫描真实磁盘文件生成；缺失的层级不会被伪造。',
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    record = {
        **SOURCE,
        'retrieved': date.today().isoformat(),
        'requestedBbox': bbox,
        'requestedZoom': [args.zoom[0], args.zoom[1]] if args.zoom else None,
        'levels': manifest['levels'],
        'downloads': [
            {'z': z, 'x': x, 'y': y, 'bytes': size, 'status': status}
            for z, x, y, size, status in fetched
        ],
        'processing': 'None. Tiles are stored byte-for-byte as served; elevation is decoded at runtime.',
        'caveat': 'SRTM/GMTED mix; vertical datum follows the upstream product (EGM96), not WGS84 ellipsoid.',
    }
    PROVENANCE.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"manifest: {manifest['totalTiles']} tiles, {total/1e6:.1f} MB, z0-z{manifest['maxZoom']}, sha256={manifest['sha256'][:16]}…")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zoom', nargs=2, type=int, metavar=('MIN', 'MAX'), default=[4, 5])
    parser.add_argument('--bbox', nargs=4, type=float, metavar=('W', 'S', 'E', 'N'), default=list(DEFAULT_BBOX))
    parser.add_argument('--workers', type=int, default=8)
    global args, bbox
    args = parser.parse_args()
    bbox = tuple(args.bbox)
    jobs = []
    for zoom in range(args.zoom[0], args.zoom[1] + 1):
        x0, y0, x1, y1 = tile_range(bbox, zoom)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                jobs.append((zoom, x, y))
    print(f'bbox={bbox} zooms={args.zoom[0]}..{args.zoom[1]} tiles={len(jobs)} workers={args.workers}')
    fetched = []
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_one, *job): job for job in jobs}
        for done, future in enumerate(as_completed(futures), 1):
            try:
                fetched.append(future.result())
            except RuntimeError as error:
                failures.append(str(error))
            if done % 25 == 0 or done == len(jobs):
                print(f'  {done}/{len(jobs)}')
    print(f'downloaded={sum(1 for f in fetched if f[4] == "downloaded")} cached={sum(1 for f in fetched if f[4] == "cached")} failed={len(failures)}')
    for failure in failures:
        print('  !', failure)
    write_manifest(scan_levels(), fetched)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
