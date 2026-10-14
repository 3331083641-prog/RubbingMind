"""Blender 5.1 reconstruction, closed sculpted volumes, UV atlas and GLB.

Run after prepare_textures.py:
blender --background --python design/blender/stele-final/build_stele.py
Coordinate authoring follows web dimensions (X width, Y height, Z front).
At export, authoring coordinates are converted to Blender Z-up exactly once.
"""
import bpy
import bmesh
import numpy as np
import json
import math
import re
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'apps/web/public/assets/stele/model3d/final'
with np.load(Path(__file__).parent / 'sculpt_fields.npz') as stored_fields:
    FIELDS = {key:stored_fields[key] for key in stored_fields.files}
ATLAS = json.loads((OUT/'atlas.json').read_text())
MODELDIR = Path(__file__).parent
CONFIG=(ROOT/'apps/web/src/config/steleDimensions.ts').read_text(encoding='utf-8')
def dimensions(section):
    text=re.search(r'\b'+section+r':\s*\{([^}]+)',CONFIG).group(1)
    return {key:float(value) for key,value in re.findall(r'(\w+):\s*(-?\d+(?:\.\d+)?)',text)}
BODY=dimensions('body'); CROWN=dimensions('crown'); PANEL=dimensions('panel')

def sample(field, u, v):
    h,w=field.shape
    x=np.clip(u*(w-1),0,w-1); y=np.clip((1-v)*(h-1),0,h-1)
    xi,yi=int(x),int(y); xf,yf=x-xi,y-yi
    return float((1-yf)*((1-xf)*field[yi,xi]+xf*field[yi,min(xi+1,w-1)])+
                 yf*((1-xf)*field[min(yi+1,h-1),xi]+xf*field[min(yi+1,h-1),min(xi+1,w-1)]))

def uv(name,u,v):
    x0,y0,x1,y1=ATLAS['regions'][name]; p=ATLAS['padding']; w,h=ATLAS['size']
    return ((x0+p+u*(x1-x0-2*p))/w, 1-(y0+p+(1-v)*(y1-y0-2*p))/h)

