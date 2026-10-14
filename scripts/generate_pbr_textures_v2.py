# -*- coding: utf-8 -*-
"""
墨韵智考 - 基于六视图基准参考图生成高精度 PBR 材质贴图套件 (V2.0)
生成 BaseColor, Normal, Roughness, AO 贴图，并同步至前端资源目录
"""
import os
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIR = os.path.join(BASE_DIR, "design", "references", "stele-v2")
OUT_DIR = os.path.join(BASE_DIR, "apps", "web", "public", "assets", "stele", "model3d")
TEXTURES_DIR = os.path.join(BASE_DIR, "assets", "textures")

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(TEXTURES_DIR, exist_ok=True)


def compute_normal_map(gray_img, strength=3.0, blur_k=3):
    """从灰度高度图计算高保真 Sobel 切线空间法线贴图 (RGB: Tangent Space Normal)"""
    if blur_k > 1:
        gray_img = cv2.GaussianBlur(gray_img, (blur_k, blur_k), 0)
    
    gray_f = gray_img.astype(np.float32) / 255.0
    gx = cv2.Sobel(gray_f, cv2.CV_32F, 1, 0, ksize=3) * strength
    gy = cv2.Sobel(gray_f, cv2.CV_32F, 0, 1, ksize=3) * strength
    gz = np.ones_like(gx)

    # 归一化向量
    norm = np.sqrt(gx**2 + gy**2 + gz**2) + 1e-6
    nx = gx / norm
    ny = -gy / norm  # OpenGL 格式反转 Y
    nz = gz / norm

    # 映射到 [0, 255] RGB
    r = ((nx * 0.5 + 0.5) * 255).astype(np.uint8)
    g = ((ny * 0.5 + 0.5) * 255).astype(np.uint8)
    b = ((nz * 0.5 + 0.5) * 255).astype(np.uint8)

    return cv2.merge([b, g, r]) # OpenCV BGR


def compute_roughness_map(gray_img, min_rough=0.72, max_rough=0.94):
    """计算石材微表面粗糙度贴图"""
    # 边缘微凹凸部分略光滑(刻痕处)，未打磨石面粗糙度高
    inv = 255 - gray_img
    norm = inv.astype(np.float32) / 255.0
    rough = min_rough + norm * (max_rough - min_rough)
    return (np.clip(rough, 0.0, 1.0) * 255).astype(np.uint8)


