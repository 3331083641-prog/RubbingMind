"""Paint hypsometric relief from the existing Terrarium DEM tiles.

The output keeps each source tile's z/x/y address. Elevation is decoded, not
redrawn, and no coastline or province boundary is edited.
"""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'apps/web/public/assets/gis/terrain'
DST = ROOT / 'apps/web/public/assets/gis/relief'
STOPS = (
    (-8000, (4, 14, 24)),
    (-80, (7, 28, 40)),
    (0, (12, 62, 56)),
    (80, (24, 108, 90)),
    (450, (36, 124, 102)),
    (1200, (52, 112, 94)),
    (2200, (86, 108, 92)),
    (3500, (132, 140, 128)),
    (4800, (198, 206, 200)),
    (6000, (232, 236, 232)),
)


def elevation(rgb):
    return rgb[:, :, 0] * 256 + rgb[:, :, 1] + rgb[:, :, 2] / 256.0 - 32768


def paint(height):
    colors = np.empty(height.shape + (3,), np.float32)
    for channel in range(3):
        colors[:, :, channel] = np.interp(height, [s[0] for s in STOPS], [s[1][channel] for s in STOPS])
    broad = cv2.GaussianBlur(height, (0, 0), 4)
    gy, gx = np.gradient(height)
    by, bx = np.gradient(broad)
    fine = np.tanh((-gx - gy) / 28.0)
    mass = np.tanh((-bx - by) / 45.0)
    relief = np.clip(0.66 + 0.40 * mass + 0.30 * fine, 0.34, 1.58)
    relief = np.where(height < 0, 0.97, relief)
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
