"""Artifact-grouped controlled degradation; production never receives the labels."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
import cv2
import numpy as np
import skimage
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from algorithm_engine import compute_metrics
from degradation_analysis import AdaptiveRubbingRestorer, VERSION
from experiments.run_ablation import apply_method

METHODS=['degraded','gaussian_lowpass','butterworth_lowpass','notch','fast_nlm','morphology','nlm_clahe','joint','adaptive_joint']


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def make_config():
    catalogue=json.loads((ROOT/'data/catalog/steles28.json').read_text('utf8'))
    selected=[]
    for dynasty in dict.fromkeys(r['dynasty'] for r in catalogue):
        for index,r in enumerate([r for r in catalogue if r['dynasty']==dynasty][:2]):
            path=ROOT/'apps/web/public'/r['imageAssets']['readable'].split('?')[0].lstrip('/')
            with Image.open(path) as image:w,h=image.size
            # Declared geometric sampling, not selection by algorithm performance.
            x=max(0,w//2-128);y=max(0,h//2-128)
            selected.append({'id':r['id'],'dynasty':dynasty,'script':r['scriptType'],'split':'development' if index==0 else 'test',
                'file':path.relative_to(ROOT).as_posix(),'crop':[x,y,x+256,y+256],
                'license':r['license'],'attribution':r['attribution'],'sourceUrl':r['sourceUrl'],'sourceSha256':sha(path)})
    return {'experimentId':'controlled-rubbings-v2-2026-10-17','seed':20261017,'samples':selected,'methods':METHODS,
            'degradations':['gaussian','salt_pepper','periodic','blur','occlusion'],'strengths':[.65,1.3],
            'samplingRule':'前两件按馆藏清单顺序；中心256方形；首件开发，次件测试；无按性能筛选。',
            'referenceNote':'受控参考为真实拓本阅读图局部，仍含历史噪声；不等于原石历史真值。',
            'limitations':['每朝代独立测试仅1件；不支持普遍优势结论','没有人工字符标注，不报告OCR准确率','非盲选中心区域可能含纸边/空白，保留所有失败区域']}


def degrade(reference,mode,seed,strength):
    rng=np.random.default_rng(seed);h,w=reference.shape
    result=reference.astype(np.float32)
    params={'strength':strength,'seed':seed}
    if mode=='gaussian':
        params['sigma']=18*strength;result+=rng.normal(0,params['sigma'],reference.shape)
    elif mode=='salt_pepper':
        p=.018*strength;params['probabilityPerTail']=p;random=rng.random(reference.shape);result[random<p]=0;result[random>1-p]=255
    elif mode=='periodic':
        params.update(amplitude=27*strength,periodPixels=8,phase=0);result+=27*strength*np.sin(2*np.pi*np.arange(w)[None,:]/8)
    elif mode=='blur':
        params['sigma']=1.5*strength;result=cv2.GaussianBlur(reference,(0,0),params['sigma'])
    elif mode=='occlusion':
        y,x=h//3,w//3;hh,ww=int(28*strength),int(45*strength)
        result[y:y+hh,x:x+ww]=np.median(reference);params['rectangle']=[x,y,ww,hh];params['fill']=float(np.median(reference))
    else:raise ValueError(mode)
    return np.clip(result,0,255).astype(np.uint8),params


def grouped_summary(rows,seed):
    summary=[];rng=np.random.default_rng(seed)
    for split in ['development','test']:
        for method in METHODS:
            # All inputs retained, including non-applicable notch identity and failures.
            values=[r for r in rows if r['split']==split and r['method']==method and r.get('error') is None]
            item={'split':split,'method':method,'n':len(values),'applicableN':sum(r['applicability']!='not_applicable' for r in values),
                  'artifactN':len(set(r['sampleId'] for r in values))}
            for metric in ['psnr','ssim','edgeF1','processingMs']:
                numeric=[r for r in values if r[metric] is not None]
                vals=np.array([r[metric] for r in numeric]);groups=[np.mean([r[metric] for r in numeric if r['sampleId']==i]) for i in sorted(set(r['sampleId'] for r in numeric))]
                boot=np.mean(rng.choice(groups,(1000,len(groups)),replace=True),axis=1) if groups else np.array([np.nan])
                item.update({metric+'Mean':float(np.mean(vals)) if len(vals) else None,metric+'Std':float(np.std(vals,ddof=1)) if len(vals)>1 else 0.,
                             metric+'CI95':np.percentile(boot,[2.5,97.5]).tolist()})
            summary.append(item)
    return summary


def run(config,out):
    if out.exists():raise ValueError('输出批次已存在；使用新目录保留历史结果')
    out.mkdir(parents=True)
    rows=[]
    for i,s in enumerate(config['samples']):
        source=ROOT/s['file']
        if sha(source)!=s['sourceSha256']:raise ValueError('源文件SHA变化')
        original=cv2.imdecode(np.frombuffer(source.read_bytes(),np.uint8),0)
        x,y,x1,y1=s['crop'];reference=original[y:y1,x:x1];assert reference.shape==(256,256)
        ref_name=s['id']+'_reference.png';cv2.imwrite(str(out/ref_name),reference)
        for j,mode in enumerate(config['degradations']):
            for k,strength in enumerate(config['strengths']):
                seed=config['seed']+i*100+j*10+k;case=f"{s['id']}_{mode}_{k}"
                damaged,params=degrade(reference,mode,seed,strength)
                input_name=case+'_input.png';cv2.imwrite(str(out/input_name),damaged)
                comparisons=[('reference',reference),('input',damaged)]
                order=np.random.default_rng(seed).permutation(config['methods']).tolist()
                for method in order:
                    start=time.perf_counter();diagnostics={};error=None
                    try:
                        if method=='adaptive_joint':
                            output,diagnostics=AdaptiveRubbingRestorer().restore(damaged);applicability='applied'
                        else:output,applicability=apply_method(damaged,method)
                        ms=(time.perf_counter()-start)*1000
                        filename=case+'_'+method+'.png';cv2.imwrite(str(out/filename),output)
                        measured=compute_metrics(reference,output)
                        a=cv2.Canny(reference,80,160)>0;b=cv2.Canny(output,80,160)>0
                        edge=2*np.count_nonzero(a&b)/max(1,np.count_nonzero(a)+np.count_nonzero(b))
                        psnr=measured['psnr'] if np.isfinite(measured['psnr']) else None
                        row={'psnr':psnr,'perfectMatch':not np.isfinite(measured['psnr']),'ssim':measured['ssim'],'edgeF1':edge,'output':filename,'outputSha256':sha(out/filename)}
                        comparisons.append((method,output))
                    except Exception as exc:
                        error=type(exc).__name__+': '+str(exc);ms=(time.perf_counter()-start)*1000;applicability='failed'
                        row={'psnr':None,'ssim':None,'edgeF1':None,'output':None,'outputSha256':None,'perfectMatch':False}
                    rows.append({'sampleId':s['id'],'dynasty':s['dynasty'],'split':s['split'],'caseId':case,'degradation':mode,'strength':strength,
                        'seed':seed,'degradationParameters':params,'method':method,'applicability':applicability,'processingMs':ms,'error':error,
                        'sourceSha256':s['sourceSha256'],'crop':s['crop'],'reference':ref_name,'referenceSha256':sha(out/ref_name),
                        'input':input_name,'inputSha256':sha(out/input_name),'algorithmVersion':VERSION if method=='adaptive_joint' else 'fixed-baselines-v2-label-free',
                        'diagnostics':diagnostics,**row})
                sheet=Image.new('RGB',(256*4,282*3),'#ece8df');draw=ImageDraw.Draw(sheet)
                for idx,(label,pixels) in enumerate(comparisons):
                    xx,yy=idx%4*256,idx//4*282;sheet.paste(Image.fromarray(pixels).convert('RGB'),(xx,yy+24));draw.text((xx+5,yy+5),label,fill='black')
                sheet.save(out/('comparison_'+case+'.jpg'),quality=85)
        print(s['id'],len(rows),flush=True)
    summary=grouped_summary(rows,config['seed'])
    result={'config':config,'sources':config['samples'],'rows':rows,'summary':summary,
        'environment':{'python':platform.python_version(),'numpy':np.__version__,'opencv':cv2.__version__,'scikitImage':skimage.__version__,
                       'gitSha':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                       'codeSha256':{f:sha(ROOT/f) for f in ['algorithm_engine.py','degradation_analysis.py','experiments/run_v2.py','experiments/run_ablation.py']}}}
    (out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),'utf8')
    for filename,entries in [('results.csv',rows),('summary.csv',summary)]:
        with (out/filename).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(entries[0]));writer.writeheader();writer.writerows(entries)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--output',default='experiments/results/2026-10-17-v2')
    args=parser.parse_args();path=ROOT/'experiments/config-v2.json'
    if args.prepare:
        path.write_text(json.dumps(make_config(),ensure_ascii=False,indent=2),'utf8')
    else:
        result=run(json.loads(path.read_text('utf8')),ROOT/args.output)
        print(json.dumps(result['summary'],ensure_ascii=False,indent=2))
