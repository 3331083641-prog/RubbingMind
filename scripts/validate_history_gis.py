"""Validate geographic containment without heavyweight GIS dependencies."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path): return json.loads((ROOT/path).read_text(encoding='utf-8'))
def in_ring(point,ring):
    x,y=point; inside=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: inside=not inside
    return inside
def contains(point,geom):
    polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
    return any(in_ring(point,polygon[0]) and not any(in_ring(point,h) for h in polygon[1:]) for polygon in polys)

def validate():
    provinces=load('apps/web/public/assets/gis/china-provinces.cgcs2000.geojson')['features']
    admin=load('data/history/coordinate-regions.geojson')['features']
    result=[]
    for id in ['tang-duobao','han-caoquan','wei-yuanhuai','wei-jianyi']:
        d=load(f'data/history/{id}.json')
        for p in d['locations']:
            if p['longitude'] is None:
                result.append({'stele':id,'place':p['id'],'status':'null / text-only'});continue
            coord=[p['longitude'],p['latitude']]
            if p['province']:
                province=next(f for f in provinces if f['properties']['name']==p['province'])
                assert contains(coord,province['geometry']), f'{id}/{p["id"]} is outside {p["province"]}'
            shape=next((f for f in admin if f['properties']['locationId']==p['id']),None)
            if shape: assert contains(coord,shape['geometry']), f'{p["id"]} is outside its admin region'
            result.append({'stele':id,'place':p['id'],'coordinate':coord,'province':p['province'],'status':'contained','precision':p['precision']})
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=='__main__':validate()
