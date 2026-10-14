"""Actual Cycles geometric AO bake on non-overlapping secondary UVs.
Re-export and save the same editable model with all runtime maps embedded.
"""
import bpy
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'apps/web/public/assets/stele/model3d/final'
BLEND=Path(__file__).parent/'stele-final.blend'
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
stone=bpy.data.objects['Stele_Final_SevenClosedVolumes']
mat=stone.data.materials[0]; nodes=mat.node_tree.nodes; links=mat.node_tree.links
mat.use_backface_culling=True
scene=bpy.context.scene; scene.render.engine='CYCLES'; scene.cycles.samples=12
scene.cycles.max_bounces=1; scene.render.bake.margin=6; scene.render.bake.use_clear=True
# Restore external originals after packed file reload; bake/export current atlas.
for image in list(bpy.data.images):
    candidate=OUT/Path(image.filepath).name
    if candidate.exists() and image.source=='FILE':
        if image.packed_file: image.unpack(method='REMOVE')
        image.filepath=str(candidate); image.reload()
ao=bpy.data.images.new('stone_geometric_ao',width=2048,height=2048,alpha=False)
ao.colorspace_settings.name='Non-Color'
target=nodes.new('ShaderNodeTexImage'); target.image=ao; target.label='Cycles AO baked on unique secondary UV'
nodes.active=target
bpy.ops.object.select_all(action='DESELECT'); stone.select_set(True); bpy.context.view_layer.objects.active=stone
assert 'AmbientOcclusion' in stone.data.uv_layers
bpy.ops.object.bake(type='AO',uv_layer='AmbientOcclusion')
ao.filepath_raw=str(OUT/'stone_ao.png'); ao.file_format='PNG'; ao.save()
uv=nodes.new('ShaderNodeUVMap'); uv.uv_map='AmbientOcclusion'; links.new(uv.outputs['UV'],target.inputs['Vector'])
sep=nodes.new('ShaderNodeSeparateColor'); links.new(target.outputs['Color'],sep.inputs['Color'])
group=next(n for n in nodes if n.type=='GROUP' and n.node_tree.name=='glTF Material Output')
links.new(sep.outputs['Red'],group.inputs['Occlusion'])
stone.data.uv_layers.active_index=0
# Explicitly bind primary atlas nodes, avoiding active-UV ambiguities on export.
primary=nodes.new('ShaderNodeUVMap'); primary.uv_map='StoneAtlas'
for node in nodes:
    if node.type=='TEX_IMAGE' and node!=target: links.new(primary.outputs['UV'],node.inputs['Vector'])
bpy.ops.export_scene.gltf(filepath=str(OUT/'stele-final.glb'),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_materials='EXPORT',export_yup=True,export_apply=True)
for image in bpy.data.images:
    if image.source=='FILE' or image==ao: image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)
audit=json.loads((OUT/'geometry-audit.json').read_text())
audit['ao']='Cycles 12-sample geometric AO, 2048x2048, unique AmbientOcclusion UV; glTF TEXCOORD_1'
audit['textures']={'basecolor':[3072,4096],'normal':[1536,2048],'roughness_metallic':[1536,2048],'ao':[2048,2048]}
(OUT/'geometry-audit.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print('GEOMETRIC_AO_BAKED',flush=True)
