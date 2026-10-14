# -*- coding: utf-8 -*-
"""
生成金石碑刻高精度 PBR 贴图套件：
1. 龙纹碑首 (Crown) 漫反射与法线贴图
2. 碑身铭文与回纹边框 (Body & Inscription) 漫反射与法线贴图
3. 三阶莲瓣基座 (Pedestal) 漫反射与法线贴图
4. 粗矿古石材侧面与背面 (Stone Material) 漫反射与法线贴图
"""

import os
import cv2
import numpy as np
from PIL import Image

BASE_DIR = r"D:\RubbingMind"
REF_DIR = os.path.join(BASE_DIR, "design", "references", "stele")
OUT_DIR = os.path.join(BASE_DIR, "apps", "web", "public", "assets", "stele", "model3d")
os.makedirs(OUT_DIR, exist_ok=True)

def generate_normal_map(gray_img, strength=2.5):
    """通过 Sobel 算子计算切线空间法线贴图"""
    gray_f = gray_img.astype(np.float32) / 255.0
    sobel_x = cv2.Sobel(gray_f, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray_f, cv2.CV_32F, 0, 1, ksize=3)
    
    # 建立法向量并归一化到 [0, 255] RGB
    dx = -sobel_x * strength
    dy = -sobel_y * strength
    dz = np.ones_like(dx)
    
    norm = np.sqrt(dx**2 + dy**2 + dz**2)
    norm[norm == 0] = 1.0
    
    nx = (dx / norm * 0.5 + 0.5) * 255.0
    ny = (dy / norm * 0.5 + 0.5) * 255.0
    nz = (dz / norm * 0.5 + 0.5) * 255.0
    
    normal_map = np.stack([nx, ny, nz], axis=2).astype(np.uint8)
    return normal_map

def generate_roughness_map(gray_img):
    """根据灰度反相与微对比度生成粗糙度贴图 (0.75 ~ 0.95)"""
    roughness = 255 - cv2.GaussianBlur(gray_img, (5, 5), 0)
    roughness = (roughness * 0.2 + 200).clip(185, 245).astype(np.uint8)
    return roughness