class Volume:
    def __init__(self,name):
        self.name=name; self.verts=[]; self.faces=[]; self.uvs=[]; self.lookup={}; self.ao_uvs=[]; self.surfaces=0; self.flat_faces=set()
        self.row=['SteleBody_ClosedRecess','TwinDragonCrown_ClosedSculpt','BearingPlinth','ScrollWaist','WaistCornice','LotusSupport','SocketCoping'].index(name)
    def ao(self,u,v,col):
        return ((col+.02+u*.96)/6,1-(self.row+.02+(1-v)*.96)/7)
    def vertex(self,p):
        key=tuple(round(float(k),7) for k in p)
        if key not in self.lookup:
            self.lookup[key]=len(self.verts); self.verts.append(p)
        return self.lookup[key]
    def surface(self,nx,ny,fn,region,reverse=False):
        col=self.surfaces; self.surfaces+=1
        ids=[]
        for j in range(ny+1):
            row=[]
            for i in range(nx+1): row.append(self.vertex(fn(i/nx,j/ny)))
            ids.append(row)
        for j in range(ny):
            for i in range(nx):
                f=[ids[j][i],ids[j][i+1],ids[j+1][i+1],ids[j+1][i]]
                t=[uv(region,i/nx,j/ny),uv(region,(i+1)/nx,j/ny),uv(region,(i+1)/nx,(j+1)/ny),uv(region,i/nx,(j+1)/ny)]
                # Collapse the arch tip into triangles without degenerate faces.
                at=[self.ao(i/nx,j/ny,col),self.ao((i+1)/nx,j/ny,col),self.ao((i+1)/nx,(j+1)/ny,col),self.ao(i/nx,(j+1)/ny,col)]
                unique=[]; tex=[]; ambient=[]
                for a,b,c in zip(f,t,at):
                    if a not in unique: unique.append(a); tex.append(b); ambient.append(c)
                if len(unique)<3: continue
                if reverse: unique.reverse(); tex.reverse(); ambient.reverse()
                self.faces.append(unique); self.uvs.append(tex); self.ao_uvs.append(ambient)
    def cap(self,nx,nz,fn,region):
        col=self.surfaces; self.surfaces+=1
        border=[(i/nx,0) for i in range(nx)]+[(1,j/nz) for j in range(nz)]+[(1-i/nx,1) for i in range(nx)]+[(0,1-j/nz) for j in range(nz)]
        inner=[(.5+(u-.5)*.92,.5+(v-.5)*.92) for u,v in border]
        outer_ids=[self.vertex(fn(u,v)) for u,v in border]; inner_ids=[self.vertex(fn(u,v)) for u,v in inner]
        center=self.vertex(fn(.5,.5)); count=len(border)
        for i in range(count):
            j=(i+1)%count
            coords=[border[i],border[j],inner[j],inner[i]]
            self.faces.append([outer_ids[i],outer_ids[j],inner_ids[j],inner_ids[i]])
            self.uvs.append([uv(region,u,v) for u,v in coords]); self.ao_uvs.append([self.ao(u,v,col) for u,v in coords])
            coords=[inner[i],inner[j],(.5,.5)]
            self.flat_faces.add(len(self.faces))
            self.faces.append([inner_ids[i],inner_ids[j],center]); self.uvs.append([uv(region,u,v) for u,v in coords]); self.ao_uvs.append([self.ao(u,v,col) for u,v in coords])
    def finish(self,material):
        mesh=bpy.data.meshes.new(self.name); mesh.from_pydata(self.verts,[],self.faces); mesh.update()
        layer=mesh.uv_layers.new(name='StoneAtlas')
        # Blender 5's UV collection wrapper is expensive to construct per loop.
        # Bulk writes keep authoring linear even for dense relief surfaces.
        layer.data.foreach_set('uv',np.asarray([coord for face in self.uvs for coord in face],dtype=np.float32).ravel())
        ambient=mesh.uv_layers.new(name='AmbientOcclusion')
        ambient.data.foreach_set('uv',np.asarray([coord for face in self.ao_uvs for coord in face],dtype=np.float32).ravel())
        mesh.uv_layers.active_index=0
        smooth=np.ones(len(mesh.polygons),dtype=bool)
        smooth[list(self.flat_faces)]=False
        mesh.polygons.foreach_set('use_smooth',smooth)
        obj=bpy.data.objects.new(self.name,mesh); bpy.context.collection.objects.link(obj)
        mesh.materials.append(material)
        bm=bmesh.new(); bm.from_mesh(mesh); bmesh.ops.recalc_face_normals(bm,faces=bm.faces); bm.to_mesh(mesh); bm.free()
        print('BUILT',self.name,len(self.verts),len(self.faces),flush=True)
        return obj

def rounded(p,center,size,r):
    q=np.array(p)-center; half=np.array(size)/2; inner=half-r
    c=np.clip(q,-inner,inner); d=q-c; norm=np.linalg.norm(d)
    if norm>1e-9: q=c+d*r/norm
    return q+center

