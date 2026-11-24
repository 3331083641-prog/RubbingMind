"""
RubbingMind — Blender 5.2.2 LTS Headless Procedural 3D Exhibition Stele Builder
===============================================================================
Reproducibly builds a museum-curated, lightweight (<5 MB) weathered carved
limestone stele mounted on a stepped obsidian museum plinth with subtle brushed
gold collar trim and intaglio rubbing normal/roughness/AO textures baked from
local repository assets.

All inputs and outputs strictly stay inside D:\\RubbingMind.

Usage (Windows):
  D:\\Codex\\blender-5.2.2\\blender-5.2.2-windows-x64\\blender.exe ^
    --background --python D:\\RubbingMind\\tools\\blender\\build_exhibition_stele.py
"""

import json
import math
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
RUBBING_SOURCE = ROOT / "apps/web/public/assets/stele/rubbings/stele_tang_duobao_clean.png"
OUT_DIR = ROOT / "apps/web/public/assets/stele/model3d/gallery"
OUT_GLB = OUT_DIR / "huacan-exhibition-stele.glb"
OUT_META = OUT_DIR / "exhibition-stele-meta.json"
OUT_TEX_DIR = OUT_DIR / "textures"


def _load_rubbing_gray(size_w: int, size_h: int) -> np.ndarray:
    """Load the repository rubbing image using Blender's built-in image loader (no external PIL required)."""
    if not RUBBING_SOURCE.exists():
        # Procedural calligraphic vertical stroke fallback if source missing
        yy, xx = np.mgrid[0:size_h, 0:size_w]
        cols = np.sin(xx / size_w * math.pi * 16.0) ** 2
        rows = np.sin(yy / size_h * math.pi * 28.0) ** 2
        return np.clip(0.55 + 0.4 * cols * rows, 0.0, 1.0).astype(np.float32)

    img = bpy.data.images.load(str(RUBBING_SOURCE), check_existing=False)
    w, h = img.size[0], img.size[1]
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    rgba = px.reshape((h, w, 4))
    # Flip Y so row 0 is top of image
    rgba = rgba[::-1, :, :]
    gray = 0.2126 * rgba[:, :, 0] + 0.7152 * rgba[:, :, 1] + 0.0722 * rgba[:, :, 2]

    # Bilinear resample to (size_h, size_w)
    ys = np.linspace(0, h - 1, size_h)
    xs = np.linspace(0, w - 1, size_w)
    y0 = np.floor(ys).astype(np.int32)
    x0 = np.floor(xs).astype(np.int32)
    y1 = np.minimum(y0 + 1, h - 1)
    x1 = np.minimum(x0 + 1, w - 1)
    wy = (ys - y0)[:, None]
    wx = (xs - x0)[None, :]
    resampled = (
        (1.0 - wy) * ((1.0 - wx) * gray[y0[:, None], x0[None, :]] + wx * gray[y0[:, None], x1[None, :]])
        + wy * ((1.0 - wx) * gray[y1[:, None], x0[None, :]] + wx * gray[y1[:, None], x1[None, :]])
    )
    return np.clip(resampled, 0.0, 1.0).astype(np.float32)


def _fbm_noise(h: int, w: int, seed: int = 42) -> np.ndarray:
    """Fast multi-octave tileable procedural limestone mineral noise using FFT-free trigonometric octaves."""
    rng = np.random.default_rng(seed)
    yy = np.linspace(0.0, 2.0 * math.pi, h, endpoint=False)[:, None]
    xx = np.linspace(0.0, 2.0 * math.pi, w, endpoint=False)[None, :]
    acc = np.zeros((h, w), dtype=np.float32)
    amp = 0.5
    for octave in range(5):
        freq = 2 ** octave
        for _ in range(4):
            fx = rng.integers(1, 3 * freq + 1)
            fy = rng.integers(1, 3 * freq + 1)
            ph = float(rng.uniform(0.0, 2.0 * math.pi))
            acc += amp * 0.25 * np.sin(fx * xx + fy * yy + ph).astype(np.float32)
        amp *= 0.52
    # Add fine grain
    acc += rng.normal(0.0, 0.06, (h, w)).astype(np.float32)
    mn, mx = float(acc.min()), float(acc.max())
    return (acc - mn) / max(1e-6, mx - mn)


