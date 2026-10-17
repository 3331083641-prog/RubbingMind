"""Real ROI analysis and opt-in human-labelled template retrieval (not OCR)."""
from __future__ import annotations
import cv2
import numpy as np
from skimage.morphology import skeletonize

VERSION='glyph-shape-v2.0'


def analyze_crop(crop):
    gray=cv2.cvtColor(crop,cv2.COLOR_BGR2GRAY) if crop.ndim==3 else crop.copy()
    _,binary=cv2.threshold(gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # Foreground polarity chosen by boundary median, disclosed in record.
    boundary=np.concatenate([gray[0],gray[-1],gray[:,0],gray[:,-1]])
    invert=bool(np.median(boundary)>127)
    if invert:binary=255-binary
    count,labels,stats,_=cv2.connectedComponentsWithStats(binary,8)
    noise=np.zeros_like(binary)
    for i in range(1,count):
        if stats[i,cv2.CC_STAT_AREA]<max(2,gray.size*.0002):noise[labels==i]=255
    foreground=cv2.bitwise_and(binary,cv2.bitwise_not(noise))
    skeleton=(skeletonize(foreground>0)*255).astype(np.uint8)
    points=cv2.findNonZero(foreground)
    bbox=list(cv2.boundingRect(points)) if points is not None else None
    touched=float(np.mean(np.concatenate([foreground[0],foreground[-1],foreground[:,0],foreground[:,-1]])>0))
    lengths=[float(np.mean(skeleton[a:b]>0)) for a,b in [(0,len(skeleton)//3),(len(skeleton)//3,2*len(skeleton)//3),(2*len(skeleton)//3,len(skeleton))]]
    components=cv2.connectedComponents(foreground)[0]-1
    warnings=[]
    if touched>.08:warnings.append('前景触及选区边缘，可能裁断字符或包含邻字')
    if bbox is None or np.mean(foreground>0)<.005:warnings.append('有效字迹不足')
    if components>30:warnings.append('碎片较多，可能含石花、多个字符或重度残损')
    return ({'version':VERSION,'foregroundPolarity':'dark' if invert else 'bright','contentBox':bbox,
            'foregroundFraction':float(np.mean(foreground>0)),'componentCount':components,
            'skeletonPixels':int(np.count_nonzero(skeleton)),'horizontalStrokeDistribution':lengths,
            'borderForegroundFraction':touched,'noisePixelCount':int(np.count_nonzero(noise)),
            'warnings':warnings,'identityStatus':'未识别；二值连通结构不等于真实汉字笔画拓扑或完整性真值'},
            {'gray':gray,'foreground':foreground,'skeleton':skeleton,'noise':noise})


def normalized_shape(foreground):
    points=cv2.findNonZero(foreground)
    canvas=np.zeros((64,64),np.uint8)
    if points is None:return canvas
    x,y,w,h=cv2.boundingRect(points);scale=56/max(w,h)
    patch=cv2.resize(foreground[y:y+h,x:x+w],(max(1,round(w*scale)),max(1,round(h*scale))),interpolation=cv2.INTER_NEAREST)
    yy,xx=(64-patch.shape[0])//2,(64-patch.shape[1])//2
    canvas[yy:yy+patch.shape[0],xx:xx+patch.shape[1]]=patch
    return canvas


def shape_similarity(a,b):
    a=normalized_shape(a)>0;b=normalized_shape(b)>0
    if not a.any() or not b.any():return 0.
    da=cv2.distanceTransform((~a).astype(np.uint8),cv2.DIST_L2,3)
    db=cv2.distanceTransform((~b).astype(np.uint8),cv2.DIST_L2,3)
    chamfer=float((da[b].mean()+db[a].mean())/2)
    projection=float(np.mean(abs(a.mean(0)-b.mean(0)))+np.mean(abs(a.mean(1)-b.mean(1))))
    return float(np.exp(-chamfer/4-projection*2))
