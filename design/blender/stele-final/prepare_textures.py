"""Reference registration and deterministic PBR atlas preparation.

References are user supplied AI concept images, not archaeological records.
No image synthesis service is used: this is numeric UV/height-map preparation
for the explicitly requested Blender reconstruction.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
REF = ROOT / 'design/references/stele-final'
OUT = ROOT / 'apps/web/public/assets/stele/model3d/final'
OUT.mkdir(parents=True, exist_ok=True)
W, H = 3072, 4096
REGIONS = {
    'front': (0, 0, 1024, 2048), 'back': (1024, 0, 2048, 2048),
    'crown_front': (0, 2048, 1024, 2560), 'crown_back': (1024, 2048, 2048, 2560),
    'stone': (0, 2560, 1024, 3584), 'lotus': (1024, 2560, 2048, 2816),
    'scroll': (1024, 2816, 2048, 3072), 'left': (1024, 3072, 1536, 4096),
    'right': (1536, 3072, 2048, 4096), 'bottom': (0, 3584, 1024, 4096),
    'plinth_front': (2048,0,3072,256), 'plinth_back': (2048,256,3072,512),
    'plinth_left': (2048,512,3072,768), 'plinth_right': (2048,768,3072,1024),
    'cornice_front': (2048,1024,3072,1152), 'cornice_back': (2048,1152,3072,1280),
    'cornice_left': (2048,1280,3072,1408), 'cornice_right': (2048,1408,3072,1536),
    'plinth_top': (2048,1536,3072,2048), 'cornice_top': (2048,2048,3072,2560),
    'socket_top': (2048,2560,3072,3072), 'arch_edge': (2048,3072,3072,3328),
    'lotus_left': (2048,3328,3072,3456), 'lotus_right': (2048,3456,3072,3584),
    'scroll_left': (2048,3584,3072,3840), 'scroll_right': (2048,3840,3072,4096),
}

def physical_stone(width,height,seed):
    """Stone grain authored at constant physical texel scale, no stretched crop."""
    rng=np.random.default_rng(seed); w,h=round(width*550),max(24,round(height*550))
    noise=np.zeros((h,w),np.float32)
    for cells,weight in [(9,.25),(24,.30),(65,.22),(160,.13),(500,.10)]:
        sw=max(2,round(width*cells)); sh=max(2,round(height*cells))
        noise+=cv2.resize(rng.random((sh,sw),dtype=np.float32),(w,h),interpolation=cv2.INTER_CUBIC)*weight
    flakes=np.clip((.062-np.abs(noise-.51))/.062,0,1)**2
    c=np.stack([68+noise*30+flakes*61,68+noise*28+flakes*52,65+noise*25+flakes*41],axis=-1)
    for _ in range(max(2,round(width*3))):
        points=np.column_stack([np.linspace(rng.integers(0,w),rng.integers(0,w),9),np.linspace(0,h,9)+rng.normal(0,h*.12,9)]).astype(np.int32)
        cv2.polylines(c,[points],False,(39,38,34),1,cv2.LINE_AA)
    return np.uint8(np.clip(c,0,255))

def read(direction):
    return np.array(Image.open(REF / f'stele_{direction}.png').convert('RGB'))

def crop(a, rect):
    x0, y0, x1, y1 = rect
    return a[y0:y1, x0:x1]

def normals(height, strength):
    dx = cv2.Sobel(height, cv2.CV_32F, 1, 0) * -strength
    # Image rows run downward; tangent +V runs upward in Blender.
    dy = cv2.Sobel(height, cv2.CV_32F, 0, 1) * strength
    n = np.stack([dx, dy, np.ones_like(dx)], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return np.uint8(np.clip((n * .5 + .5) * 255, 0, 255))

def main():
    front, back, left, right = [read(k) for k in ('front', 'back', 'left', 'right')]
    source = {
        'front': crop(front, (305, 275, 780, 1116)),
        'back': crop(back, (309, 267, 776, 1087)),
        'crown_front': crop(front, (305, 22, 780, 275)),
        'crown_back': crop(back, (309, 19, 777, 267)),
        'stone': crop(back, (351, 600, 737, 986)),
        'lotus': crop(front, (257, 1144, 829, 1201)),
        'scroll': crop(front, (208, 1253, 875, 1317)),
        'left': crop(left, (491, 273, 575, 1078)),
        'right': crop(right, (513, 274, 595, 1102)),
        'bottom': crop(read('bottom'), (179, 440, 1079, 790)),
    }
    source.update({
        'plinth_front':crop(front,(183,1328,905,1398)),
        'plinth_back':crop(back,(194,1290,893,1358)),
        'plinth_left':crop(left,(412,1288,676,1354)),
        'plinth_right':crop(right,(412,1318,676,1384)),
        'lotus_left':crop(left,(422,1098,653,1162)),
        'lotus_right':crop(right,(432,1127,661,1187)),
        'scroll_left':crop(left,(376,1212,703,1271)),
        'scroll_right':crop(right,(379,1241,708,1303)),
    })
    for name,width,height,seed in [('cornice_front',1.75,.036,4),('cornice_back',1.75,.036,5),('cornice_left',.65,.036,6),('cornice_right',.65,.036,7),('plinth_top',1.85,.72,8),('cornice_top',1.75,.65,9),('socket_top',1.46,.45,10),('arch_edge',1.01,.24,11)]:
        source[name]=physical_stone(width,height,seed)
    atlas = np.full((H, W, 3), 110, np.uint8)
    normal = np.empty_like(atlas); normal[:] = (128, 128, 255)
    orm = np.empty_like(atlas); orm[:] = (255, 230, 0)
    heights = {}
    for name, rect in REGIONS.items():
        x0, y0, x1, y1 = rect
        sw, sh = x1-x0-16, y1-y0-16
        a = cv2.resize(source[name], (sw, sh), interpolation=cv2.INTER_LANCZOS4)
        # Remove the white exterior from the crown rectangle before atlas packing.
        if name.startswith('crown'):
            exterior = (a.min(axis=2) > 220).astype(np.uint8)
            a = cv2.inpaint(a, exterior, 9, cv2.INPAINT_TELEA)
        g = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
        # Reduce photographic lighting without destroying weathering variation.
        low = cv2.GaussianBlur(g, (0, 0), 28)
        gain = np.clip(.38 / np.maximum(low, .12), .72, 1.10)
        color = np.uint8(np.clip(a * gain[..., None], 0, 255))
        micro = g - cv2.GaussianBlur(g, (0, 0), 2.2)
        if name.startswith('crown'):
            h = crown_height(source[name])
        elif name.startswith('lotus'):
            h = cv2.GaussianBlur(g, (0, 0), 1.8)
        elif name.startswith('scroll'):
            h = cv2.GaussianBlur(g, (0, 0), 1.5)
        else:
            h = micro
        if name.startswith(('crown','lotus','scroll')):
            heights[name] = h
        # Bright concept glyph strokes are incised, not embossed.
        tile_normal = normals(-micro if name=='front' else micro, .85)
        cavity = np.clip(1 + micro * .5, .80, 1)
        tile_orm = np.stack([cavity*255, np.clip(231-micro*35, 211, 246), np.zeros_like(g)], axis=-1).astype(np.uint8)
        for target, tile in ((atlas, color), (normal, tile_normal), (orm, tile_orm)):
            target[y0:y1, x0:x1] = cv2.copyMakeBorder(tile, 8, 8, 8, 8, cv2.BORDER_REPLICATE)
    Image.fromarray(atlas).save(OUT / 'stone_basecolor.jpg', quality=94, subsampling=0)
    # Source reference detail is <= 1K per part; 2K-high data atlas avoids
    # spending GPU memory on interpolated pixels. Base color remains 4K-high.
    Image.fromarray(normal).resize((1536,2048),Image.Resampling.LANCZOS).save(OUT / 'stone_normal.png', optimize=True)
    orm[:,:,0]=(orm[:,:,0]//8)*8
    orm[:,:,1]=(orm[:,:,1]//4)*4
    Image.fromarray(orm).resize((1536,2048),Image.Resampling.LANCZOS).save(OUT / 'stone_orm.png', optimize=True)
    np.savez_compressed(Path(__file__).parent / 'sculpt_fields.npz', **heights)
    (OUT / 'atlas.json').write_text(json.dumps({'size':[W,H], 'padding':8,'regions':REGIONS}, indent=2), encoding='utf-8')
    print('Registered reference atlas:', W, H)

def crown_height(rgb):
    """Hand registered dragon masses + carved detail, not a flat image plane.

    Raised volumes follow the coil, inward-facing head, horns, claws and clouds.
    Photometric detail is deliberately constrained to < 9 mm because lighting
    alone cannot yield archaeological depth. Orb is an analytic embedded dome.
    """
    rgb = cv2.resize(rgb, (475,253))
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    mask = np.zeros((253,475), np.uint8)
    # Left coil: neck -> large curved belly -> inward tail; mirror for right.
    coil = np.array([(99,150),(72,175),(77,207),(106,230),(143,230),(165,211),(158,187),(134,177),(115,181)], np.int32)
    head = np.array([(86,151),(83,132),(111,108),(152,100),(168,114),(184,126),(172,139),(150,151),(122,156)], np.int32)
    cv2.polylines(mask,[coil],False,255,31,cv2.LINE_AA)
    cv2.fillPoly(mask,[head],255)
    for points in [[(112,111),(104,87),(87,91),(80,74)],[(133,105),(143,82),(156,80)],
                   [(105,156),(78,162),(62,150)],[(113,190),(100,173),(89,178)],
                   [(142,192),(160,173),(173,179)]]:
        cv2.polylines(mask,[np.array(points,np.int32)],False,255,9,cv2.LINE_AA)
    mask = np.maximum(mask, cv2.flip(mask,1))
    mass = cv2.GaussianBlur(mask.astype(np.float32)/255,(0,0),3.2)
    distance = cv2.distanceTransform(mask,cv2.DIST_L2,5)
    rounded = np.clip(distance/18,0,1)**.55
    struct = cv2.GaussianBlur(g,(0,0),1.0)
    carving = np.clip((struct-.25)/.42,0,1)
    detail = g-cv2.GaussianBlur(g,(0,0),5)
    y,x = np.mgrid[0:253,0:475]
    u=(x-237.5)/237.5; v=1-y/253
    rad=np.sqrt(u*u+v*v)
    inside = np.clip((.94-rad)/.025,0,1)
    h = (-.008 + .022*mass + .014*rounded + .010*carving + .007*detail)*inside
    # Continuous rounded perimeter carved from the same crown slab.
    h += .006*np.exp(-((rad-.955)/.022)**2)
    orb_dist = np.sqrt(((x-237)/39)**2+((y-95)/39)**2)
    orb=np.maximum(1-orb_dist**2,0)**.5
    h=np.where(orb_dist<1, .052*orb, h)
    h[:2]=0; h[-2:]=0
    return h.astype(np.float32)

if __name__ == '__main__':
    main()
