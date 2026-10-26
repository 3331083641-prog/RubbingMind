"""Verify stored image hashes/metrics and replay historical snapshot pixels read-only.

Writes only the requested report and a new temporary code copy. Never overwrites
results.json, derived files, source images or the current application modules.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cv2
import numpy as np
from algorithm_engine import compute_metrics

BATCHES = ('2026-10-17-v2', '2026-10-17-v2-text')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


REPLAY = r'''
import hashlib,json,sys
from pathlib import Path
import cv2,numpy as np
from experiments.run_ablation import apply_method
from degradation_analysis import AdaptiveRubbingRestorer
cv2.setNumThreads(1)
root=Path(sys.argv[1]);data=json.loads((root/'results.json').read_text(encoding='utf-8'))
groups={}
for row in data['rows']:
 if not row.get('error') and row.get('output'):
  groups.setdefault((row['sampleId'],row['method']),[]).append(row)
checks=[]
for key,rows in sorted(groups.items()):
 row=min(rows,key=lambda r:hashlib.sha256((r['caseId']+'|'+r['method']).encode()).hexdigest())
 image=cv2.imread(str(root/row['input']),cv2.IMREAD_GRAYSCALE)
 stored=cv2.imread(str(root/row['output']),cv2.IMREAD_GRAYSCALE)
 if row['method']=='adaptive_joint':out,_=AdaptiveRubbingRestorer().restore(image)
 else:out,_=apply_method(image,row['method'])
 checks.append({'sampleId':row['sampleId'],'method':row['method'],'caseId':row['caseId'],'equal':bool(np.array_equal(out,stored))})
print(json.dumps({'checked':len(checks),'equal':sum(c['equal'] for c in checks),'mismatches':[c for c in checks if not c['equal']]}))
'''


def verify(batch, replay=False, temp_root=None):
    folder=ROOT/'experiments/results'/batch
    data=json.loads((folder/'results.json').read_text(encoding='utf-8'))
    assets={};errors=[];metric_n=0;max_delta={'psnr':0.,'ssim':0.,'edgeF1':0.}
    for row in data['rows']:
        for role in ('reference','input','output'):
            if row.get(role):
                previous=assets.setdefault(row[role],row.get(role+'Sha256'))
                if previous!=row.get(role+'Sha256'):errors.append('inconsistent recorded hash: '+row[role])
    for filename,expected in assets.items():
        path=(folder/filename).resolve()
        if path.parent!=folder.resolve() or not path.is_file() or sha(path)!=expected:
            errors.append('missing / mismatched image: '+filename)
    for source in data.get('sources',[]):
        path=ROOT/source['file']
        if not path.is_file() or sha(path)!=source['sourceSha256']:
            errors.append('source image mismatch: '+source['id'])
    for row in data['rows']:
        if row.get('error') or not row.get('output'):continue
        reference=cv2.imread(str(folder/row['reference']),cv2.IMREAD_GRAYSCALE)
        output=cv2.imread(str(folder/row['output']),cv2.IMREAD_GRAYSCALE)
        if reference is None or output is None:continue
        values=compute_metrics(reference,output)
        a=cv2.Canny(reference,80,160)>0;b=cv2.Canny(output,80,160)>0
        values['edgeF1']=float(2*np.count_nonzero(a&b)/max(1,np.count_nonzero(a)+np.count_nonzero(b)))
        for name,value in values.items():
            stored=row.get(name)
            if not math.isfinite(value):
                if stored is not None:errors.append('perfect-match metric mismatch: '+row['caseId'])
            elif stored is None or abs(value-stored)>1e-9:
                errors.append('metric mismatch: '+row['caseId']+'/'+row['method']+'/'+name)
            if stored is not None and math.isfinite(value):max_delta[name]=max(max_delta[name],abs(value-stored))
        metric_n+=1
    result={'batch':batch,'rows':len(data['rows']),'imageFilesVerified':len(assets),
            'sourceImagesVerified':len(data.get('sources',[])),'metricsRecomputed':metric_n,
            'maximumAbsoluteMetricDelta':max_delta,'errors':errors,
            'selectionRule':'minimum SHA256(caseId|method) per artifact and method; no performance selection'}
    if replay:
        with tempfile.TemporaryDirectory(prefix='snapshot-replay-',dir=temp_root) as name:
            copy=Path(name);(copy/'experiments').mkdir()
            (copy/'experiments/__init__.py').write_text('',encoding='utf-8')
            snapshot=folder/'source_snapshot'
            for rel in ['algorithm_engine.py','degradation_analysis.py','experiments/run_ablation.py']:
                target=copy/rel;target.write_bytes((snapshot/rel).read_bytes())
            (copy/'replay.py').write_text(REPLAY,encoding='utf-8')
            env=dict(os.environ,PYTHONUTF8='1',PYTHONPATH=str(copy))
            p=subprocess.run([sys.executable,str(copy/'replay.py'),str(folder)],cwd=copy,env=env,capture_output=True,text=True,encoding='utf-8')
            if p.returncode:raise RuntimeError('Snapshot replay failed: '+p.stderr[-1200:])
            result['snapshotReplay']=json.loads(p.stdout.strip().splitlines()[-1])
    result['ok']=not errors and (not replay or not result['snapshotReplay']['mismatches'])
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--replay',action='store_true')
    parser.add_argument('--temp-root',type=Path)
    args=parser.parse_args()
    cv2.setNumThreads(1)
    report={'batches':[verify(b,args.replay,args.temp_root) for b in BATCHES],
            'historicalResultsRewritten':False,'runtimeTimingReproduced':False,
            'scope':'stored-file provenance, paired metric recomputation, selected historical-code pixel replay; not ancient-glyph accuracy'}
    report['ok']=all(b['ok'] for b in report['batches'])
    text=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text+'\n',encoding='utf-8')
    print(text)
    raise SystemExit(0 if report['ok'] else 1)