def box(name,center,size,mat,front='stone',back='stone',left='stone',right='stone',nx=64,ny=24,nz=12,sculpt=None,top='stone'):
    cx,cy,cz=center; w,h,d=size; vol=Volume(name)
    def point(face,u,v):
        if face=='front': p=(cx+(u-.5)*w,cy+(v-.5)*h,cz+d/2)
        elif face=='back': p=(cx+(.5-u)*w,cy+(v-.5)*h,cz-d/2)
        elif face=='left': p=(cx-w/2,cy+(v-.5)*h,cz+(u-.5)*d)
        elif face=='right': p=(cx+w/2,cy+(v-.5)*h,cz+(.5-u)*d)
        elif face=='top': p=(cx+(u-.5)*w,cy+h/2,cz+(.5-v)*d)
        else: p=(cx+(u-.5)*w,cy-h/2,cz+(v-.5)*d)
        p=rounded(p,np.array(center),size,min(.011,h*.14))
        if name=='SteleBody_ClosedRecess':
            # Same world-space edge spalls on all adjacent faces, welded shut.
            strength=max(0,min(1,(abs(p[0])-.54)/.10))**2
            sites=[(.92,.027,.035),(1.55,.016,.045),(2.29,.025,.055)] if p[0]<0 else [(1.03,.023,.05),(1.67,.025,.04),(2.38,.018,.035)]
            loss=sum(depth*math.exp(-((p[1]-y)/span)**2) for y,depth,span in sites)
            p[0]-=math.copysign(strength*loss,p[0])
        if name=='BearingPlinth' and face=='bottom':
            p[1]+=.014 if min(u,1-u,v,1-v)>1e-6 else 0
        # All faces share the same spatial wear function, so edges stay watertight.
        grain=.00045*math.sin(p[0]*97+p[1]*31+p[2]*53)*math.sin(p[0]*29-p[1]*83)
        axis={'front':2,'back':2,'left':0,'right':0,'top':1,'bottom':1}[face]
        sign=1 if face in ('front','right','top') else -1
        edge=min(u,1-u,v,1-v)
        if sculpt and face in ('front','back','left','right'):
            p[axis]+=sign*sculpt(face,u,v)*min(1,edge*60)
        # Relief vanishes at shared edges; geometric wear is already in bevels.
        if face not in ('top','bottom'):
            p[axis]+=grain*min(1,edge*80)
        return tuple(p)
    for f,a,b,region in [('front',nx,ny,front),('back',nx,ny,back),('left',nz,ny,left),('right',nz,ny,right)]:
        vol.surface(a,b,lambda u,v,f=f:point(f,u,v),region)
    vol.cap(nx,nz,lambda u,v:point('top',u,v),top)
    vol.cap(nx,nz,lambda u,v:point('bottom',u,v),'bottom')
    return vol.finish(mat)

def material():
    mat=bpy.data.materials.new('Weathered limestone / complete PBR atlas'); mat.use_nodes=True; mat.use_backface_culling=True
    n=mat.node_tree.nodes; l=mat.node_tree.links; bs=n.get('Principled BSDF')
    bs.inputs['Metallic'].default_value=0; bs.inputs['Roughness'].default_value=.9
    for filename,space,kind in [('stone_basecolor.jpg','sRGB','color'),('stone_normal.png','Non-Color','normal'),('stone_orm.png','Non-Color','orm')]:
        image=bpy.data.images.load(str(OUT/filename)); image.colorspace_settings.name=space
        tex=n.new('ShaderNodeTexImage'); tex.image=image; tex.label=filename; tex.interpolation='Linear'; tex.extension='EXTEND'
        if kind=='color': l.new(tex.outputs['Color'],bs.inputs['Base Color'])
        elif kind=='normal':
            norm=n.new('ShaderNodeNormalMap'); norm.inputs['Strength'].default_value=.65; l.new(tex.outputs['Color'],norm.inputs['Color']); l.new(norm.outputs['Normal'],bs.inputs['Normal'])
        else:
            sep=n.new('ShaderNodeSeparateColor'); l.new(tex.outputs['Color'],sep.inputs['Color']); l.new(sep.outputs['Green'],bs.inputs['Roughness'])
            # Exporter recognizes glTF material output Occlusion input.
            tree=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree'); tree.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
            node=n.new('ShaderNodeGroup'); node.node_tree=tree; l.new(sep.outputs['Red'],node.inputs['Occlusion'])
    return mat

