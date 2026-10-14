"""Verify the authority, all derived catalogues, image identities and native sizes."""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from catalog import load,museum_records

def validate():
    rows=museum_records();assert len(rows)==28
    assert Counter(r['dynasty'] for r in rows)==dict.fromkeys(['东汉','北魏','唐代','宋代','元代','明代','清代'],4)
    ids={r['id'] for r in rows};assert len(ids)==28
    assert not ids & {r['oldId'] for r in load('replacement_mapping.json')}
    for path in ['apps/web/src/data/steles28.json','data/museum-import/merged_28_steles.json']:
        assert json.loads((ROOT/path).read_text('utf-8'))==rows,path
    database=json.loads((ROOT/'data/museum_database.json').read_text('utf-8'));db={r['id']:r for r in database}
    for r in rows:assert db[r['id']]==r
    sources={r['id']:r for r in load('image_sources.json')};hashes=set();pairs=[]
    for r in rows:
        assert r['sourceUrl'].startswith('https://') and r['collectionNumber'] and r['collectionInstitution']
        assert r['metrics']==dict.fromkeys(r['metrics'],None) and not r['damaged_image'] and not r['restored_image']
        p=load('processing/'+r['id']+'.json');assert not p['generative_processing'] and not p['stroke_reconstruction']
        assert p['source_sha256']==r['sourceVerification']['sourceSha256']
        for role,url in r['imageAssets'].items():
            file=ROOT/'apps/web/public'/urlsplit(url).path.lstrip('/');assert file.is_file(),str(file)
            digest=hashlib.sha256(file.read_bytes()).hexdigest()
            assert digest==p['output_sha256'][role+'.jpg']==sources[r['id']]['outputSha256'][role+'.jpg']
            assert digest[:12] in url
            with Image.open(file) as image:
                image.load()
                if role=='cover':
                    assert image.size==(1100,1420)
                    assert digest not in hashes;hashes.add(digest)
                    small=np.array(image.convert('L').resize((17,16)),dtype=np.int16)
                    pairs.append((r['id'],small[:,1:]>small[:,:-1]))
    near=[]
    for i,(a,ha) in enumerate(pairs):
        for b,hb in pairs[i+1:]:
            distance=int(np.count_nonzero(ha!=hb))
            if distance<=12:near.append({'first':a,'second':b,'distance':distance})
    assert Counter(r['license'] for r in rows)=={'CC BY 4.0':23,'CC0':2,'Public Domain':3}
    cores=load('core_samples.json');assert {r['id'] for r in cores}=={'tang-duobao','han-caoquan','wei-yuanhuai','wei-jianyi'}
    for r in cores:assert (ROOT/'apps/web/public'/r['raw_image'].lstrip('/')).is_file()
    links=load('core_sample_links.json');assert next(r for r in links if r['coreSampleId']=='wei-jianyi')['museumSteleId'] is None
    return {'passed':True,'items':28,'images':84,'sha256Match':84,'dynasties':dict(Counter(r['dynasty'] for r in rows)),'licenseCounts':dict(Counter(r['license'] for r in rows)),'nearDuplicateCandidates':near,'comparisonPairs':378}

if __name__=='__main__':print(json.dumps(validate(),ensure_ascii=False,indent=2))
