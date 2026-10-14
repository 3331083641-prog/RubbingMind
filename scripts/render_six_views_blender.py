# -*- coding: utf-8 -*-
"""
墨韵智考 - 基于 Blender 5.1.2 的六视图纯白背景高精度渲染脚本
输出标准验收图像至 D:\RubbingMind\screenshots\stele-v2\
严格遵循：纯白背景、无UI、无激光、同一模型、同一材质、高分辨率
"""
import os
import sys
import math

try:
    import bpy
    from mathutils import Vector, Euler
except ImportError:
    print("[!] 错误：请通过 Blender 环境运行此脚本！")
    sys.exit(1)

BASE_DIR = r"D:\RubbingMind"
BLEND_FILE = os.path.join(BASE_DIR, "assets", "models", "stele_v2.blend")
OUT_DIR = os.path.join(BASE_DIR, "screenshots", "stele-v2")
os.makedirs(OUT_DIR, exist_ok=True)


def setup_render_environment():
    """配置无光晕纯白摄影棚世界环境与照明"""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False

    # 1. 纯白世界背景
    if not scene.world:
        scene.world = bpy.data.worlds.new("WhiteStudioWorld")
    world = scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    nodes.clear()
    node_out = nodes.new(type="ShaderNodeOutputWorld")
    node_bg = nodes.new(type="ShaderNodeBackground")
    node_bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0) # 纯白底色
    node_bg.inputs["Strength"].default_value = 0.85
    world.node_tree.links.new(node_bg.outputs["Background"], node_out.inputs["Surface"])

    # 2. 清理旧灯光与摄像机
    for obj in list(scene.objects):
        if obj.type in {"LIGHT", "CAMERA"}:
            bpy.data.objects.remove(obj, do_unlink=True)

    # 3. 添加博物馆全方位漫射布光 (照亮雕刻、侧面与背面，杜绝死黑与高光过曝)
    # 顶部主漫射光
    light_top_data = bpy.data.lights.new(name="Light_Top", type="SUN")
    light_top_data.energy = 2.0
    light_top_data.color = (1.0, 0.98, 0.95)
    light_top = bpy.data.objects.new(name="Light_Top", object_data=light_top_data)
    light_top.rotation_euler = (math.radians(35), math.radians(20), math.radians(45))
    scene.collection.objects.link(light_top)

    # 正面补光
    light_front_data = bpy.data.lights.new(name="Light_Front", type="AREA")
    light_front_data.energy = 180.0
    light_front_data.size = 3.0
    light_front_data.color = (0.95, 0.98, 1.0)
    light_front = bpy.data.objects.new(name="Light_Front", object_data=light_front_data)
    light_front.location = (0, 4.5, 2.0)
    light_front.rotation_euler = (math.radians(-90), 0, math.radians(180))
    scene.collection.objects.link(light_front)

    # 背面补光
    light_back_data = bpy.data.lights.new(name="Light_Back", type="AREA")
    light_back_data.energy = 160.0
    light_back_data.size = 3.0
    light_back_data.color = (1.0, 0.96, 0.92)
    light_back = bpy.data.objects.new(name="Light_Back", object_data=light_back_data)
    light_back.location = (0, -4.5, 2.0)
    light_back.rotation_euler = (math.radians(90), 0, 0)
    scene.collection.objects.link(light_back)

    # 4. 创建拍摄摄像机
    cam_data = bpy.data.cameras.new("RenderCam")
    cam_data.lens = 55.0 # 55mm 标准人眼透视镜头，畸变极低
    cam_data.clip_start = 0.1
    cam_data.clip_end = 100.0
    cam_obj = bpy.data.objects.new("RenderCam", cam_data)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    return cam_obj


def render_all_views():
    # 打开由 build_stele_blender.py 构建好的工程
    if os.path.exists(BLEND_FILE):
        bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)
    else:
        print(f"[!] 找不到工程文件 {BLEND_FILE}")
        return

    cam = setup_render_environment()
    scene = bpy.context.scene

    # 7 大验收视角参数定义 (模型中心约为 Z = 1.825m)
    # 注意：在 Blender 中，+Y 为正面，-Y 为背面，+Z 为高度
    VIEW_CONFIGS = [
        {
            "name": "stele_front.png",
            "res": (768, 1024),
            "pos": (0.0, 4.4, 1.825),
            "rot": (math.radians(90), 0, math.radians(180)),
            "desc": "正视图 (双龙圆拱碑首、碑文刻字、仰覆莲座)",
        },
        {
            "name": "stele_back.png",
            "res": (768, 1024),
            "pos": (0.0, -4.4, 1.825),
            "rot": (math.radians(90), 0, 0),
            "desc": "背视图 (风化青石微痕、自然断裂斜纹)",
        },
        {
            "name": "stele_left.png",
            "res": (768, 1024),
            "pos": (-4.2, 0.0, 1.825),
            "rot": (math.radians(90), 0, math.radians(-90)),
            "desc": "左视图 (厚度剖面、层叠基座)",
        },
        {
            "name": "stele_right.png",
            "res": (768, 1024),
            "pos": (4.2, 0.0, 1.825),
            "rot": (math.radians(90), 0, math.radians(90)),
            "desc": "右视图 (右侧石材断面与榫卯层级)",
        },
        {
            "name": "stele_top.png",
            "res": (1024, 1024),
            "pos": (0.0, 0.001, 5.8),
            "rot": (0, 0, math.radians(180)),
            "desc": "俯视图 (碑首拱顶圆润曲度与底座台面布局)",
        },
        {
            "name": "stele_bottom.png",
            "res": (1024, 1024),
            "pos": (0.0, 0.001, -2.4),
            "rot": (math.radians(180), 0, 0),
            "desc": "仰视图 (底座承重实体结构与防滑咬合槽)",
        },
        {
            "name": "stele_perspective.png",
            "res": (1024, 1024),
            "pos": (2.8, 3.2, 3.2),
            "rot": (math.radians(68), 0, math.radians(140)),
            "desc": "45° 黄金透视全局三维展陈图",
        },
    ]

    print(f"[*] 开始自动化渲染 7 大高精度纯白背景三维石碑验收图...")
    for cfg in VIEW_CONFIGS:
        out_path = os.path.join(OUT_DIR, cfg["name"])
        scene.render.resolution_x = cfg["res"][0]
        scene.render.resolution_y = cfg["res"][1]
        scene.render.filepath = out_path

        cam.location = cfg["pos"]
        cam.rotation_euler = cfg["rot"]

        bpy.ops.render.render(write_still=True)
        size_kb = os.path.getsize(out_path) // 1024
        print(f"  [OK] 成功渲染: {cfg['name']} -> {cfg['desc']} ({size_kb} KB)")

    print(f"[✓] 全部 7 张高精度验收截图已保存至: {OUT_DIR}")


if __name__ == "__main__":
    render_all_views()
