# -*- coding: utf-8 -*-
"""
墨韵智考（RubbingMind）- 碑拓样本图自动准备与高仿真生成模块
支持：
1. 本地真迹图像优先加载（用户上传的真实高精度拓片）
2. 网络历史碑刻拓片自动下载（超时、UA 伪装、防盗链兜底）
3. 本地 Pillow + OpenCV 高仿真数字碑刻合成双保险（传统从右至左竖排、石材肌理、椒盐石花、斜向裂纹、局部风化漫漶）
"""

import os
import sys
import shutil
import logging
import random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("SampleGenerator")

# 基础路径定义
# Label shown wherever sample_4 text is displayed or retrieved (see data/catalog/core_samples.json).
SYNTHETIC_TEXT_LABEL = "合成测试文本（sample_generator 生成，非真实释文）"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.join(BASE_DIR, "static", "samples")

# 4张核心样本真迹候选路径（基于仓库内置的高清拓片母本）
USER_UPLOADED_CANDIDATES = {
    "sample_1.png": [
        os.path.join(BASE_DIR, "assets", "source", "stele-assets", "rubbings", "stele_tang_duobao_damaged.png"),
        os.path.join(BASE_DIR, "apps", "web", "public", "assets", "stele", "rubbings", "stele_tang_duobao_damaged.png")
    ],
    "sample_2.png": [
        os.path.join(BASE_DIR, "assets", "source", "stele-assets", "rubbings", "stele_han_caoquan.png"),
        os.path.join(BASE_DIR, "apps", "web", "public", "assets", "stele", "rubbings", "stele_han_caoquan.png")
    ],
    "sample_3.png": [
        os.path.join(BASE_DIR, "assets", "source", "stele-assets", "rubbings", "stele_wei_yuanhuai.png"),
        os.path.join(BASE_DIR, "apps", "web", "public", "assets", "stele", "rubbings", "stele_wei_yuanhuai.png")
    ],
    "sample_4.png": [
        os.path.join(BASE_DIR, "assets", "source", "stele-assets", "rubbings", "stele_wei_jianyi_fragment.png"),
        os.path.join(BASE_DIR, "apps", "web", "public", "assets", "stele", "rubbings", "stele_wei_jianyi_fragment.png")
    ],
}

# 网络真实拓片原图下载地址
REMOTE_SAMPLE_URLS = {
    "sample_1.png": {
        "url": "http://www.yueyaa.com/uploads/imgzt/D835C9D03ACBE598.jpg",
        "title": "唐·多宝塔感应碑（颜真卿书丹）",
        "font_preference": ["simkai.ttf", "simsun.ttc", "simhei.ttf"],
        "lines": [
            "大唐西京千福寺多寶佛塔感應碑文",
            "南陽岑勛撰朝議郎判尚書武部員外郎",
            "琅邪顏真卿書朝散大夫檢校尚書都官",
            "郎中東海徐浩題額粵妙法蓮華諸佛之",
            "秘藏也多寶佛塔證經之踴現也發明資",
            "乎十力弘建在於四依有禪師法號楚金",
            "姓程廣平人也祖父並信著釋門慶歸法",
            "胤母高氏久而無妊夜夢諸佛覺而有娠",
        ],
    },
    "sample_2.png": {
        "url": "https://p1.itc.cn/q_70/images03/20230211/2dfe42c409124186a013f529b662faca.jpeg",
        "title": "东汉·郃阳令曹全碑（汉隶极则）",
        "font_preference": ["STLITI.TTF", "simkai.ttf", "simsun.ttc"],
        "lines": [
            "君諱全字景完敦煌效穀人也其先蓋周",
            "之冑武王秉乾之機翦伐殷商既定爾勳",
            "福祿攸同封弟叔振鐸於曹國因氏焉秦",
            "漢之際曹參以功佐漢高帝建寧二年舉",
            "孝廉除郎中拜西域戊部司馬遷郃陽令",
        ],
    },
    "sample_3.png": {
        "url": "http://www.dengdingsheng.com/zb_users/upload/2021/01/20210131102030161205963077659.jpg",
        "title": "北魏·广平王元怀墓志铭（魏碑皇室世系）",
        "font_preference": ["simkai.ttf", "simsun.ttc", "simhei.ttf"],
        "lines": [
            "魏故侍中太保領司徒公廣平王姓元諱懷字宣義",
            "河南洛陽乘軒里人顯祖獻文皇帝之孫高祖孝文",
            "皇帝之第四子世宗宣武皇帝之母弟皇上之叔父",
            "也體乾坤之叡性承日月之貞暉比德蘭玉標遙雲",
            "峰春秋卅熙平二年三月廿六日丁亥薨追崇使持",
            "節假黃鉞都督中外諸軍事太師領太尉公侍中王",
        ],
    },
    "sample_4.png": {
        "url": "http://www.yac8.com/upFiles/infoImg/201607/2016071560987609.jpg",
        "title": "北魏·建义元年重度风化墓志（河阴之变重度石花）",
        # The lines below are generator-authored test text, not an authentic inscription.
        "text_provenance": SYNTHETIC_TEXT_LABEL,
        "font_preference": ["simkai.ttf", "simsun.ttc", "simhei.ttf"],
        "lines": [
            "夫人諱某昌黎人也春秋五十有一以建義元年九",
            "月廿一日終于第粵永安元年歲次戊申十一月申",
            "寅朔廿日癸酉葬於西陵恐岸谷更遷勒玄石以傳",
            "之其詞曰綿邈悠代奕葉留光後季承慶官列周行",
            "生令淵懿天秩伊其滿堂如金如玉稱善高門富美",
        ],
    },
}