def crown(mat):
    r=CROWN['archRadius']; base=CROWN['yPos']; vol=Volume('TwinDragonCrown_ClosedSculpt'); nx,ny=256,128
    def face(sign,u,v):
        x=(u*2-1)*r*math.sqrt(max(0,1-v*v)); y=base+v*r
        tu=x/(2*r)+.5
        height=sample(FIELDS['crown_front' if sign>0 else 'crown_back'],tu,v)
        # Bevel the crown slab independently of the decorative dome.
        rho=math.sqrt((x/r)**2+v*v)
        bevel=.011*max(0,min(1,(rho-.973)/.027))
        z=sign*(CROWN['depth']/2-bevel+height)
        return x,y,z
    # Surface UV must be projected in X/Y, not the arch's tapered grid U.
    for sign,region in [(1,'crown_front'),(-1,'crown_back')]:
        before=len(vol.faces)
        vol.surface(nx,ny,lambda u,v,s=sign:face(s,u,v),region,reverse=sign<0)
        for k in range(before,len(vol.faces)):
            vol.uvs[k]=[uv(region,vol.verts[idx][0]/(2*r)+.5,(vol.verts[idx][1]-base)/r) for idx in vol.faces[k]]
    # Wall boundary: both arc halves plus lower seam; welded to both relief skins.
    paths=[]
    for u in (0,1): paths.append([(u,j/ny) for j in range(ny+1)])
    paths.append([(i/nx,0) for i in range(nx+1)])
    for col,path in enumerate(paths,2):
        for i in range(len(path)-1):
            u,v=path[i]; un,vn=path[i+1]
            f=[vol.vertex(face(1,u,v)),vol.vertex(face(-1,u,v)),vol.vertex(face(-1,un,vn)),vol.vertex(face(1,un,vn))]
            a=i/(len(path)-1); b=(i+1)/(len(path)-1)
            if col<4:
                a=math.asin(a)*2/math.pi; b=math.asin(b)*2/math.pi
            vol.faces.append(f); vol.uvs.append([uv('arch_edge',a,1),uv('arch_edge',a,0),uv('arch_edge',b,0),uv('arch_edge',b,1)])
            vol.ao_uvs.append([vol.ao(i/(len(path)-1),1,col),vol.ao(i/(len(path)-1),0,col),vol.ao((i+1)/(len(path)-1),0,col),vol.ao((i+1)/(len(path)-1),1,col)])
    return vol.finish(mat)

def body_sculpt(face,u,v):
    if face not in ('front','back'): return 0
    # Recess is cut into the closed slab: no independent inscription plane.
    edge=min(u,1-u,v,1-v)
    recess=-PANEL['recessDepth']*min(1,max(0,(edge-.035)/.018))
    # Four Greek-key corners are actual shallow raised stone lines.
    if face=='front':
        a=min(u,1-u); b=min(v,1-v)
        key=0
        if a<.16 and b<.09:
            for q in (.067,.10,.133):
                key=max(key,math.exp(-((a-q)/.0023)**2)*(b<q*.55),math.exp(-((b-q*.55)/.0015)**2)*(a<q))
        recess+=.0035*key
    return recess

def lotus(face,u,v):
    count=14 if face in ('front','back') else 6
    local=(u*count)%1; xx=(local-.5)*2
    # Rounded lotus lobes join the support stone, with double carved outlines.
    yy=(v-.47)*1.95
    rad=math.sqrt(xx*xx+(max(yy,0)*1.14)**2)
    outline=.007*math.exp(-((rad-.84)/.085)**2)+.004*math.exp(-((rad-.65)/.065)**2)
    raised=.006*max(0,1-rad**2)
    return outline+raised+.0014*sample(FIELDS['lotus_'+face if face in ('left','right') else 'lotus'],u,v)

def scroll(face,u,v):
    h=sample(FIELDS['scroll_'+face if face in ('left','right') else 'scroll'],u,v)
    relief=.014*max(0,min(1,(h-.28)/.3))
    return relief+.002*math.sin(u*math.pi*12)*math.sin(v*math.pi)

def audit(objects):
    report=[]
    for obj in objects:
        bm=bmesh.new(); bm.from_mesh(obj.data)
        bad=sum(not e.is_manifold for e in bm.edges); bm.free()
        obj.data.calc_loop_triangles()
        item={'name':obj.name,'vertices':len(obj.data.vertices),'triangles':len(obj.data.loop_triangles),'non_manifold_edges':bad,'uv':bool(obj.data.uv_layers),'materials':len(obj.data.materials)}
        report.append(item)
        assert bad==0, item
        assert item['uv'] and item['materials'],item
    return report