def _save_image_rgb(path: Path, rgb: np.ndarray, file_format: str = "JPEG", quality: int = 88) -> bpy.types.Image:
    """Write float32 [0..1] (H, W, 3) array (top-to-bottom) via Blender image IO and reload cleanly."""
    h, w, _ = rgb.shape
    rgba = np.ones((h, w, 4), dtype=np.float32)
    # Blender stores bottom-to-top
    rgba[:, :, :3] = np.clip(rgb[::-1, :, :], 0.0, 1.0)
    img = bpy.data.images.new(name=path.stem, width=w, height=h, alpha=False)
    img.pixels.foreach_set(rgba.ravel())
    img.filepath_raw = str(path)
    img.file_format = file_format
    scene = bpy.context.scene
    prev_fmt = scene.render.image_settings.file_format
    prev_q = scene.render.image_settings.quality
    scene.render.image_settings.file_format = file_format
    scene.render.image_settings.quality = quality
    img.save_render(str(path))
    scene.render.image_settings.file_format = prev_fmt
    scene.render.image_settings.quality = prev_q
    bpy.data.images.remove(img)
    loaded = bpy.data.images.load(str(path), check_existing=False)
    return loaded


def synthesize_stele_pbr_maps():
    """Generate high-aesthetic weathered bluestone + carved inscription PBR maps (1024x1024)."""
    OUT_TEX_DIR.mkdir(parents=True, exist_ok=True)
    size = 1024
    noise_coarse = _fbm_noise(size, size, seed=752)
    noise_fine = _fbm_noise(size, size, seed=185)
    rubbing = _load_rubbing_gray(size, size)

    # Normalize rubbing so bright ink strokes become deep carved grooves (intaglio)
    p10, p92 = float(np.percentile(rubbing, 10)), float(np.percentile(rubbing, 92))
    glyph_mask = np.clip((rubbing - p10) / max(1e-5, p92 - p10), 0.0, 1.0)
    # Softly frame the inscription area so stone edges stay clean weathered limestone
    yy = np.linspace(0.0, 1.0, size)[:, None]
    xx = np.linspace(0.0, 1.0, size)[None, :]
    margin_x = np.clip(np.minimum(xx, 1.0 - xx) / 0.065, 0.0, 1.0)
    margin_y = np.clip(np.minimum(yy, 1.0 - yy) / 0.045, 0.0, 1.0)
    frame_blend = margin_x * margin_y

    # Subtle carved double border frame (古碑界栏线)
    border_outer = np.exp(-(((np.minimum(np.minimum(xx, 1.0 - xx), np.minimum(yy, 1.0 - yy)) - 0.036) / 0.004) ** 2))
    border_inner = np.exp(-(((np.minimum(np.minimum(xx, 1.0 - xx), np.minimum(yy, 1.0 - yy)) - 0.052) / 0.0028) ** 2))
    carved_groove = np.clip(glyph_mask * frame_blend * 0.85 + 0.55 * border_outer + 0.35 * border_inner, 0.0, 1.0)

    # Height field: stone strata + micro pits - carved intaglio grooves
    strata = 0.06 * np.sin(yy * math.pi * 18.0 + noise_coarse * 2.4)
    height = 0.62 + 0.18 * noise_coarse + 0.09 * noise_fine + strata - 0.34 * carved_groove

    # Albedo: authentic Xi'an Beilin weathered bluish-charcoal limestone with warm mineral patina
    base_r = 0.24 + 0.10 * noise_coarse + 0.04 * noise_fine
    base_g = 0.25 + 0.09 * noise_coarse + 0.035 * noise_fine
    base_b = 0.265 + 0.08 * noise_coarse + 0.03 * noise_fine
    # Warm ochre mineral patina near borders & weathering veins
    patina = np.clip((noise_coarse - 0.52) * 1.9, 0.0, 1.0)
    base_r += 0.055 * patina
    base_g += 0.038 * patina
    base_b += 0.012 * patina
    # Carved grooves catch subtle pale limestone chisel dust / contrast for raking-light readability
    groove_tint = 1.0 - 0.28 * carved_groove
    chisel_highlight = 0.14 * np.clip(carved_groove - 0.35, 0.0, 1.0)
    albedo = np.stack(
        [
            np.clip(base_r * groove_tint + chisel_highlight * 0.92, 0.05, 0.95),
            np.clip(base_g * groove_tint + chisel_highlight * 0.88, 0.05, 0.95),
            np.clip(base_b * groove_tint + chisel_highlight * 0.80, 0.05, 0.95),
        ],
        axis=-1,
    )

    # Tangent-space Normal Map from height gradient (strong crisp chisel bevels for raking light!)
    gx = np.gradient(height, axis=1) * 18.0
    gy = np.gradient(height, axis=0) * 18.0
    nx = -gx
    ny = gy  # OpenGL +Y normal orientation for glTF
    nz = np.ones_like(height)
    inv_len = 1.0 / np.sqrt(nx * nx + ny * ny + nz * nz + 1e-8)
    normal_rgb = np.stack(
        [
            nx * inv_len * 0.5 + 0.5,
            ny * inv_len * 0.5 + 0.5,
            nz * inv_len * 0.5 + 0.5,
        ],
        axis=-1,
    )

    # ORM Map (R = AO, G = Roughness, B = Metallic=0)
    ao = np.clip(0.95 - 0.42 * carved_groove - 0.12 * (1.0 - noise_coarse), 0.35, 1.0)
    roughness = np.clip(0.76 + 0.16 * noise_fine + 0.08 * carved_groove - 0.08 * patina, 0.55, 0.98)
    metallic = np.zeros_like(ao)
    orm_rgb = np.stack([ao, roughness, metallic], axis=-1)

    albedo_img = _save_image_rgb(OUT_TEX_DIR / "exhibition_stone_albedo.jpg", albedo, "JPEG", 88)
    albedo_img.colorspace_settings.name = "sRGB"

    normal_img = _save_image_rgb(OUT_TEX_DIR / "exhibition_stone_normal.png", normal_rgb, "PNG", 90)
    normal_img.colorspace_settings.name = "Non-Color"

    orm_img = _save_image_rgb(OUT_TEX_DIR / "exhibition_stone_orm.jpg", orm_rgb, "JPEG", 88)
    orm_img.colorspace_settings.name = "Non-Color"

    return albedo_img, normal_img, orm_img, carved_groove


