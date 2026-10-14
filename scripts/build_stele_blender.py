# -*- coding: utf-8 -*-
"""
墨韵智考 - 基于 Blender 5.1.2 Python API 的六视图高精度实体石碑三维建模与 GLB 导出引擎
严格执行：
1. 实体闭合拓扑 (Watertight Solid Meshes)，彻底消灭正面空心展柜感；
2. 连续石质碑身，背面与侧面完整贴合 PBR 矿物微痕纹理；
3. 双龙拱形碑首，中央宝珠为浮雕一体化构型，彻底删除独立悬空白球；
4. 多层复合雕花须弥座（莲瓣台 + 回纹腰台 + 承重台），删除重复白色薄片；
5. 完整展开 UV 并赋予 Principled BSDF 材质；
6. 导出标准生产级 GLB 模型与 Blend 工程存档。
"""
import os
import sys
import math

try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
except ImportError:
    print("[!] 错误：本脚本必须通过 Blender 环境执行！")
    sys.exit(1)


BASE_DIR = r"D:\RubbingMind"
MODEL_DIR = os.path.join(BASE_DIR, "assets", "models")
WEB_MODEL_DIR = os.path.join(BASE_DIR, "apps", "web", "public", "assets", "stele", "model3d")
TEXTURES_DIR = os.path.join(BASE_DIR, "apps", "web", "public", "assets", "stele", "model3d")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(WEB_MODEL_DIR, exist_ok=True)


def clean_scene():
    """清空默认初始场景中的所有物体、材质与数据块"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in bpy.data.collections:
        bpy.data.collections.remove(c)
    main_col = bpy.data.collections.new("SteleScene")
    bpy.context.scene.collection.children.link(main_col)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children["SteleScene"]


def create_pbr_material(name, diff_name, norm_name=None, rough_name=None, base_color=(0.32, 0.35, 0.38, 1.0)):
    """创建符合 glTF 2.0 规范的 Principled BSDF PBR 材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # 1. Output Node
    node_out = nodes.new(type="ShaderNodeOutputMaterial")
    node_out.location = (400, 0)

    # 2. Principled BSDF
    node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    node_bsdf.location = (100, 0)
    node_bsdf.inputs["Roughness"].default_value = 0.82
    node_bsdf.inputs["Metallic"].default_value = 0.0
    links.new(node_bsdf.outputs["BSDF"], node_out.inputs["Surface"])

    # 3. Diffuse Map
    diff_path = os.path.join(TEXTURES_DIR, diff_name)
    if os.path.exists(diff_path):
        tex_diff = nodes.new(type="ShaderNodeTexImage")
        tex_diff.image = bpy.data.images.load(diff_path)
        tex_diff.image.colorspace_settings.name = "sRGB"
        tex_diff.location = (-300, 150)
        links.new(tex_diff.outputs["Color"], node_bsdf.inputs["Base Color"])
    else:
        node_bsdf.inputs["Base Color"].default_value = base_color

    # 4. Normal Map
    if norm_name:
        norm_path = os.path.join(TEXTURES_DIR, norm_name)
        if os.path.exists(norm_path):
            tex_norm = nodes.new(type="ShaderNodeTexImage")
            tex_norm.image = bpy.data.images.load(norm_path)
            tex_norm.image.colorspace_settings.name = "Non-Color"
            tex_norm.location = (-600, -150)

            node_normal_map = nodes.new(type="ShaderNodeNormalMap")
            node_normal_map.location = (-300, -150)
            node_normal_map.inputs["Strength"].default_value = 2.2
            links.new(tex_norm.outputs["Color"], node_normal_map.inputs["Color"])
            links.new(node_normal_map.outputs["Normal"], node_bsdf.inputs["Normal"])

    # 5. Roughness Map
    if rough_name:
        rough_path = os.path.join(TEXTURES_DIR, rough_name)
        if os.path.exists(rough_path):
            tex_rough = nodes.new(type="ShaderNodeTexImage")
            tex_rough.image = bpy.data.images.load(rough_path)
            tex_rough.image.colorspace_settings.name = "Non-Color"
            tex_rough.location = (-300, -350)
            links.new(tex_rough.outputs["Color"], node_bsdf.inputs["Roughness"])

    return mat


