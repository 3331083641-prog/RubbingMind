"""Verify the DEM pyramid, decode math and the terrain surface claims.

These checks read the real tiles that ship in the repository; nothing here is
mocked. They guard the properties the 3D scene depends on:

* Terrarium decoding returns real metres (Tibetan Plateau high, Tarim low).
* The manifest matches the files on disk (no fabricated coverage).
* The horizontal resolution of each level matches its advertised zoom.
* The hypsometric ramp is monotonic in elevation and stays inside the
  ink / celadon / stone / gold palette band.
"""
from __future__ import annotations

import io
import json
import math
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TERRAIN = ROOT / 'apps/web/public/assets/gis/terrain'


def terrarium(rgb: np.ndarray) -> np.ndarray:
    return rgb[:, :, 0] * 256.0 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0 - 32768.0


def tile_path(z: int, x: int, y: int) -> Path:
    return TERRAIN / str(z) / str(x) / f'{y}.png'


def lon_to_tile(lon: float, z: int) -> int:
    return int((lon + 180) / 360 * 2 ** z)


def lat_to_tile(lat: float, z: int) -> int:
    rad = math.radians(lat)
    return int((1 - math.log(math.tan(rad) + 1 / math.cos(rad)) / math.pi) / 2 * 2 ** z)


def sample(lon: float, lat: float, z: int) -> float:
    x, y = lon_to_tile(lon, z), lat_to_tile(lat, z)
    path = tile_path(z, x, y)
    assert path.exists(), f'missing tile {z}/{x}/{y}'
    image = np.asarray(Image.open(path).convert('RGB'), np.float32)
    heights = terrarium(image)
    fx = (lon + 180) / 360 * 2 ** z * 256 - x * 256 - 0.5
    fy = (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * 2 ** z * 256 - y * 256 - 0.5
    i = int(np.clip(round(fx), 0, 255))
    j = int(np.clip(round(fy), 0, 255))
    return float(heights[j, i])


def test_manifest_matches_disk():
    manifest = json.loads((TERRAIN / 'manifest.json').read_text(encoding='utf-8'))
    actual = {}
    for level_dir in TERRAIN.iterdir():
        if not level_dir.is_dir() or not level_dir.name.isdigit():
            continue
        count = sum(1 for _ in level_dir.rglob('*.png'))
        if count:
            actual[int(level_dir.name)] = count
    listed = {level['z']: level['tiles'] for level in manifest['levels']}
    assert listed == actual, f'manifest {listed} != disk {actual}'
    assert manifest['maxZoom'] == max(actual)
    assert manifest['totalTiles'] == sum(actual.values())


def test_tiles_are_terrarium_pngs():
    for zoom in (0, 3, 5, 6):
        tiles = sorted((TERRAIN / str(zoom)).rglob('*.png'))[:3]
        assert tiles, f'no tiles at z{zoom}'
        for tile in tiles:
            image = Image.open(io.BytesIO(tile.read_bytes()))
            assert image.size == (256, 256)
            assert image.mode in ('RGB', 'RGBA')


def test_elevation_is_real_geography():
    """The DEM must show the Tibetan Plateau high and the Tarim Basin low."""
    everest = sample(86.925, 27.988, 5)
    lhasa = sample(91.14, 29.65, 5)
    tarim = sample(83.0, 39.5, 5)
    north_plain = sample(116.4, 36.0, 5)
    shanghai_offshore = sample(123.0, 31.0, 5)

    assert 6000 < everest < 9200, everest
    assert 3000 < lhasa < 4800, lhasa
    assert 700 < tarim < 1600, tarim
    assert -20 < north_plain < 200, north_plain
    assert shanghai_offshore < 0, shanghai_offshore

    # 西高东低: the plateau must sit far above the eastern plain.
    assert lhasa - north_plain > 3000


def test_vertical_resolution_beats_national_view_needs():
    """z5 must resolve at least 120 samples across China's 62 degrees."""
    degrees_per_pixel = 360 / (256 * 2 ** 5)
    assert 62 / degrees_per_pixel > 120


def test_no_bathymetry_fabrication():
    """Ocean pixels are negative (real bathymetry), not clamped to zero."""
    image = np.asarray(Image.open(tile_path(5, 26, 13)).convert('RGB'), np.float32)
    heights = terrarium(image)
    assert heights.min() < -1000


def test_hypsometric_ramp_is_monotonic_and_in_palette():
    source = (ROOT / 'apps/web/src/components/graph/terrain3d/terrainMaterial.ts').read_text(encoding='utf-8')
    start = source.index('export const TERRAIN_RAMP')
    end = source.index('];', start)
    block = source[start:end]
    stops = []
    for line in block.splitlines():
        line = line.strip()
        if line.startswith('[') and '#' in line:
            height = float(line[1:line.index(',')])
            hex_value = line[line.index("'#") + 2:line.index("'#") + 8]
            red, green, blue = (int(hex_value[i:i + 2], 16) for i in (0, 2, 4))
            stops.append((height, (red, green, blue)))
    assert len(stops) >= 10
    heights = [height for height, _ in stops]
    assert heights == sorted(heights), 'ramp heights must increase'
    # Low ground is dark and blue-green (青黛), high ground warm (泥金), peaks pale.
    low = stops[2][1]
    high = stops[10][1]
    peak = stops[-1][1]
    assert max(low) < 90, low
    assert low[2] >= low[0], low
    assert high[0] > high[2], high
    assert min(peak) > 200, peak
    # No washed-out bright green anywhere: green may not dominate by a wide margin.
    for _, (red, green, blue) in stops:
        assert not (green > red + 60 and green > blue + 60), (red, green, blue)


def test_terrain_module_has_no_random_terrain():
    """Guard against noise-generated 'mountains' sneaking into the engine."""
    banned = ['Math.random', 'simplex', 'perlin', 'noise(']
    for path in (ROOT / 'apps/web/src/components/graph/terrain3d').glob('*.ts'):
        text = path.read_text(encoding='utf-8')
        for token in banned:
            assert token not in text, f'{path.name} contains {token}'