def main():
    front_path = os.path.join(REF_DIR, "stele_front.jpg")
    side_path = os.path.join(REF_DIR, "stele_side.jpg")
    top_path = os.path.join(REF_DIR, "stele_top.jpg")
    
    front_img = cv2.imread(front_path)
    side_img = cv2.imread(side_path)
    top_img = cv2.imread(top_path)
    
    if front_img is None:
        print("Error: stele_front.jpg not found")
        return
        
    H, W, _ = front_img.shape
    print(f"Front image loaded: {W}x{H}")
    
    # 1. 裁剪龙纹碑首 (Crown: y ~ 20 to y ~ 205, x ~ 235 to x ~ 585)
    # 自动定位碑首区域
    crown_crop = front_img[18:208, 235:585]
    crown_resized = cv2.resize(crown_crop, (1024, 512), interpolation=cv2.INTER_LANCZOS4)
    crown_gray = cv2.cvtColor(crown_resized, cv2.COLOR_BGR2GRAY)
    crown_normal = generate_normal_map(crown_gray, strength=3.5)
    crown_roughness = generate_roughness_map(crown_gray)
    
    cv2.imwrite(os.path.join(OUT_DIR, "crown_diffuse.png"), crown_resized)
    cv2.imwrite(os.path.join(OUT_DIR, "crown_normal.png"), crown_normal)
    cv2.imwrite(os.path.join(OUT_DIR, "crown_roughness.png"), crown_roughness)
    print("Crown textures generated.")
    
    # 2. 碑身与铭文回纹区域 (Body & Inscription: y ~ 195 to y ~ 785, x ~ 235 to x ~ 585)
    body_crop = front_img[195:785, 235:585]
    body_resized = cv2.resize(body_crop, (1024, 1024), interpolation=cv2.INTER_LANCZOS4)
    body_gray = cv2.cvtColor(body_resized, cv2.COLOR_BGR2GRAY)
    body_normal = generate_normal_map(body_gray, strength=2.8)
    body_roughness = generate_roughness_map(body_gray)
    
    cv2.imwrite(os.path.join(OUT_DIR, "body_diffuse.png"), body_resized)
    cv2.imwrite(os.path.join(OUT_DIR, "body_normal.png"), body_normal)
    cv2.imwrite(os.path.join(OUT_DIR, "body_roughness.png"), body_roughness)
    print("Body textures generated.")
    
    # 3. 三阶莲瓣底座 (Pedestal: y ~ 785 to y ~ 970, x ~ 140 to x ~ 680)
    ped_crop = front_img[785:970, 140:680]
    ped_resized = cv2.resize(ped_crop, (1024, 512), interpolation=cv2.INTER_LANCZOS4)
    ped_gray = cv2.cvtColor(ped_resized, cv2.COLOR_BGR2GRAY)
    ped_normal = generate_normal_map(ped_gray, strength=3.0)
    ped_roughness = generate_roughness_map(ped_gray)
    
    cv2.imwrite(os.path.join(OUT_DIR, "pedestal_diffuse.png"), ped_resized)
    cv2.imwrite(os.path.join(OUT_DIR, "pedestal_normal.png"), ped_normal)
    cv2.imwrite(os.path.join(OUT_DIR, "pedestal_roughness.png"), ped_roughness)
    print("Pedestal textures generated.")
    
    # 4. 侧面与背部风化青石岩层 (Stone Texture: from side_img)
    side_crop = side_img[200:750, 460:560]
    side_resized = cv2.resize(side_crop, (512, 1024), interpolation=cv2.INTER_LANCZOS4)
    side_gray = cv2.cvtColor(side_resized, cv2.COLOR_BGR2GRAY)
    side_normal = generate_normal_map(side_gray, strength=2.2)
    side_roughness = generate_roughness_map(side_gray)
    
    cv2.imwrite(os.path.join(OUT_DIR, "stone_side_diffuse.png"), side_resized)
    cv2.imwrite(os.path.join(OUT_DIR, "stone_side_normal.png"), side_normal)
    cv2.imwrite(os.path.join(OUT_DIR, "stone_side_roughness.png"), side_roughness)
    print("Side stone textures generated.")
    
    # 5. 生成高分辨率通用风化青石底材 (Base Stone Seamless Texture: 1024x1024)
    # 混合正面与侧面石材纹理
    base_stone = np.zeros((1024, 1024, 3), dtype=np.uint8)
    base_stone[:512, :512] = cv2.resize(side_crop, (512, 512))
    base_stone[:512, 512:] = cv2.flip(cv2.resize(side_crop, (512, 512)), 1)
    base_stone[512:, :512] = cv2.flip(cv2.resize(side_crop, (512, 512)), 0)
    base_stone[512:, 512:] = cv2.flip(cv2.resize(side_crop, (512, 512)), -1)
    # 平滑接缝
    base_stone = cv2.GaussianBlur(base_stone, (3, 3), 0)
    base_gray = cv2.cvtColor(base_stone, cv2.COLOR_BGR2GRAY)
    base_normal = generate_normal_map(base_gray, strength=2.0)
    base_roughness = generate_roughness_map(base_gray)
    
    cv2.imwrite(os.path.join(OUT_DIR, "stone_seamless_diffuse.png"), base_stone)
    cv2.imwrite(os.path.join(OUT_DIR, "stone_seamless_normal.png"), base_normal)
    cv2.imwrite(os.path.join(OUT_DIR, "stone_seamless_roughness.png"), base_roughness)
    print("Seamless stone textures generated.")
    print("All PBR textures generated successfully in:", OUT_DIR)

if __name__ == "__main__":
    main()
