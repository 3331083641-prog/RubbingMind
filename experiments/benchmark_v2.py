"""Measure whole-pipeline peak resident memory in a fresh subprocess per size."""
import argparse
import ctypes
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def peak_bytes():
    if os.name=='nt':
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('faults',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in ('peakWorking','working','peakPaged','paged','peakNonPaged','nonPaged','pagefile','peakPagefile')]
        c=Counters();c.cb=ctypes.sizeof(c)
        current=ctypes.windll.kernel32.GetCurrentProcess
        current.restype=wintypes.HANDLE
        measure=ctypes.windll.psapi.GetProcessMemoryInfo
        measure.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
        measure.restype=wintypes.BOOL
        if not measure(current(),ctypes.byref(c),c.cb):raise ctypes.WinError()
        return c.peakWorking
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)


def worker(h,w):
    sys.path.insert(0,str(ROOT))
    import numpy as np
    from algorithm_engine import algorithm_engine
    rng=np.random.default_rng(20261017)
    image=np.clip(80+rng.normal(0,12,(h,w)),0,255).astype(np.uint8)
    start=time.perf_counter();result=algorithm_engine.process_rubbing(image,filter_type='adaptive',random_seed=20261017)
    return {'sourceShape':[h,w],'workingImage':result['working_image'],'elapsedSeconds':time.perf_counter()-start,
            'peakResidentMiB':peak_bytes()/1024**2,'metrics':result['metrics'],'seed':20261017,
            'measurement':'fresh-process lifetime peak RSS includes imports, arrays, PNG and base64 output'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--worker',nargs=2,type=int);args=parser.parse_args()
    if args.worker:print(json.dumps(worker(*args.worker)))
    else:
        rows=[]
        for h,w in [(512,768),(1024,1536),(2000,2400)]:
            result=subprocess.check_output([sys.executable,__file__,'--worker',str(h),str(w)],text=True,cwd=ROOT)
            rows.append(json.loads(result))
        output={'platform':platform.platform(),'python':platform.python_version(),'rows':rows,'limitations':'单机单次合成噪声输入；非并发服务压力测试。工作副本上限160万像素，非历史真值。'}
        path=ROOT/'experiments/results/2026-10-17-v2/performance.json';path.write_text(json.dumps(output,ensure_ascii=False,indent=2),'utf8');print(json.dumps(output,ensure_ascii=False))