def make_stone_material(name: str, albedo_img, normal_img, orm_img):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.86

    tex_albedo = nodes.new("ShaderNodeTexImage")
    tex_albedo.image = albedo_img
    links.new(tex_albedo.outputs["Color"], bsdf.inputs["Base Color"])

    tex_norm = nodes.new("ShaderNodeTexImage")
    tex_norm.image = normal_img
    norm_map = nodes.new("ShaderNodeNormalMap")
    norm_map.inputs["Strength"].default_value = 1.15
    links.new(tex_norm.outputs["Color"], norm_map.inputs["Color"])
    links.new(norm_map.outputs["Normal"], bsdf.inputs["Normal"])

    tex_orm = nodes.new("ShaderNodeTexImage")
    tex_orm.image = orm_img
    sep = nodes.new("ShaderNodeSeparateColor")
    links.new(tex_orm.outputs["Color"], sep.inputs["Color"])
    links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])

    # glTF Occlusion socket group
    tree = bpy.data.node_groups.new("glTF Material Output", "ShaderNodeTree")
    tree.interface.new_socket(name="Occlusion", in_out="INPUT", socket_type="NodeSocketFloat")
    ao_node = nodes.new("ShaderNodeGroup")
    ao_node.node_tree = tree
    links.new(sep.outputs["Red"], ao_node.inputs["Occlusion"])
    return mat


