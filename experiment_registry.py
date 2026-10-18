"""Read-only allowlisted experiment catalogue and verifiable image serving."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from catalog import BASE

RESULTS=BASE/'experiments/results'


@lru_cache(maxsize=8)
def _read(path,stamp):
    result=json.loads(Path(path).read_text('utf8'))
    assert isinstance(result['rows'],list) and isinstance(result['summary'],list)
    return result


def batches():
    result=[]
    for path in sorted(RESULTS.glob('*/results.json')):
        data=_read(str(path),path.stat().st_mtime_ns)
        config=data.get('config')
        sources=data.get('sources')
        # Metrics-only comparisons have no image manifest. Skip them instead of failing the catalogue.
        if not isinstance(config, dict) or 'experimentId' not in config or not isinstance(sources, list):
            continue
        result.append({'id':config['experimentId'],'directory':path.parent.name,'rowCount':len(data['rows']),
            'sampleCount':len(sources),'summary':data['summary'],'limitations':config.get('limitations',[]),
            'historicalWarning':'历史joint根据生成器退化标签选陷波，有先验泄漏；仅作历史记录。' if path.parent.name=='2026-10-15' else None})
    return result


def batch(experiment_id):
    entry=next((r for r in batches() if r['id']==experiment_id),None)
    if entry is None:return None
    path=RESULTS/entry['directory']/'results.json'
    return {**_read(str(path),path.stat().st_mtime_ns),'registry':entry}


def asset(experiment_id,filename):
    data=batch(experiment_id)
    if data is None:return None
    root=(RESULTS/data['registry']['directory']).resolve()
    path=(root/filename).resolve()
    if path.parent!=root:return None
    expected={}
    for row in data['rows']:
        for key in ['input','reference','output']:
            if row.get(key):expected[row[key]]=row.get(key+'Sha256')
    if filename not in expected:return None
    if not path.is_file():return None
    if expected[filename] and hashlib.sha256(path.read_bytes()).hexdigest()!=expected[filename]:
        raise ValueError('实验影像SHA-256不匹配')
    return path


def export_file(experiment_id,kind):
    data=batch(experiment_id)
    if data is None or kind not in ('results.json','results.csv','summary.csv'):return None
    return RESULTS/data['registry']['directory']/kind
