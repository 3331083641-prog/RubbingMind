"""Real ROI analysis and opt-in human-labelled template retrieval (not OCR)."""
from __future__ import annotations
import cv2
import numpy as np
from skimage.morphology import skeletonize

VERSION='glyph-shape-v2.1'


def _topology(skeleton):
    ink=skeleton>0
    if not ink.any():
        return 0,0
    padded=np.pad(ink,1)
    neighbors=np.zeros(ink.shape,np.int32)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if dy or dx:
                neighbors+=padded[1+dy:1+dy+ink.shape[0],1+dx:1+dx+ink.shape[1]]
    return int(np.count_nonzero(ink&(neighbors==1))),int(np.count_nonzero(ink&(neighbors>=3)))


def _gap_count(foreground,box):
    """Empty cells inside the ink box, between cells that still contain ink."""
    if box is None:
        return 0
    x,y,w,h=box
    patch=foreground[y:y+h,x:x+w]>0
    if min(patch.shape)<6:
        return 0
    ys=np.linspace(0,patch.shape[0],4,dtype=int)
    xs=np.linspace(0,patch.shape[1],4,dtype=int)
    occupied=[]
    for row in range(3):
        for col in range(3):
            occupied.append(bool(patch[ys[row]:ys[row+1],xs[col]:xs[col+1]].any()))
    gaps=0
    for index,present in enumerate(occupied):
        if present:
            continue
        neighbors=[]
        if index%3:neighbors.append(occupied[index-1])
        if index%3<2:neighbors.append(occupied[index+1])
        if index>=3:neighbors.append(occupied[index-3])
        if index<6:neighbors.append(occupied[index+3])
        if sum(neighbors)>=2:
            gaps+=1
    return gaps


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
    largest_area=0
    largest_box=None
    kept=cv2.connectedComponentsWithStats(foreground,8)
    for i in range(1,kept[0]):
        area=int(kept[2][i,cv2.CC_STAT_AREA])
        if area>largest_area:
            largest_area=area
            largest_box=[int(kept[2][i,cv2.CC_STAT_LEFT]),int(kept[2][i,cv2.CC_STAT_TOP]),int(kept[2][i,cv2.CC_STAT_WIDTH]),int(kept[2][i,cv2.CC_STAT_HEIGHT])]
    skeleton=(skeletonize(foreground>0)*255).astype(np.uint8)
    points=cv2.findNonZero(foreground)
    bbox=list(cv2.boundingRect(points)) if points is not None else None
    touched=float(np.mean(np.concatenate([foreground[0],foreground[-1],foreground[:,0],foreground[:,-1]])>0))
    lengths=[float(np.mean(skeleton[a:b]>0)) for a,b in [(0,len(skeleton)//3),(len(skeleton)//3,2*len(skeleton)//3),(2*len(skeleton)//3,len(skeleton))]]
    components=kept[0]-1
    endpoints,branches=_topology(skeleton)
    gaps=_gap_count(foreground,bbox)
    foreground_pixels=max(1,int(np.count_nonzero(foreground)))
    largest_fraction=largest_area/foreground_pixels if largest_area else 0.
    warnings=[]
    if touched>.08:warnings.append('前景触及选区边缘，可能裁断字符或包含邻字')
    if bbox is None or np.mean(foreground>0)<.005:warnings.append('有效字迹不足')
    if components>30:warnings.append('碎片较多，可能含石花、多个字符或重度残损')
    if gaps:warnings.append('字迹包围盒内存在局部空缺，不能把空缺补成笔画')
    reject=bbox is None or float(np.mean(foreground>0))<.005 or (components>80 and largest_fraction<.15)
    identity='拒识：有效字迹不足或无法确定单字区域。结构描述不是识别结果。' if reject else '未识别；骨架、连通域和空缺只描述选区结构，不是汉字身份或完整度真值。'
    return ({'version':VERSION,'foregroundPolarity':'dark' if invert else 'bright','contentBox':bbox,
            'characterRegion':largest_box,'largestComponentFraction':float(largest_fraction),
            'foregroundFraction':float(np.mean(foreground>0)),'componentCount':components,
            'skeletonPixels':int(np.count_nonzero(skeleton)),'endpointCount':endpoints,'branchCount':branches,
            'localGapCount':gaps,'horizontalStrokeDistribution':lengths,
            'borderForegroundFraction':touched,'noisePixelCount':int(np.count_nonzero(noise)),
            'rejectRecognition':bool(reject),'warnings':warnings,'identityStatus':identity},
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


def _contour_score(a,b):
    def largest(mask):
        contours,_=cv2.findContours(mask.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
        return max(contours,key=cv2.contourArea) if contours else None
    ca,cb=largest(a),largest(b)
    if ca is None or cb is None or len(ca)<5 or len(cb)<5:
        return None
    def hu(contour):
        moments=cv2.HuMoments(cv2.moments(contour)).flatten()
        return np.sign(moments)*np.log10(np.abs(moments)+1e-12)
    return float(np.exp(-np.linalg.norm(hu(ca)-hu(cb))))


def shape_similarity(a,b):
    a=normalized_shape(a)>0;b=normalized_shape(b)>0
    if not a.any() or not b.any():return 0.
    da=cv2.distanceTransform((~a).astype(np.uint8),cv2.DIST_L2,3)
    db=cv2.distanceTransform((~b).astype(np.uint8),cv2.DIST_L2,3)
    chamfer=float((da[b].mean()+db[a].mean())/2)
    projection=float(np.mean(abs(a.mean(0)-b.mean(0)))+np.mean(abs(a.mean(1)-b.mean(1))))
    chamfer_score=float(np.exp(-chamfer/4-projection*2))
    contour=_contour_score(a,b)
    if contour is None:
        return chamfer_score
    return float(0.75*chamfer_score+0.25*contour)