def make_solid_pbr_material(name: str, color, roughness: float, metallic: float):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def build_weathered_stele_slab(mat_stone, carved_groove: np.ndarray):
    """
    Construct a watertight sculpted stele body with:
    - Physical slab thickness (1.28m x 2.15m x 0.24m), matching steleDimensions.ts
    - Weathered organic edge chamfers & asymmetric corner spalling
    - Recessed front inscription panel with actual micro-relief geometry
    """
    nx, ny, nz = 72, 112, 10
    w, h, d = 1.28, 2.15, 0.24
    y_center = 1.585

    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    # Subdivide grid manually via clean parametric shell for perfect UVs & watertight edges
    bm.free()

    verts = []
    faces = []
    uvs = []
    lookup = {}

    def get_v(pt):
        key = (round(pt[0], 6), round(pt[1], 6), round(pt[2], 6))
        idx = lookup.get(key)
        if idx is None:
            idx = len(verts)
            lookup[key] = idx
            verts.append(pt)
        return idx

    gh, gw = carved_groove.shape

    def sample_groove(u, v):
        ix = min(gw - 1, max(0, int(u * (gw - 1))))
        iy = min(gh - 1, max(0, int((1.0 - v) * (gh - 1))))
        return float(carved_groove[iy, ix])

    def eval_point(face_name: str, u: float, v: float):
        if face_name == "front":
            x, y, z = (u - 0.5) * w, y_center + (v - 0.5) * h, d * 0.5
        elif face_name == "back":
            x, y, z = (0.5 - u) * w, y_center + (v - 0.5) * h, -d * 0.5
        elif face_name == "left":
            x, y, z = -w * 0.5, y_center + (v - 0.5) * h, (u - 0.5) * d
        elif face_name == "right":
            x, y, z = w * 0.5, y_center + (v - 0.5) * h, (0.5 - u) * d
        elif face_name == "top":
            x, y, z = (u - 0.5) * w, y_center + h * 0.5, (0.5 - v) * d
        else:
            x, y, z = (u - 0.5) * w, y_center - h * 0.5, (v - 0.5) * d

        # Smooth rounded limestone bevel along slab edges
        r = 0.016
        qx, qy, qz = x, y - y_center, z
        hx, hy, hz = w * 0.5 - r, h * 0.5 - r, d * 0.5 - r
        cx, cy, cz = max(-hx, min(hx, qx)), max(-hy, min(hy, qy)), max(-hz, min(hz, qz))
        dx, dy, dz = qx - cx, qy - cy, qz - cz
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist > 1e-8:
            x = cx + dx * r / dist
            y = y_center + cy + dy * r / dist
            z = cz + dz * r / dist

        # Authentic historical corner & side spalling (shared in world space -> watertight)
        edge_factor = max(0.0, min(1.0, (abs(x) - 0.54) / 0.10)) ** 2
        spall_sites = (
            [(0.95, 0.022, 0.055), (1.62, 0.014, 0.045), (2.34, 0.024, 0.060)]
            if x < 0
            else [(1.08, 0.019, 0.05), (1.76, 0.021, 0.045), (2.41, 0.016, 0.04)]
        )
        spall = sum(depth * math.exp(-(((y - sy) / span) ** 2)) for sy, depth, span in spall_sites)
        x -= math.copysign(edge_factor * spall, x)

        # Recessed calligraphic tablet & carved intaglio relief on front face
        if face_name == "front":
            margin = min(u, 1.0 - u, v, 1.0 - v)
            recess = -0.0085 * min(1.0, max(0.0, (margin - 0.045) / 0.022))
            # Subtle physical carve depth from rubbing mask
            carve = -0.0028 * sample_groove(u, v) * min(1.0, margin * 18.0)
            z += recess + carve
        elif face_name == "back":
            margin = min(u, 1.0 - u, v, 1.0 - v)
            z += 0.004 * min(1.0, max(0.0, (margin - 0.05) / 0.025))

        # Fine mineral undulation shared across faces (vanishes on top/bottom seams)
        if face_name in ("front", "back", "left", "right"):
            seam_fade = min(1.0, min(u, 1.0 - u, v, 1.0 - v) * 24.0)
            micro = 0.0007 * math.sin(x * 41.0 + y * 23.0 + z * 37.0) * math.cos(x * 19.0 - y * 31.0)
            if face_name == "front":
                z += micro * seam_fade
            elif face_name == "back":
                z -= micro * seam_fade
            elif face_name == "left":
                x -= micro * seam_fade
            else:
                x += micro * seam_fade

        return (x, y, z)

    def add_grid(face_name: str, su: int, sv: int, uv_scale=(1.0, 1.0), uv_off=(0.0, 0.0)):
        grid = []
        for j in range(sv + 1):
            row = []
            for i in range(su + 1):
                row.append(get_v(eval_point(face_name, i / su, j / sv)))
            grid.append(row)
        for j in range(sv):
            for i in range(su):
                f = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
                u0, v0 = uv_off[0] + (i / su) * uv_scale[0], uv_off[1] + (j / sv) * uv_scale[1]
                u1, v1 = uv_off[0] + ((i + 1) / su) * uv_scale[0], uv_off[1] + ((j + 1) / sv) * uv_scale[1]
                faces.append(f)
                uvs.append([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    add_grid("front", nx, ny, (1.0, 1.0), (0.0, 0.0))
    add_grid("back", 24, 36, (0.25, 0.35), (0.02, 0.02))
    add_grid("left", nz, 36, (0.08, 0.35), (0.01, 0.02))
    add_grid("right", nz, 36, (0.08, 0.35), (0.90, 0.02))
    add_grid("top", 24, nz, (0.25, 0.08), (0.02, 0.90))
    add_grid("bottom", 24, nz, (0.25, 0.08), (0.02, 0.01))

    mesh = bpy.data.meshes.new("ExhibitionSteleBody")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", np.asarray([c for f in uvs for c in f], dtype=np.float32).ravel())
    mesh.polygons.foreach_set("use_smooth", np.ones(len(mesh.polygons), dtype=bool))

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("ExhibitionSteleBody", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    return obj


def build_arch_crown(mat_stone):
    """Build an elegant Tang-Song arched stele crown (螭首拱额) with sculpted double border & title cartouche."""
    r = 0.64
    base_y = 2.66
    depth = 0.24
    nu, nv = 64, 32

    verts = []
    faces = []
    uvs = []
    lookup = {}

    def get_v(pt):
        key = (round(pt[0], 6), round(pt[1], 6), round(pt[2], 6))
        idx = lookup.get(key)
        if idx is None:
            idx = len(verts)
            lookup[key] = idx
            verts.append(pt)
        return idx

    def crown_pt(sign: float, u: float, v: float):
        x = (u * 2.0 - 1.0) * r * math.sqrt(max(0.0, 1.0 - v * v))
        y = base_y + v * r
        rho = math.sqrt((x / r) ** 2 + v * v)
        bevel = 0.016 * max(0.0, min(1.0, (rho - 0.94) / 0.06))

        # Sculpted relief on front crown: stylized cloud arch + central vertical title plaque recess (篆额)
        relief = 0.0
        if sign > 0:
            # Raised arch rib + cloud waves
            arch_rib = 0.012 * math.exp(-(((rho - 0.82) / 0.06) ** 2))
            cloud_wave = 0.007 * math.exp(-(((rho - 0.64) / 0.14) ** 2)) * (0.5 + 0.5 * math.cos(math.atan2(v, x / r) * 8.0))
            # Central recessed title tablet (篆额框)
            in_cartouche = abs(x) < 0.13 and 0.12 < v < 0.56
            cartouche_rim = (
                0.008 * math.exp(-(((abs(x) - 0.135) / 0.014) ** 2)) * (1.0 if 0.10 < v < 0.58 else 0.0)
                + 0.008 * math.exp(-(((v - 0.57) / 0.022) ** 2)) * (1.0 if abs(x) < 0.145 else 0.0)
                + 0.008 * math.exp(-(((v - 0.11) / 0.022) ** 2)) * (1.0 if abs(x) < 0.145 else 0.0)
            )
            relief = arch_rib + cloud_wave + cartouche_rim + (-0.007 if in_cartouche else 0.0)
        else:
            relief = 0.004 * math.exp(-(((rho - 0.82) / 0.07) ** 2))

        z = sign * (depth * 0.5 - bevel + relief)
        return (x, y, z)

    for sign in (1.0, -1.0):
        grid = []
        for j in range(nv + 1):
            row = []
            for i in range(nu + 1):
                row.append(get_v(crown_pt(sign, i / nu, j / nv)))
            grid.append(row)
        for j in range(nv):
            for i in range(nu):
                raw_f = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
                uniq = []
                for idx in raw_f:
                    if idx not in uniq:
                        uniq.append(idx)
                if len(uniq) < 3:
                    continue
                if sign < 0:
                    uniq.reverse()
                faces.append(uniq)
                uvs.append(
                    [
                        (
                            0.04 + (verts[idx][0] / (2.0 * r) + 0.5) * 0.24,
                            0.04 + ((verts[idx][1] - base_y) / r) * 0.24,
                        )
                        for idx in uniq
                    ]
                )

    # Stitch outer arch rim and bottom seam watertight
    seam_paths = [
        [(0.0, j / nv) for j in range(nv + 1)],
        [(1.0, j / nv) for j in range(nv + 1)],
        [(i / nu, 0.0) for i in range(nu + 1)],
    ]
    for path in seam_paths:
        for i in range(len(path) - 1):
            u0, v0 = path[i]
            u1, v1 = path[i + 1]
            f = [
                get_v(crown_pt(1.0, u0, v0)),
                get_v(crown_pt(-1.0, u0, v0)),
                get_v(crown_pt(-1.0, u1, v1)),
                get_v(crown_pt(1.0, u1, v1)),
            ]
            if len(set(f)) >= 3:
                faces.append(f)
                uvs.append([(0.02, 0.02), (0.06, 0.02), (0.06, 0.06), (0.02, 0.06)])

    mesh = bpy.data.meshes.new("ExhibitionSteleCrown")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_layer.data.foreach_set("uv", np.asarray([c for f in uvs for c in f], dtype=np.float32).ravel())
    mesh.polygons.foreach_set("use_smooth", np.ones(len(mesh.polygons), dtype=bool))

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("ExhibitionSteleCrown", mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat_stone)
    return obj


def build_beveled_tier(name: str, center_y: float, size, bevel_width: float, mat):
    """Build a crisp museum architectural plinth tier with smooth chamfered edges."""
    w, h, d = size
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, h, d), verts=bm.verts)
    bmesh.ops.bevel(
        bm,
        geom=list(bm.edges),
        offset=bevel_width,
        segments=3,
        affect="EDGES",
        clamp_overlap=True,
    )
    bmesh.ops.translate(bm, vec=(0.0, center_y, 0.0), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()

    # Box-projected UVs
    uv_layer = mesh.uv_layers.new(name="UVMap")
    uv_coords = []
    for poly in mesh.polygons:
        n = poly.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        for li in poly.loop_indices:
            co = mesh.vertices[mesh.loops[li].vertex_index].co
            if ax == 0:
                u, v = co.z * 0.5 + 0.5, co.y * 0.5 + 0.5
            elif ax == 1:
                u, v = co.x * 0.5 + 0.5, co.z * 0.5 + 0.5
            else:
                u, v = co.x * 0.5 + 0.5, co.y * 0.5 + 0.5
            uv_coords.extend([max(0.0, min(1.0, u)), max(0.0, min(1.0, v))])
    uv_layer.data.foreach_set("uv", np.asarray(uv_coords, dtype=np.float32))
    mesh.polygons.foreach_set("use_smooth", np.ones(len(mesh.polygons), dtype=bool))

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    albedo_img, normal_img, orm_img, carved_groove = synthesize_stele_pbr_maps()

    mat_stone = make_stone_material("WeatheredCarvedLimestone", albedo_img, normal_img, orm_img)
    mat_obsidian_plinth = make_solid_pbr_material("ObsidianMuseumPlinth", (0.045, 0.050, 0.058), roughness=0.42, metallic=0.08)
    mat_brushed_gold = make_solid_pbr_material("MuseumBrushedGoldTrim", (0.76, 0.60, 0.32), roughness=0.34, metallic=0.88)

    objects = [
        build_weathered_stele_slab(mat_stone, carved_groove),
        build_arch_crown(mat_stone),
        # Stepped contemporary-meets-classical museum plinth (matches Y=0..0.55 pedestal footprint)
        build_beveled_tier("MuseumPlinth_Base", 0.09, (1.86, 0.18, 0.74), 0.014, mat_obsidian_plinth),
        build_beveled_tier("MuseumPlinth_GoldFilletLower", 0.188, (1.72, 0.018, 0.64), 0.004, mat_brushed_gold),
        build_beveled_tier("MuseumPlinth_Waist", 0.29, (1.66, 0.19, 0.58), 0.012, mat_obsidian_plinth),
        build_beveled_tier("MuseumPlinth_StoneCradle", 0.455, (1.48, 0.15, 0.44), 0.014, mat_stone),
        build_beveled_tier("MuseumPlinth_GoldCollar", 0.538, (1.36, 0.022, 0.32), 0.005, mat_brushed_gold),
    ]

    # Audit topology before coordinate export
    audit_parts = []
    total_verts = 0
    total_tris = 0
    for obj in objects:
        obj.data.calc_loop_triangles()
        v_cnt = len(obj.data.vertices)
        t_cnt = len(obj.data.loop_triangles)
        total_verts += v_cnt
        total_tris += t_cnt
        audit_parts.append({"name": obj.name, "vertices": v_cnt, "triangles": t_cnt})

    # Convert Web Y-up authoring space -> Blender Z-up so glTF Y-up export lands upright at Y=0..3.30
    conversion = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    for obj in objects:
        obj.data.transform(conversion)

    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    bpy.ops.export_scene.gltf(
        filepath=str(OUT_GLB),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_jpeg_quality=86,
    )

    # Clean up intermediate loose texture files so only self-contained GLB ships cleanly
    for tmp_tex in OUT_TEX_DIR.glob("*"):
        tmp_tex.unlink(missing_ok=True)
    if OUT_TEX_DIR.exists():
        OUT_TEX_DIR.rmdir()

    glb_bytes = OUT_GLB.stat().st_size
    meta = {
        "generator": f"Blender {bpy.app.version_string}",
        "script": "tools/blender/build_exhibition_stele.py",
        "model": OUT_GLB.relative_to(ROOT).as_posix(),
        "bytes": glb_bytes,
        "megabytes": round(glb_bytes / (1024 * 1024), 2),
        "totalVertices": total_verts,
        "totalTriangles": total_tris,
        "parts": audit_parts,
    }
    OUT_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("EXPORTED_EXHIBITION_STELE:", json.dumps(meta, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
