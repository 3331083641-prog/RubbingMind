"""Read-only allowlisted experiment catalogue and verifiable image serving."""
import csv
import hashlib
import io
import json
from functools import lru_cache
from pathlib import Path
from catalog import BASE

RESULTS=BASE/'experiments/results'
METRICS_NOTE='本批次只保留了数值，没有保存任何图像，无法提供图像对比'
DERIVED='derived/applied_status.json'
# Display names override experiment IDs whose wording overstates the protocol.
# The stored ID stays unchanged so historical files and exports remain addressable.
DISPLAY={
    'heldout-v20-v21-2026-10-18':{
        'displayName':'同批复测 v2.1（v2.0 对照，2026-10-18）','heldOut':False,
        'protocolNote':'不是留出评测：14 件文物与 2026-10-17-v2-text 批次相同（源图 SHA 一致，song_03_daguan 裁切完全重叠、tang_04_xuanmita 重叠 79.5%），且 v2.1 在该批误差分析之后修改。见 docs/product-upgrade/AUDIT_EVALUATION.md E-01。'},
}


@lru_cache(maxsize=8)
def _read(path,stamp):
    result=json.loads(Path(path).read_text('utf8'))
    assert isinstance(result['rows'],list) and isinstance(result['summary'],list)
    return result


def _entry(path, data):
    config=data.get('config') if isinstance(data.get('config'), dict) else {}
    experiment_id=config.get('experimentId') or data.get('experimentId')
    sources=data.get('sources') if isinstance(data.get('sources'), list) else None
    samples=data.get('samples') if isinstance(data.get('samples'), list) else []
    if not experiment_id or not isinstance(data.get('rows'), list):
        return None
    image_names=[row.get(key) for row in data['rows'] for key in ('input','reference','output') if row.get(key)]
    images_available=sources is not None and bool(image_names)
    limitations=list(config.get('limitations') or [])
    for note in (data.get('samplingRule'), data.get('notThePreviousBatch'), data.get('pairedReference')):
        if note and note not in limitations:
            limitations.append(note)
    if not images_available and METRICS_NOTE not in limitations:
        limitations.append(METRICS_NOTE)
    display=DISPLAY.get(experiment_id,{})
    if display.get('protocolNote') and display['protocolNote'] not in limitations:
        limitations.insert(0,display['protocolNote'])
    derived=path.parent/DERIVED
    return {'id':experiment_id,'displayName':display.get('displayName',experiment_id),'heldOut':display.get('heldOut'),
        'appliedStatusAvailable':derived.is_file(),'directory':path.parent.name,'rowCount':len(data['rows']),
        'sampleCount':len(sources) if sources is not None else len(samples),'summary':data['summary'],
        'limitations':limitations,'imageComparisonAvailable':images_available,'metricsOnly':not images_available,
        'historicalWarning':'历史joint根据生成器退化标签选陷波，有先验泄漏；仅作历史记录。' if path.parent.name=='2026-10-15' else None}


def batches():
    result=[]
    for path in sorted(RESULTS.glob('*/results.json')):
        data=_read(str(path),path.stat().st_mtime_ns)
        entry=_entry(path, data)
        if entry is not None:
            result.append(entry)
    return result


def batch(experiment_id):
    entry=next((r for r in batches() if r['id']==experiment_id),None)
    if entry is None:return None
    path=RESULTS/entry['directory']/'results.json'
    data=dict(_read(str(path),path.stat().st_mtime_ns))
    if not isinstance(data.get('config'), dict):
        data['config']={'experimentId':data.get('experimentId'),'referenceNote':data.get('pairedReference') or METRICS_NOTE,'limitations':entry['limitations']}
    if not isinstance(data.get('sources'), list):
        data['sources']=[]
    derived=path.parent/DERIVED
    if derived.is_file():
        status=json.loads(derived.read_text('utf8'))
        data['appliedStatus']={k:status.get(k) for k in ('criterion','imagesAvailable','note','summaryByMethod','summaryBySplitMethod','summaryByMethodDegradation','sourceResultsSha256')}
    return {**data,'registry':entry}


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
    payload=export_payload(experiment_id,kind)
    if payload is None:return None
    return payload


def _csv_bytes(rows):
    buffer=io.StringIO()
    fields=list(dict.fromkeys(key for row in rows for key in row))
    writer=csv.DictWriter(buffer,fieldnames=fields,extrasaction='ignore',lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row.get(key) for key in fields})
    return buffer.getvalue().encode('utf-8-sig')


def export_payload(experiment_id,kind):
    data=batch(experiment_id)
    if data is None or kind not in ('results.json','results.csv','summary.csv','applied_status.csv','applied_status.json'):return None
    path=RESULTS/data['registry']['directory']/kind
    if kind.startswith('applied_status'):
        path=RESULTS/data['registry']['directory']/'derived'/kind
        return (path.read_bytes(),'text/csv' if kind.endswith('.csv') else 'application/json') if path.is_file() else None
    if path.is_file():
        return path.read_bytes(),'text/csv' if kind.endswith('.csv') else 'application/json'
    if kind=='results.json':
        stored=dict(data)
        stored.pop('registry',None)
        return json.dumps(stored,ensure_ascii=False,indent=2).encode('utf-8'),'application/json'
    rows=data['summary'] if kind=='summary.csv' else data['rows']
    return _csv_bytes(rows),'text/csv'