def find_system_font(preference_list):
    """探测 Windows 系统字库中匹配的字体"""
    fonts_dir = r"C:\Windows\Fonts"
    for fname in preference_list:
        full_p = os.path.join(fonts_dir, fname)
        if os.path.exists(full_p):
            return full_p
    # 兜底常见默认字体
    fallbacks = ["simkai.ttf", "STLITI.TTF", "simsun.ttc", "simhei.ttf", "msyh.ttc", "arial.ttf"]
    for fname in fallbacks:
        full_p = os.path.join(fonts_dir, fname)
        if os.path.exists(full_p):
            return full_p
    return None


def download_remote_image(url, target_path, timeout=5):
    """尝试下载网络图片，设置 UA 和 Referer"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
    }
    try:
        import requests
        resp = requests.get(url, headers=headers, timeout=timeout, verify=False)
        if resp.status_code == 200 and len(resp.content) > 10240:
            # 校验是否为合法图片
            img_arr = np.frombuffer(resp.content, dtype=np.uint8)
            decoded = cv2.imdecode(img_arr, cv2.IMREAD_COLOR)
            if decoded is not None and decoded.shape[0] > 100 and decoded.shape[1] > 100:
                with open(target_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"网络拓片下载成功: {os.path.basename(target_path)} ({len(resp.content)} bytes)")
                return True
    except Exception as e:
        logger.warning(f"网络拓片下载失败 [{url}]: {e}")
    return False


def synthesize_rubbing_image(sample_key, target_path, width=800, height=1000):
    """
    基于 PIL + OpenCV 生成逼真高仿真黑底白字传统竖排碑拓图像
    具备：
    1. 传统古籍从右向左、从上至下的竖排排版；
    2. 石质粗糙背景底噪（微弱噪点与结晶反光）；
    3. 拓印书法白字（带微小墨晕渗化与刀刻崩刃效果）；
    4. 椒盐石花白斑（局部密集、形状不规则的点状石花剥落）；
    5. 斜向石材裂纹与断层折痕；
    6. 局部风化漫漶掩码（高斯失真与笔画剥蚀）。
    """
    info = REMOTE_SAMPLE_URLS.get(sample_key, {})
    lines = info.get("lines", ["墨韻智考金石碑拓"])
    font_path = find_system_font(info.get("font_preference", ["simkai.ttf"]))

    # 1. 创建石材黑色基底（深灰黑 ~ 纯黑：RGB 12~24）
    base_color = random.randint(14, 22)
    img_pil = Image.new("RGB", (width, height), color=(base_color, base_color, base_color))
    draw = ImageDraw.Draw(img_pil)

    # 2. 从右至左竖排绘制文字
    num_cols = len(lines)
    col_width = (width - 120) // max(1, num_cols)
    char_size = min(int(col_width * 0.72), 48)

    try:
        font = ImageFont.truetype(font_path, char_size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    # 从右侧起排
    start_x = width - 80 - col_width // 2
    for col_idx, line_text in enumerate(lines):
        curr_x = start_x - col_idx * col_width
        curr_y = 60
        for char in line_text:
            if curr_y + char_size > height - 60:
                break
            # 拓片白字带有微小灰度变化（白至浅灰）
            ink_val = random.randint(220, 252)
            draw.text((curr_x - char_size // 2, curr_y), char, font=font, fill=(ink_val, ink_val, ink_val))
            curr_y += int(char_size * 1.25)

    # 转换为 OpenCV BGR 格式
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    # 3. 模拟石材表面高频颗粒微噪点 (Rock Surface Noise)
    noise = np.random.normal(0, 10, img_cv.shape).astype(np.float32)
    img_cv = np.clip(img_cv.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    # 4. 模拟石材裂纹 (Stone Cracks)
    num_cracks = random.randint(2, 4)
    for _ in range(num_cracks):
        pt1 = (random.randint(0, width), random.randint(0, height // 3))
        pt2 = (random.randint(0, width), random.randint(height * 2 // 3, height))
        # 绘制断续裂纹折线
        curr = pt1
        crack_color = (random.randint(180, 230), random.randint(180, 230), random.randint(180, 230))
        steps = random.randint(6, 12)
        for s in range(steps):
            t = (s + 1) / steps
            nxt = (
                int(pt1[0] + (pt2[0] - pt1[0]) * t + random.randint(-15, 15)),
                int(pt1[1] + (pt2[1] - pt1[1]) * t + random.randint(-15, 15)),
            )
            thickness = random.randint(1, 2)
            cv2.line(img_cv, curr, nxt, crack_color, thickness)
            curr = nxt

    # 5. 模拟椒盐石花白斑 (Stone Efflorescence & Salt Noise)
    # 随机生成大量微小白斑与中型石花斑块
    salt_mask = np.zeros((height, width), dtype=np.uint8)
    num_salt_dots = random.randint(3000, 7000)
    ys = np.random.randint(0, height, num_salt_dots)
    xs = np.random.randint(0, width, num_salt_dots)
    salt_mask[ys, xs] = 255

    # 形态学膨胀让石花呈现不规则团簇状
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    salt_mask = cv2.dilate(salt_mask, kernel, iterations=1)
    # 随机滤除一部分
    salt_mask = cv2.bitwise_and(salt_mask, (np.random.rand(height, width) > 0.4).astype(np.uint8) * 255)
    # 叠加到原图
    salt_val = (np.random.rand(height, width, 1) * 160 + 90).astype(np.uint8)
    img_cv = np.where(salt_mask[:, :, None] > 0, np.maximum(img_cv, salt_val), img_cv)

    # 6. 模拟局部重度风化漫漶斑块 (Weathering Erosion Mask)
    # 在特定角落或中部生成大面积风化磨损区
    num_weather_spots = random.randint(2, 4)
    weather_mask = np.zeros((height, width), dtype=np.float32)
    for _ in range(num_weather_spots):
        cx, cy = random.randint(100, width - 100), random.randint(100, height - 100)
        radius = random.randint(60, 140)
        cv2.circle(weather_mask, (cx, cy), radius, 1.0, -1)

    weather_mask = cv2.GaussianBlur(weather_mask, (99, 99), 30)
    # 在磨损区文字对比度下降、石花更密集
    blurred = cv2.GaussianBlur(img_cv, (9, 9), 3)
    weather_mask_3c = np.repeat(weather_mask[:, :, None], 3, axis=2)
    img_cv = (img_cv * (1 - weather_mask_3c * 0.5) + blurred * (weather_mask_3c * 0.5)).astype(np.uint8)

    # 保存合成图（统一使用 imencode 配合 tofile 确保中文路径绝对安全）
    success, encoded = cv2.imencode(".png", img_cv)
    if success:
        encoded.tofile(target_path)
        logger.info(f"本地高仿真碑拓合成成功: {os.path.basename(target_path)} [800x1000]")
        return True
    return False


def ensure_samples():
    """
    检查并保证 static/samples 目录下 sample_1.png 到 sample_4.png 100% 存在且有效。
    优先级顺序：
    1. 现有文件有效性检测
    2. 用户附件已上传原图拷贝
    3. 网络官方原图抓取
    4. 本地 PIL/OpenCV 高保真合成兜底
    """
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    results = {}

    for i in range(1, 5):
        key = f"sample_{i}.png"
        target_path = os.path.join(SAMPLES_DIR, key)

        # 检查是否已存在且文件大于 5KB
        if os.path.exists(target_path) and os.path.getsize(target_path) > 5120:
            logger.info(f"样本已存在且有效: {key}")
            results[key] = target_path
            continue

        # 策略 1: 优先检查并拷贝本地用户已上传原图
        copied_from_user = False
        candidates = USER_UPLOADED_CANDIDATES.get(key, [])
        for cand_path in candidates:
            if os.path.exists(cand_path) and os.path.getsize(cand_path) > 5120:
                try:
                    shutil.copy2(cand_path, target_path)
                    logger.info(f"已成功从用户真迹备份加载样本: {key} <- {os.path.basename(cand_path)}")
                    results[key] = target_path
                    copied_from_user = True
                    break
                except Exception as e:
                    logger.warning(f"拷贝用户真迹失败: {e}")

        if copied_from_user:
            continue

        # 策略 2: 尝试网络下载
        net_info = REMOTE_SAMPLE_URLS.get(key)
        download_success = False
        if net_info and "url" in net_info:
            download_success = download_remote_image(net_info["url"], target_path)

        if download_success and os.path.exists(target_path) and os.path.getsize(target_path) > 5120:
            results[key] = target_path
            continue

        # 策略 3: 本地高逼真 PIL/OpenCV 碑拓合成双保险
        logger.warning(f"网络与外部资源不可用，启动本地高仿真碑拓合成引擎: {key}")
        synth_success = synthesize_rubbing_image(key, target_path)
        if synth_success and os.path.exists(target_path):
            results[key] = target_path
        else:
            logger.error(f"样本初始化严重异常: {key}")

    return results


if __name__ == "__main__":
    print("=== 正在检查并自动准备 4 张碑刻拓片样本 ===")
    res = ensure_samples()
    print("准备结果:")
    for k, v in res.items():
        print(f"  {k} -> {v} (大小: {os.path.getsize(v):,} 字节)")
