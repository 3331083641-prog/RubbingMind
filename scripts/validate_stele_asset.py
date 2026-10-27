"""Independent GLB binary audit: indices, normals, UVs, material coverage.
No renderer can hide an invalid accessor or missing embedded PBR resource.
"""
from pathlib import Path
import json
import struct
import hashlib
import io
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'apps/web/public/assets/stele/model3d/final'
MODEL=ASSETS/'stele-final.glb'

def run(report_path=None):
    raw=MODEL.read_bytes(); magic,version,length=struct.unpack_from('<III',raw)
    assert magic==0x46546c67 and version==2 and length==len(raw)
    jl,jt=struct.unpack_from('<II',raw,12); assert jt==0x4e4f534a
    doc=json.loads(raw[20:20+jl]); offset=20+jl
    bl,bt=struct.unpack_from('<II',raw,offset); assert bt==0x004e4942
    binary=raw[offset+8:offset+8+bl]
    types={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
    sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
    def accessor(index):
        a=doc['accessors'][index]; v=doc['bufferViews'][a['bufferView']]
        start=v.get('byteOffset',0)+a.get('byteOffset',0); dt=np.dtype(types[a['componentType']]); components=sizes[a['type']]
        stride=v.get('byteStride',dt.itemsize*components)
        return np.ndarray(shape=(a['count'],components),dtype=dt,buffer=binary,offset=start,strides=(stride,dt.itemsize))
    results=[]; total=0
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            attrs=p['attributes']; vertices=accessor(attrs['POSITION']); normals=accessor(attrs['NORMAL']); uv=accessor(attrs['TEXCOORD_0']); uv1=accessor(attrs['TEXCOORD_1'])
            indices=accessor(p['indices']).reshape(-1); assert len(indices)%3==0 and indices.max()<len(vertices)
            assert all(np.isfinite(a).all() for a in [vertices,normals,uv,uv1])
            assert np.all((uv>=0)&(uv<=1)) and np.all((uv1>=0)&(uv1<=1))
            assert np.all(np.abs(np.linalg.norm(normals,axis=1)-1)<.005)
            tri=vertices[indices.reshape(-1,3)]
            area=np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
            assert np.all(area>1e-12),'degenerate geometry'
            m=doc['materials'][p['material']]; pb=m['pbrMetallicRoughness']
            assert pb['metallicFactor']==0 and 'baseColorTexture' in pb and 'metallicRoughnessTexture' in pb
            assert 'normalTexture' in m and 'occlusionTexture' in m
            assert m['occlusionTexture'].get('texCoord')==1
            assert m.get('alphaMode','OPAQUE')=='OPAQUE' and not m.get('doubleSided',False)
            total+=len(indices)//3
            results.append({'vertices':len(vertices),'triangles':len(indices)//3,'index_max':int(indices.max()),'UV0':True,'UV1':True,'normal_unit':True,'zero_area_faces':0,'PBR_complete':True})
    images=[]
    for item in doc['images']:
        assert 'bufferView' in item and 'uri' not in item
        v=doc['bufferViews'][item['bufferView']]; payload=binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
        image=Image.open(io.BytesIO(payload)); image.verify()
        images.append({'mime':item['mimeType'],'pixels':list(image.size),'bytes':len(payload)})
    report={'pass':True,'model':MODEL.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'triangles':total,'primitives':results,'embedded_images':images,'external_image_uris':0}
    if report_path is not None:
        out = Path(report_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        # LF-only JSON so CI/pytest never dirty tracked CRLF/LF on Windows
        out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))
    return report

if __name__ == '__main__':
    run(ROOT / 'screenshots/stele-final/asset-validation.json')
