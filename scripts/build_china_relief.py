"""Paint hypsometric relief from the existing Terrarium DEM tiles.

The output keeps each source tile's z/x/y address. Elevation is decoded, not
redrawn, and no coastline or province boundary is edited.
"""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'apps/web/public/assets/gis/terrain'
DST = ROOT / 'apps/web/public/assets/gis/relief'
STOPS = (
    (-8000, (6, 16, 24)),
    (-200, (8, 24, 34)),
    (0, (11, 34, 40)),
    (120, (18, 58, 50)),
    (500, (26, 74, 64)),
    (1400, (48, 84, 74)),
    (2600, (74, 82, 70)),
    (4000, (118, 124, 118)),
    (5600, (168, 176, 172)),
)


def elevation(rgb):
    return rgb[:, :, 0] * 256 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0 - 32768


def paint(height):
    colors = np.empty(height.shape + (3,), np.float32)
    for channel in range(3):
        colors[:, :, channel] = np.interp(height, [s[0] for s in STOPS], [s[1][channel] for s in STOPS])
    gy, gx = np.gradient(height)
    relief = np.clip(0.78 + 0.34 * np.tanh((-gx - gy) / 90.0), 0.46, 1.22)
    relief = np.where(height < 0, 0.94 + 0.06 * np.tanh(height / 2500.0), relief)
    return np.clip(colors * relief[:, :, None], 0, 255).astype(np.uint8)


def main():
    written = 0
    for source in SRC.rglob('*.png'):
        if source.parent == SRC:
            continue
        image = np.asarray(Image.open(source).convert('RGB'), np.float32)
        target = DST / source.relative_to(SRC)
        target.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(paint(elevation(image)), 'RGB').save(target, optimize=True)
        written += 1
    print(f'wrote {written} relief tiles from the existing Terrarium DEM')


if __name__ == '__main__':
    main()