def main():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    mat=material()
    objects=[box('SteleBody_ClosedRecess',(0,BODY['yPos'],0),(BODY['width'],BODY['height'],BODY['depth']),mat,'front','back','left','right',96,160,12,body_sculpt),crown(mat)]
    t1,t2,t3=[dimensions(k) for k in ('tier1','tier2','tier3')]
    objects += [box('BearingPlinth',(0,t1['yPos'],0),(t1['width'],t1['height'],t1['depth']),mat,'plinth_front','plinth_back','plinth_left','plinth_right',nx=96,ny=10,nz=32,top='plinth_top'),
                box('ScrollWaist',(0,t2['yPos']-.018,0),(t2['width'],t2['height']-.036,t2['depth']),mat,'scroll','scroll','scroll_left','scroll_right',256,32,80,scroll),
                box('WaistCornice',(0,t2['yPos']+t2['height']/2-.018,0),(t2['width']+.07,.036,t2['depth']+.05),mat,'cornice_front','cornice_back','cornice_left','cornice_right',nx=96,ny=4,nz=32,top='cornice_top'),
                box('LotusSupport',(0,t3['yPos']-.012,0),(t3['width'],t3['height']-.024,t3['depth']),mat,'lotus','lotus','lotus_left','lotus_right',280,36,80,lotus),
                box('SocketCoping',(0,t3['yPos']+t3['height']/2-.012,0),(t3['width']-.02,.024,t3['depth']-.01),mat,'cornice_front','cornice_back','cornice_left','cornice_right',nx=96,ny=4,nz=32,top='socket_top')]
    report=audit(objects)
    # Web Y-up -> Blender Z-up; glTF exporter performs Z-up -> Y-up.
    conversion=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    for obj in objects: obj.data.transform(conversion)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    # Combine only equal material components: one material, seven closed islands.
    bpy.ops.object.join(); stone=bpy.context.object; stone.name='Stele_Final_SevenClosedVolumes'
    stone['reference_origin']='User supplied AI concept; no historical measurement claim'
    stone['inscription']='Concept glyphs from supplied image; not authenticated historical text'
    stone.data.calc_loop_triangles()
    reportdata={'blender':bpy.app.version_string,'components':report,'triangles':len(stone.data.loop_triangles),'atlas':ATLAS['size'],'height':3.3,'width':1.85,'depth':.72,'coordinate_system':'glTF Y-up +Z front','ao':'Local cavity AO packed into ORM.R; geometric AO baked on non-overlapping secondary UV by bake_ao.py'}
    (OUT/'geometry-audit.json').write_text(json.dumps(reportdata,indent=2),encoding='utf-8')
    # Embed all GLB textures; original files remain editable next to source.
    bpy.ops.export_scene.gltf(filepath=str(OUT/'stele-final.glb'),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_yup=True,export_apply=True)
    # Renderable editable scene, studio lights without an underside-occluding floor.
    scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=24
    scene.world.color=(.45,.45,.45)
    scene.view_settings.view_transform='AgX'
    for name,pos,power,size in [('Key',(3,-4,5),450,4),('Fill',(-3,-2,3),260,3),('Back',(1,4,4),420,4),('Bottom',(0,0,-3),120,3)]:
        bpy.ops.object.light_add(type='AREA',location=pos); light=bpy.context.object; light.name=name; light.data.energy=power; light.data.shape='DISK'; light.data.size=size; light.rotation_euler=(Vector((0,0,1.65))-light.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(3,-4,2.8)); cam=bpy.context.object; cam.name='StudioCamera'; cam.rotation_euler=(Vector((0,0,1.65))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=3.85; scene.camera=cam
    scene.render.resolution_x=1200; scene.render.resolution_y=1600; scene.render.resolution_percentage=100
    for im in bpy.data.images:
        if im.source=='FILE': im.pack()
    bpy.ops.wm.save_as_mainfile(filepath=str(MODELDIR/'stele-final.blend'),compress=True)
    print('STELE_AUDIT',json.dumps(reportdata))

if __name__=='__main__': main()
