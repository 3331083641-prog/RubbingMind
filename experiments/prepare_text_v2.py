"""Pre-register image-only text-area sampling on the previously unused 14 artifacts."""
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.run_v2 import make_config,sha


def select_crop(gray,seed):
    h,w=gray.shape;eligible=[]
    for y in range(0,h-255,128):
        for x in range(0,w-255,128):
            tile=gray[y:y+256,x:x+256]
            dynamic=float(np.percentile(tile,90)-np.percentile(tile,10))
            edge=float(np.mean(cv2.Canny(cv2.GaussianBlur(tile,(3,3),.6),60,140)>0))
            _,binary=cv2.threshold(tile,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
            minority=float(min(np.mean(binary>0),np.mean(binary==0)))
            if dynamic>=65 and .03<=edge<=.30 and .06<=minority<=.46:
                eligible.append({'crop':[x,y,x+256,y+256],'dynamicP90P10':dynamic,'edgeFraction':edge,'minorityFraction':minority})
    if not eligible:raise ValueError('没有符合预声明图像字迹条件的区域；应人工审查，不能用纸边代替')
    selected=eligible[int(np.random.default_rng(seed).integers(len(eligible)))]
    return {**selected,'eligibleRegionCount':len(eligible),'samplingSeed':seed}


if __name__=='__main__':
    config=make_config();catalogue=json.loads((ROOT/'data/catalog/steles28.json').read_text('utf8'));samples=[]
    for dynasty in dict.fromkeys(r['dynasty'] for r in catalogue):
        for index,r in enumerate([r for r in catalogue if r['dynasty']==dynasty][2:4]):
            path=ROOT/'apps/web/public'/r['imageAssets']['readable'].split('?')[0].lstrip('/')
            image=cv2.imdecode(np.frombuffer(path.read_bytes(),np.uint8),0)
            try:selection=select_crop(image,20261018+len(samples))
            except ValueError:
                if r['id']!='song_03_daguan':raise
                h,w=image.shape;x=w//2-128;y=h//2-128
                selection={'crop':[x,y,x+256,y+256],'eligibleRegionCount':0,'samplingSeed':None,
                    'selectionStatus':'heuristic_rejected_textured_case_retained',
                    'reviewer':'Codex图像检查，非独立人工释字标注',
                    'reason':'满幅原拓文字与石花；通用字迹阈值未通过，保留中心局部作为困难案例，不按性能剔除。'}
            samples.append({'id':r['id'],'title':r['title'],'dynasty':dynasty,'script':r['scriptType'],'split':'development' if index==0 else 'test',
                'file':path.relative_to(ROOT).as_posix(),'crop':selection['crop'],'samplingDiagnostics':selection,
                'sourceSha256':sha(path),'license':r['license'],'attribution':r['attribution'],'sourceUrl':r['sourceUrl']})
    config.update(experimentId='controlled-rubbings-v2-text-2026-10-17',seed=20261018,samples=samples,
        samplingRule='未用于中心采样试验的每朝代第3/4件；128步长256方窗，P90-P10>=65，Canny密度.03-.30，Otsu少数前景.06-.46；符合条件区域中按固定种子均匀抽取，不使用任何算法输出或评测值。',
        algorithmParameters={'degraded':{},'gaussian_lowpass':{'d0':60},'butterworth_lowpass':{'d0':60,'order':2},'notch':{'d0':48},
            'fast_nlm':{'h':10,'templateWindowSize':7,'searchWindowSize':21},'morphology':{'operation':'open','kernel':3},'nlm_clahe':{'h':10,'clipLimit':2.5,'tileGridSize':[8,8]},
            'joint':{'filter':'butterworth','d0':60,'order':2,'nlm_h':10,'clahe_clip':2.5,'morph_kernel':3},'adaptive_joint':{'strength':1.,'notch_width':.8}},
        limitations=['图像字迹筛选不等于逐字人工真值标注；后续人工盲评仍需补充','独立测试仅七件文物，每朝代一件，不支持总体优势结论','真实石花与残损仍留在受控参考中','中心采样的空白失败批次完整保留，未据性能删除或改写'])
    config['samplingExceptions']={'song_03_daguan':'满幅文字石花图像未通过通用阈值；图像审查后保留中心困难区域，无算法分数参与。'}
    (ROOT/'experiments/config-v2-text.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),'utf8')
    print('Prepared 14 previously unused artifacts, with image-only text-region criteria.')