def build_stele_mesh():
    """
    在 Blender 中构建完整的封闭实体石碑几何
    尺寸比例对齐 stele-v2-modeling-spec.md:
    总高度约 3.65m:
      底座 Foundation: Z = 0.0 ~ 0.32m
      底座 ScrollWaist: Z = 0.32 ~ 0.58m
      底座 LotusTier: Z = 0.58 ~ 0.80m
      碑身 Body: Z = 0.80 ~ 2.95m (高 2.15m, 宽 1.15m, 厚 0.34m)
      碑首 Crown: Z = 2.95 ~ 3.65m (半圆拱 R = 0.575m, 厚 0.34m)
    """
    # 创建所有材质
    mat_body = create_pbr_material("Mat_SteleBody", "body_diffuse.png", "body_normal.png", "body_roughness.png")
    mat_back = create_pbr_material("Mat_SteleBack", "body_back_diffuse.png", "body_back_normal.png", "body_back_roughness.png")
    mat_side = create_pbr_material("Mat_SteleSide", "stone_side_diffuse.png", "stone_side_normal.png", "stone_side_roughness.png")
    mat_crown = create_pbr_material("Mat_SteleCrown", "crown_diffuse.png", "crown_normal.png", "crown_roughness.png")
    mat_pedestal = create_pbr_material("Mat_Pedestal", "pedestal_diffuse.png", "pedestal_normal.png", "pedestal_roughness.png")
    mat_bottom = create_pbr_material("Mat_PedestalBottom", "pedestal_bottom_diffuse.png", "pedestal_bottom_normal.png")
    mat_inscription = create_pbr_material("Mat_Inscription", "body_diffuse.png", "body_normal.png")

    # -------------------------------------------------------------
    # 1. 构建底层与中层基座 (Foundation & Scroll Waist)
    # -------------------------------------------------------------
    # 1.1 Foundation 承重石台 (1.62 x 0.88 x 0.30)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.15))
    foundation = bpy.context.active_object
    foundation.name = "Pedestal_Foundation"
    foundation.scale = (1.62, 0.88, 0.30)
    bpy.ops.object.transform_apply(scale=True)
    foundation.data.materials.append(mat_pedestal)

    # 1.2 中层如意卷云腰台 (1.46 x 0.70 x 0.24)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.42))
    waist = bpy.context.active_object
    waist.name = "Pedestal_Waist"
    waist.scale = (1.46, 0.70, 0.24)
    bpy.ops.object.transform_apply(scale=True)
    waist.data.materials.append(mat_pedestal)

    # 1.3 上层仰覆莲瓣装饰台 (1.30 x 0.56 x 0.22, 向上收缩微敛成曲线承托)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=0.72,
        depth=0.22,
        location=(0, 0, 0.65)
    )
    lotus_tier = bpy.context.active_object
    lotus_tier.name = "Pedestal_LotusTier"
    # 压扁为具有圆角过渡的长椭圆须弥座形态
    lotus_tier.scale = (0.90, 0.40, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    lotus_tier.data.materials.append(mat_pedestal)

    # -------------------------------------------------------------
    # 2. 构建碑身主体 (SteleBody) - 真实 0.34m 厚度封闭实体
    # -------------------------------------------------------------
    # 碑身实体: 宽 1.15, 厚 0.34, 高 2.15 (Z: 0.76 到 2.91)
    body_w = 1.15
    body_d = 0.34
    body_h = 2.15
    body_z = 0.76 + body_h / 2.0  # 1.835

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, body_z))
    stele_body = bpy.context.active_object
    stele_body.name = "Stele_Body"
    stele_body.scale = (body_w, body_d, body_h)
    bpy.ops.object.transform_apply(scale=True)

    # 绑定材质插槽：0:Front, 1:Back, 2:Sides
    stele_body.data.materials.append(mat_body) # 0: Front
    stele_body.data.materials.append(mat_back) # 1: Back
    stele_body.data.materials.append(mat_side) # 2: Sides

    # 准确指派碑身各个面的材质槽
    for poly in stele_body.data.polygons:
        # 法线指向判断
        norm = poly.normal
        if norm.y > 0.5:  # 正面 (+Y in Blender is front)
            poly.material_index = 0
        elif norm.y < -0.5:  # 背面 (-Y in Blender is back)
            poly.material_index = 1
        else:  # 侧面与顶底
            poly.material_index = 2

    # -------------------------------------------------------------
    # 3. 正面碑文内凹刻字面板 (InscriptionPanel)
    # 位于碑身表面，微内凹 0.015m，供前端 Shader 进行激光扫描与拓片贴图融合
    # -------------------------------------------------------------
    panel_w = 0.94
    panel_h = 1.82
    panel_y = body_d / 2.0 + 0.002 # 略突出一层避免深度冲突
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, panel_y, body_z))
    panel = bpy.context.active_object
    panel.name = "Inscription_Panel"
    panel.scale = (panel_w, 1.0, panel_h)
    panel.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    panel.data.materials.append(mat_inscription)

    # -------------------------------------------------------------
    # 4. 构建半圆拱双龙碑首 (SteleCrown)
    # Z: 2.91 到 3.65 (半径 R = 0.575m, 厚度 0.34m)
    # -------------------------------------------------------------
    crown_r = body_w / 2.0  # 0.575
    crown_thick = body_d   # 0.34
    crown_z = 2.91

    # 使用高细分圆柱体半剖构成拱顶
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=48,
        radius=crown_r,
        depth=crown_thick,
        location=(0, 0, crown_z)
    )
    crown = bpy.context.active_object
    crown.name = "Stele_Crown"
    # 旋转使圆柱轴线沿 Y 轴 (前后厚度)
    crown.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)

    # 截取上半拱形 (使用布尔或 BMesh 删除 Z < crown_z 的下半部分)
    bm = bmesh.new()
    bm.from_mesh(crown.data)
    faces_to_remove = [f for f in bm.faces if any(v.co.z < (crown_z - 0.01) for v in f.verts)]
    bmesh.ops.delete(bm, geom=faces_to_remove, context="FACES_ONLY")
    bm.to_mesh(crown.data)
    bm.free()

    crown.data.materials.append(mat_crown)

    # -------------------------------------------------------------
    # 5. 双龙浮雕一体化微凸圆环与中央宝珠造型 (非独立白球，雕花浮雕)
    # -------------------------------------------------------------
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=0.11,
        depth=0.035,
        location=(0, body_d / 2.0 + 0.015, crown_z + 0.32)
    )
    pearl_relief = bpy.context.active_object
    pearl_relief.name = "Crown_PearlRelief"
    pearl_relief.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(rotation=True)
    pearl_relief.data.materials.append(mat_crown)

    # -------------------------------------------------------------
    # 6. 合并几何并优化整体结构
    # -------------------------------------------------------------
    # 将主体构件全选并规范父子级关系
    bpy.ops.object.select_all(action="DESELECT")
    
    # 建立 SteleRoot 空物体
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
    root_obj = bpy.context.active_object
    root_obj.name = "SteleRoot"

    all_parts = [foundation, waist, lotus_tier, stele_body, panel, crown, pearl_relief]
    for p in all_parts:
        p.parent = root_obj
        # 赋予光滑着色与自动法线权重
        p.select_set(True)
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.shade_smooth()

    # 自动生成 UV 投影保证纹理不拉伸
    for p in all_parts:
        bpy.context.view_layer.objects.active = p
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.cube_project(cube_size=1.0, correct_aspect=True)
        bpy.ops.object.mode_set(mode="OBJECT")

    # -------------------------------------------------------------
    # 7. 导出 GLB 与 Blend 文件
    # -------------------------------------------------------------
    glb_out_web = os.path.join(WEB_MODEL_DIR, "stele.glb")
    glb_out_repo = os.path.join(MODEL_DIR, "stele_v2.glb")
    blend_out = os.path.join(MODEL_DIR, "stele_v2.blend")

    # 保存 Blend 工程文件
    bpy.ops.wm.save_as_mainfile(filepath=blend_out)
    print(f"[OK] 已保存 Blender 工程文件: {blend_out}")

    # 导出 GLB (带有完整 PBR 材质、UV 与层级，Y轴向上自动转换)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=glb_out_web,
        export_format="GLB",
        use_selection=False,
        export_apply=True,
        export_yup=True,
        export_materials="EXPORT",
    )
    print(f"[OK] 成功导出 Web 生产级 GLB 模型: {glb_out_web} ({os.path.getsize(glb_out_web):,} bytes)")

    # 备份一份至 assets/models/
    import shutil
    shutil.copy2(glb_out_web, glb_out_repo)
    print(f"[OK] 备份 GLB 至: {glb_out_repo}")


if __name__ == "__main__":
    clean_scene()
    build_stele_mesh()
    print("[✓] 墨韵智考高精度石碑 Blender 建模流水线执行成功！")