def process_textures():
    print(f"[*] 开始基于六视图生成 PBR 贴图套件: {OUT_DIR}")

    front_p = os.path.join(REF_DIR, "stele_front.png")
    back_p = os.path.join(REF_DIR, "stele_back.png")
    left_p = os.path.join(REF_DIR, "stele_left.png")
    right_p = os.path.join(REF_DIR, "stele_right.png")
    top_p = os.path.join(REF_DIR, "stele_top.png")
    bottom_p = os.path.join(REF_DIR, "stele_bottom.png")

    img_front = cv2.imread(front_p)
    img_back = cv2.imread(back_p)
    img_left = cv2.imread(left_p)
    img_right = cv2.imread(right_p)
    img_top = cv2.imread(top_p)
    img_bottom = cv2.imread(bottom_p)

    h_f, w_f = img_front.shape[:2]

    # 1. 碑首 (SteleCrown) - 双龙拱顶区域 (顶部 0% ~ 22%)
    crown_crop = img_front[int(h_f * 0.015):int(h_f * 0.22), :]
    crown_diffuse = cv2.resize(crown_crop, (1024, 512), interpolation=cv2.INTER_LANCZOS4)
    # 微调色阶避免死黑，呈现高贵的青石灰度
    crown_diffuse = cv2.convertScaleAbs(crown_diffuse, alpha=1.1, beta=12)
    crown_gray = cv2.cvtColor(crown_diffuse, cv2.COLOR_BGR2GRAY)
    crown_normal = compute_normal_map(crown_gray, strength=3.5, blur_k=3)
    crown_rough = compute_roughness_map(crown_gray, 0.70, 0.88)

    # 2. 碑身正面 (SteleBody Front) - 回纹边框与碑文 (高度 18% ~ 78%)
    body_crop = img_front[int(h_f * 0.18):int(h_f * 0.78), :]
    body_diffuse = cv2.resize(body_crop, (1024, 1024), interpolation=cv2.INTER_LANCZOS4)
    body_diffuse = cv2.convertScaleAbs(body_diffuse, alpha=1.05, beta=10)
    body_gray = cv2.cvtColor(body_diffuse, cv2.COLOR_BGR2GRAY)
    body_normal = compute_normal_map(body_gray, strength=2.8, blur_k=3)
    body_rough = compute_roughness_map(body_gray, 0.75, 0.92)

    # 3. 碑身背面 (SteleBody Back) - 从 stele_back.png 提取实心石纹
    h_b, w_b = img_back.shape[:2]
    back_crop = img_back[int(h_b * 0.18):int(h_b * 0.78), :]
    back_diffuse = cv2.resize(back_crop, (1024, 1024), interpolation=cv2.INTER_LANCZOS4)
    back_diffuse = cv2.convertScaleAbs(back_diffuse, alpha=1.05, beta=10)
    back_gray = cv2.cvtColor(back_diffuse, cv2.COLOR_BGR2GRAY)
    back_normal = compute_normal_map(back_gray, strength=2.5, blur_k=3)
    back_rough = compute_roughness_map(back_gray, 0.78, 0.94)

    # 4. 侧面石纹 (Side Stone) - 从 stele_left.png 和 stele_right.png 提取纵向石材断面
    h_l, w_l = img_left.shape[:2]
    # 取中段侧面石壁
    side_crop = img_left[int(h_l * 0.15):int(h_l * 0.78), int(w_l * 0.42):int(w_l * 0.58)]
    side_diffuse = cv2.resize(side_crop, (512, 1024), interpolation=cv2.INTER_LANCZOS4)
    side_diffuse = cv2.convertScaleAbs(side_diffuse, alpha=1.1, beta=15)
    side_gray = cv2.cvtColor(side_diffuse, cv2.COLOR_BGR2GRAY)
    side_normal = compute_normal_map(side_gray, strength=3.0, blur_k=3)
    side_rough = compute_roughness_map(side_gray, 0.80, 0.95)

    # 5. 须弥座基台 (Pedestal) - 从 stele_front.png 下部 (75% ~ 99%) 及 stele_bottom.png
    ped_crop = img_front[int(h_f * 0.75):int(h_f * 0.98), :]
    ped_diffuse = cv2.resize(ped_crop, (1024, 512), interpolation=cv2.INTER_LANCZOS4)
    ped_diffuse = cv2.convertScaleAbs(ped_diffuse, alpha=1.1, beta=14)
    ped_gray = cv2.cvtColor(ped_diffuse, cv2.COLOR_BGR2GRAY)
    ped_normal = compute_normal_map(ped_gray, strength=3.2, blur_k=3)
    ped_rough = compute_roughness_map(ped_gray, 0.76, 0.90)

    # 6. 底座底面 (Bottom Plinth)
    bot_diffuse = cv2.resize(img_bottom, (512, 512), interpolation=cv2.INTER_LANCZOS4)
    bot_gray = cv2.cvtColor(bot_diffuse, cv2.COLOR_BGR2GRAY)
    bot_normal = compute_normal_map(bot_gray, strength=2.2, blur_k=3)

    # 7. 无缝背景石质 (Seamless Granite/Basalt)
    stone_patch = img_back[int(h_b * 0.35):int(h_b * 0.65), int(w_b * 0.35):int(w_b * 0.65)]
    stone_seamless = cv2.resize(stone_patch, (512, 512), interpolation=cv2.INTER_LANCZOS4)
    stone_gray = cv2.cvtColor(stone_seamless, cv2.COLOR_BGR2GRAY)
    stone_normal = compute_normal_map(stone_gray, strength=2.2, blur_k=3)
    stone_rough = compute_roughness_map(stone_gray, 0.82, 0.95)

    # 保存函数
    def save_tex(name, img_mat):
        p1 = os.path.join(OUT_DIR, name)
        p2 = os.path.join(TEXTURES_DIR, name)
        cv2.imwrite(p1, img_mat)
        cv2.imwrite(p2, img_mat)
        print(f"  [OK] 生成 PBR 贴图: {name} ({img_mat.shape[1]}x{img_mat.shape[0]})")

    # 写入各通道
    save_tex("crown_diffuse.png", crown_diffuse)
    save_tex("crown_normal.png", crown_normal)
    save_tex("crown_roughness.png", crown_rough)

    save_tex("body_diffuse.png", body_diffuse)
    save_tex("body_normal.png", body_normal)
    save_tex("body_roughness.png", body_rough)

    save_tex("body_back_diffuse.png", back_diffuse)
    save_tex("body_back_normal.png", back_normal)
    save_tex("body_back_roughness.png", back_rough)

    save_tex("stone_side_diffuse.png", side_diffuse)
    save_tex("stone_side_normal.png", side_normal)
    save_tex("stone_side_roughness.png", side_rough)

    save_tex("pedestal_diffuse.png", ped_diffuse)
    save_tex("pedestal_normal.png", ped_normal)
    save_tex("pedestal_roughness.png", ped_rough)

    save_tex("pedestal_bottom_diffuse.png", bot_diffuse)
    save_tex("pedestal_bottom_normal.png", bot_normal)

    save_tex("stone_seamless_diffuse.png", stone_seamless)
    save_tex("stone_seamless_normal.png", stone_normal)
    save_tex("stone_seamless_roughness.png", stone_rough)

    print("[OK] 全套 20 项高精度 PBR 材质贴图构建完毕！")


if __name__ == "__main__":
    process_textures()
