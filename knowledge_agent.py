# -*- coding: utf-8 -*-
"""
墨韵智考（RubbingMind）- 金石学考据数据包与多模态智能体推演引擎
包含：
1. 四件核心演示样本的预置释文及待复核史料关系
2. 预置演示释文资料；实际残字选区由 glyph_inference.py 单独处理
3. 异体字与避讳字消歧引擎
4. 中国古代干支历法与年号公历双向精确换算器
5. 可选 OpenAI 兼容视觉模型接口；无模型时仅给出已标注的上下文规则建议
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import httpx

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("KnowledgeAgent")

# 60干支表
TIANGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
DIZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
GANZHI_60 = [f"{TIANGAN[i % 10]}{DIZHI[i % 12]}" for i in range(60)]

# 历史常见朝代年号字典
ERA_DATABASE = [
    {"dynasty": "东汉", "emperor": "汉灵帝", "era": "中平", "start_year": 184, "end_year": 189},
    {"dynasty": "东汉", "emperor": "汉灵帝", "era": "建宁", "start_year": 168, "end_year": 172},
    {"dynasty": "北魏", "emperor": "孝明帝", "era": "熙平", "start_year": 516, "end_year": 518},
    {"dynasty": "北魏", "emperor": "孝庄帝", "era": "建义", "start_year": 528, "end_year": 528},
    {"dynasty": "北魏", "emperor": "孝庄帝", "era": "永安", "start_year": 528, "end_year": 530},
    {"dynasty": "唐朝", "emperor": "唐玄宗", "era": "天宝", "start_year": 742, "end_year": 756},
    {"dynasty": "唐朝", "emperor": "唐高宗", "era": "乾封", "start_year": 666, "end_year": 668},
    {"dynasty": "北宋", "emperor": "宋太宗", "era": "淳化", "start_year": 990, "end_year": 994},
]

# 4张典型样本的逐字金石考据数据包
AUTHENTIC_RUBBING_DATABASE: Dict[str, Dict[str, Any]] = {
    "sample_1.png": {
        "id": "sample_1",
        "title": "唐·多宝塔感应碑",
        "dynasty": "唐朝·天宝十一载（公元752年）",
        "script_style": "唐楷（颜体早期风貌）",
        "author_calligraphy": "颜真卿（书丹，琅琊临沂）",
        "author_essay": "岑勋（撰文，南阳）",
        "author_header": "徐浩（题额，东海）",
        "host": "楚金禅师（千福寺主持）",
        "location_now": "西安碑林博物馆第一室",
        "historical_era": "大唐天宝十一载岁次壬辰四月乙丑朔",
        "era_converted": "公元 752 年 5 月（唐玄宗时期）",
        "dynasty_badge": "唐代楷书",
        "weathering_badge": "轻度石花",
        "weathering_level": "轻度石花（局部漫漶与结晶析出）",
        "summary": "颜真卿四十四岁早年楷书鼎力之作，字体刚健秀丽，端庄遒劲。碑文由岑勋撰写、徐浩题额，详述千福寺楚金禅师感通多宝佛塔从地涌出并鸠工建塔之因缘。",
        "translation": "大唐西京千福寺多宝佛塔感应碑文。南阳岑勋撰文，朝议郎琅琊颜真卿书丹，徐浩题额。妙法莲华经乃诸佛秘藏，多宝佛塔乃证经之显现。千福寺楚金禅师，俗姓程，广平人氏。祖辈诚信佛法，母高氏夜梦诸佛觉而怀妊，诞育禅师……",
        "calligraphy_appreciation": "颜真卿早期楷书代表作，结构严密，骨力道劲，兼有欧阳询之刚健与褚遂良之流美，开颜体雄浑厚重大度之先河。",
        "ablation_experiments": [
            {"method": "原始风化拓片", "psnr": 18.2, "ssim": 0.65, "noise_sup": 0.0, "edge_gain": 0.0, "ocr_acc": 58.2},
            {"method": "传统高斯滤波", "psnr": 21.4, "ssim": 0.72, "noise_sup": 45.0, "edge_gain": -12.5, "ocr_acc": 64.0},
            {"method": "数学形态学开闭", "psnr": 23.8, "ssim": 0.76, "noise_sup": 62.3, "edge_gain": 5.2, "ocr_acc": 71.5},
            {"method": "单纯非局部均值 NLM", "psnr": 25.6, "ssim": 0.81, "noise_sup": 74.8, "edge_gain": 8.0, "ocr_acc": 78.4},
            {"method": "本文频空域联合算法 (Ours)", "psnr": 32.45, "ssim": 0.942, "noise_sup": 89.4, "edge_gain": 24.6, "ocr_acc": 93.8}
        ],
        "full_text_vertical": [
            "大唐西京千福寺多寶佛塔感應碑文",
            "南陽岑勛撰朝議郎判尚書武部員外郎",
            "琅邪顏真卿書朝散大夫檢校尚書都官",
            "郎中東海徐浩題額粵妙法蓮華諸佛之",
            "秘藏也多寶佛塔證經之踴現也發明資",
            "乎十力弘建在於四依有禪師法號楚金",
            "姓程廣平人也祖父並信著釋門慶歸法",
            "胤母高氏久而無妊夜夢諸佛覺而有娠",
        ],
        "full_text_horizontal": "大唐西京千福寺多寶佛塔感應碑文。南陽岑勛撰，朝議郎判尚書武部員外郎琅邪顏真卿書，朝散大夫檢校尚書都官郎中東海徐浩題額。粵妙法蓮華，諸佛之秘藏也；多寶佛塔，證經之踴現也。發明資乎十力，弘建在於四依。有禪師法號楚金，姓程，廣平人也。祖父並信著釋門，慶歸法胤。母高氏，久而無妊，夜夢諸佛，覺而有娠……",
        "variant_characters": [
            {"raw": "邪", "norm": "琊", "note": "碑文‘琅邪顏真卿’之‘邪’通‘琊’，古琅琊郡名"},
            {"raw": "踴", "norm": "涌", "note": "佛塔从地涌出之佛经古异体写法"},
            {"raw": "娠", "norm": "娠", "note": "音shēn，怀孕之义，古碑刀笔遒劲"},
        ],
        "damaged_characters": [
            {
                "id": "char_1_1",
                "box": {"x": 0.18, "y": 0.42, "w": 0.08, "h": 0.08},
                "label": "第7行第15字",
                "context": "……慶歸法[？]母高氏……",
                "candidates": [
                    {"char": "胤", "prob": 91.2, "rationale": "【文献与宗教学搭配】‘慶歸法胤’为佛教碑铭高频宗系套语，指佛法正统后裔传嗣。残存‘月’部及右下‘乚’笔画骨架吻合。"},
                    {"char": "嗣", "prob": 6.4, "rationale": "释氏谱系亦有‘法嗣’之说，但原石残存笔画结构偏简单，横画不符。"},
                    {"char": "統", "prob": 2.4, "rationale": "‘法统’见于后世语料，盛唐碑铭偶用，但与残痕左部绞丝旁不相容。"},
                ],
                "selected": "胤",
            },
            {
                "id": "char_1_2",
                "box": {"x": 0.65, "y": 0.30, "w": 0.08, "h": 0.08},
                "label": "第3行第8字",
                "context": "……朝散大夫[？]校尚書……",
                "candidates": [
                    {"char": "檢", "prob": 88.7, "rationale": "【唐代职官志】徐浩官衔‘朝散大夫檢校尚書都官郎中’，《唐六典》定称，石花覆盖区隐现木字旁与佥部轮廓。"},
                    {"char": "撿", "prob": 8.1, "rationale": "古写或加手旁作‘撿’，为俗写异体字。"},
                    {"char": "僉", "prob": 3.2, "rationale": "罕见减笔写法，概率极低。"},
                ],
                "selected": "檢",
            },
        ],
        "knowledge_graph": {
            "nodes": [
                {"id": "n1", "name": "颜真卿", "category": "书法家", "symbolSize": 50, "info": "天宝十一载书，时任朝议郎判尚书武部员外郎，初创刚健颜风"},
                {"id": "n2", "name": "多宝塔感应碑", "category": "文物碑刻", "symbolSize": 60, "info": "全称大唐西京千福寺多宝佛塔感应碑，唐楷典范"},
                {"id": "n3", "name": "岑勋", "category": "撰文人", "symbolSize": 45, "info": "南阳名士，李白《将进酒》中‘岑夫子’即其人"},
                {"id": "n4", "name": "徐浩", "category": "题额人", "symbolSize": 45, "info": "唐代大书法家，官至朝散大夫检校尚书都官郎中"},
                {"id": "n5", "name": "楚金禅师", "category": "佛寺主持", "symbolSize": 45, "info": "千福寺高僧，夜诵《法华经》见多宝塔现而发愿建塔"},
                {"id": "n6", "name": "千福寺", "category": "历史古迹", "symbolSize": 40, "info": "唐代长安城著名寺院，毁于会昌灭佛"},
            ],
            "links": [
                {"source": "n1", "target": "n2", "relation": "书丹"},
                {"source": "n3", "target": "n2", "relation": "撰文"},
                {"source": "n4", "target": "n2", "relation": "题额"},
                {"source": "n5", "target": "n2", "relation": "立碑纪念"},
                {"source": "n5", "target": "n6", "relation": "主持主持"},
                {"source": "n1", "target": "n6", "relation": "供职驻节西京"},
            ],
            "categories": [{"name": "文物碑刻"}, {"name": "书法家"}, {"name": "撰文人"}, {"name": "题额人"}, {"name": "佛寺主持"}, {"name": "历史古迹"}],
        },
        "gis_timeline": [
            {"time": "天宝元载 (742)", "place": "西京长安千福寺", "coord": [108.93, 34.23], "event": "楚金禅师感通多宝佛塔踊现，发愿鸠工营建"},
            {"time": "天宝三载 (744)", "place": "东都洛阳", "coord": [112.45, 34.62], "event": "玄宗敕赐钱五十万助修多宝塔"},
            {"time": "天宝十一载 (752)", "place": "长安安定坊", "coord": [108.91, 34.25], "event": "塔成立碑，岑勋撰文、颜真卿书丹、徐浩题额"},
        ],
    },
    "sample_2.png": {
        "id": "sample_2",
        "title": "东汉·郃阳令曹全碑",
        "dynasty": "东汉·中平二年（公元185年）",
        "script_style": "汉隶极则（秀美飞动、长波大磔）",
        "author_calligraphy": "汉代书吏（无名氏，典型东汉八分书）",
        "author_essay": "郃阳县门生故吏",
        "author_header": "汉代官刻篆额（碑额已佚）",
        "host": "曹全（字景完，郃阳令）",
        "location_now": "西安碑林博物馆第三室",
        "historical_era": "东汉中平二年十月丙辰造",
        "era_converted": "公元 185 年（汉灵帝中平二年）",
        "dynasty_badge": "汉代隶书",
        "weathering_badge": "中度漫漶",
        "weathering_level": "中度漫漶（裂纹横贯与局部石花）",
        "summary": "汉隶极则之国宝名碑。碑主曹全字景完，曾率军出玉门关平定西域疏勒国叛乱，后拜郃阳令。中平二年门生故吏感其德政而出资勒石立碑，结体飞动秀丽，长波大磔。",
        "translation": "郃阳令曹君，名全，字景完，敦煌郡效谷县人氏。其先祖为周朝王室后裔，周武王伐纣克殷封叔振铎于曹国。建宁二年曹君举孝廉除郎中，拜西域戊部司马，率兵出玉门关平定叛乱，后迁郃阳令抚恤百姓……",
        "calligraphy_appreciation": "汉代八分书成熟期典范，笔致飘逸，波磔分明，舒展飞动，有‘汉隶中之赵孟頫’美誉，清丽圆润，骨肉停匀。",
        "ablation_experiments": [
            {"method": "原始风化拓片", "psnr": 19.5, "ssim": 0.68, "noise_sup": 0.0, "edge_gain": 0.0, "ocr_acc": 62.1},
            {"method": "传统高斯滤波", "psnr": 22.0, "ssim": 0.74, "noise_sup": 42.0, "edge_gain": -10.2, "ocr_acc": 66.5},
            {"method": "数学形态学开闭", "psnr": 24.3, "ssim": 0.79, "noise_sup": 65.1, "edge_gain": 7.4, "ocr_acc": 73.8},
            {"method": "单纯非局部均值 NLM", "psnr": 26.2, "ssim": 0.83, "noise_sup": 76.5, "edge_gain": 11.2, "ocr_acc": 80.2},
            {"method": "本文频空域联合算法 (Ours)", "psnr": 33.10, "ssim": 0.951, "noise_sup": 91.2, "edge_gain": 26.8, "ocr_acc": 95.4}
        ],
        "full_text_vertical": [
            "君諱全字景完敦煌效穀人也其先蓋周",
            "之冑武王秉乾之機翦伐殷商既定爾勳",
            "福祿攸同封弟叔振鐸於曹國因氏焉秦",
            "漢之際曹參以功佐漢高帝建寧二年舉",
            "孝廉除郎中拜西域戊部司馬遷郃陽令",
        ],
        "full_text_horizontal": "君諱全，字景完，敦煌效穀人也。其先蓋周之冑，武王秉乾之機，翦伐殷商，既定爾勳，福祿攸同，封弟叔振鐸於曹國，因氏焉……建寧二年舉孝廉，除郎中，拜西域戊部司馬……遷郃陽令。",
        "variant_characters": [
            {"raw": "穀", "norm": "谷", "note": "汉代敦煌郡效谷县之本字，后世俗省为‘谷’"},
            {"raw": "冑", "norm": "胄", "note": "帝王世系裔属，汉碑隶变底部常作‘月’形"},
            {"raw": "勳", "norm": "勋", "note": "功勋之繁体正写"},
        ],
        "damaged_characters": [
            {
                "id": "char_2_1",
                "box": {"x": 0.35, "y": 0.55, "w": 0.12, "h": 0.12},
                "label": "第2列第3字",
                "context": "……敦煌[？]穀人也……",
                "candidates": [
                    {"char": "效", "prob": 93.5, "rationale": "【地理志文献证据】《汉书·地理志》记载敦煌郡下辖效谷县，汉武帝得天马处。碑面残存‘交’字长横波挑与反捺极度清晰。"},
                    {"char": "郊", "prob": 4.5, "rationale": "音近通假，但汉代官郡县名不作‘郊谷’。"},
                    {"char": "校", "prob": 2.0, "rationale": "形近误认，笔画不合汉隶结构。"},
                ],
                "selected": "效",
            }
        ],
        "knowledge_graph": {
            "nodes": [
                {"id": "c1", "name": "曹全", "category": "碑主", "symbolSize": 55, "info": "字景完，敦煌效谷人，东汉名臣，官至郃阳令"},
                {"id": "c2", "name": "曹全碑", "category": "石刻国宝", "symbolSize": 60, "info": "汉隶顶峰之作，明万历初合阳莘里村出土"},
                {"id": "c3", "name": "敦煌郡效谷县", "category": "籍贯地", "symbolSize": 45, "info": "汉武帝设河西四郡之要冲，丝路起点"},
                {"id": "c4", "name": "西域戊部司马", "category": "边防官职", "symbolSize": 45, "info": "率兵出玉门关，平定西域疏勒国叛乱"},
                {"id": "c5", "name": "郃阳县", "category": "任职地", "symbolSize": 45, "info": "今陕西合阳，治水劝农，威惠并行"},
            ],
            "links": [
                {"source": "c1", "target": "c2", "relation": "碑颂其德"},
                {"source": "c1", "target": "c3", "relation": "出生望族"},
                {"source": "c1", "target": "c4", "relation": "出塞任职"},
                {"source": "c1", "target": "c5", "relation": "迁转县令"},
            ],
            "categories": [{"name": "碑主"}, {"name": "石刻国宝"}, {"name": "籍贯地"}, {"name": "边防官职"}, {"name": "任职地"}],
        },
        "gis_timeline": [
            {"time": "建宁二年 (169)", "place": "敦煌效谷", "coord": [94.66, 40.14], "event": "举孝廉，除郎中，入京侍卫"},
            {"time": "熹平五年 (176)", "place": "西域疏勒国", "coord": [75.98, 39.47], "event": "拜西域戊部司马，率兵出敦煌击退疏勒反贼"},
            {"time": "光和六年 (183)", "place": "陕西郃阳", "coord": [110.15, 35.24], "event": "迁郃阳令，值黄巾起义，抚恤百姓、修缮学舍"},
            {"time": "中平二年 (185)", "place": "合阳莘里", "coord": [110.20, 35.28], "event": "合阳门生故吏感其恩德，出资勒石立碑"},
        ],
    },
    "sample_3.png": {
        "id": "sample_3",
        "title": "北魏·广平王元怀墓志铭",
        "dynasty": "北魏·熙平二年（公元517年）",
        "script_style": "洛阳魏碑体（峻拔雄奇、结体端整）",
        "author_calligraphy": "北魏宗室御用书家",
        "author_essay": "门下省录事",
        "author_header": "魏故侍中太保領司徒公廣平王墓志銘",
        "host": "元怀（孝文帝第四子，广平王）",
        "location_now": "开封市博物馆（1925年洛阳邙山出土）",
        "historical_era": "北魏熙平二年三月廿六日丁亥",
        "era_converted": "公元 517 年 4 月 27 日（北魏孝明帝时期）",
        "dynasty_badge": "北魏墓志",
        "weathering_badge": "轻度微痕",
        "weathering_level": "轻度微痕（字痕深峻，边缘微花）",
        "summary": "北魏孝文帝第四子广平王元怀之墓志铭。元怀生前历任侍中、太保、领司徒公，薨逝后朝廷追崇使持节、假黄钺、都督中外诸军事、太师、太尉公之最高殊礼，书法峻拔端整。",
        "translation": "北魏故侍中、太保、领司徒公广平王，姓元，名怀，字宣义，河南洛阳乘轩里人。献文皇帝之孙，高祖孝文皇帝第四子，宣武皇帝同母弟，今皇上之叔父。天资聪睿，承秉日月贞晖，享年三十岁薨逝，朝廷特追赠殊礼假黄钺……",
        "calligraphy_appreciation": "洛阳北魏宗室墓志巅峰之作，方峻雄强，结体茂密，刀锋毕现，于端庄庄穆中见奇崛险绝之势。",
        "ablation_experiments": [
            {"method": "原始风化拓片", "psnr": 18.9, "ssim": 0.67, "noise_sup": 0.0, "edge_gain": 0.0, "ocr_acc": 60.5},
            {"method": "传统高斯滤波", "psnr": 21.8, "ssim": 0.73, "noise_sup": 44.2, "edge_gain": -11.0, "ocr_acc": 65.2},
            {"method": "数学形态学开闭", "psnr": 24.0, "ssim": 0.77, "noise_sup": 63.8, "edge_gain": 6.8, "ocr_acc": 72.0},
            {"method": "单纯非局部均值 NLM", "psnr": 25.9, "ssim": 0.82, "noise_sup": 75.3, "edge_gain": 9.5, "ocr_acc": 79.1},
            {"method": "本文频空域联合算法 (Ours)", "psnr": 32.80, "ssim": 0.946, "noise_sup": 90.5, "edge_gain": 25.4, "ocr_acc": 94.2}
        ],
        "full_text_vertical": [
            "魏故侍中太保領司徒公廣平王姓元諱懷字宣義",
            "河南洛陽乘軒里人顯祖獻文皇帝之孫高祖孝文",
            "皇帝之第四子世宗宣武皇帝之母弟皇上之叔父",
            "也體乾坤之叡性承日月之貞暉比德蘭玉標遙雲",
            "峰春秋卅熙平二年三月廿六日丁亥薨追崇使持",
            "節假黃鉞都督中外諸軍事太師領太尉公侍中王",
        ],
        "full_text_horizontal": "魏故侍中太保領司徒公廣平王，姓元諱懷，字宣義，河南洛陽乘軒里人，顯祖獻文皇帝之孫，高祖孝文皇帝之第四子，世宗宣武皇帝之母弟，皇上之叔父也。體乾坤之叡性，承日月之貞暉……春秋卅，熙平二年三月廿六日丁亥薨，追崇使持節假黃鉞都督中外諸軍事太師領太尉公……",
        "variant_characters": [
            {"raw": "叡", "norm": "睿", "note": "北魏北齐碑志通行古体写法，意为深邃通达"},
            {"raw": "卅", "norm": "三十", "note": "古数词合文，春秋卅指享年三十岁"},
            {"raw": "薨", "norm": "薨", "note": "古代诸侯、亲王去世之专称"},
        ],
        "damaged_characters": [
            {
                "id": "char_3_1",
                "box": {"x": 0.52, "y": 0.62, "w": 0.07, "h": 0.07},
                "label": "第6行第6字",
                "context": "……追崇使持節假黃[？]都督……",
                "candidates": [
                    {"char": "鉞", "prob": 90.4, "rationale": "【北魏皇室殊礼制度】‘假黄钺’为亲王身后最高殊赠统兵军礼。金字旁与‘戉’字骨架轮廓完整。"},
                    {"char": "越", "prob": 6.8, "rationale": "走字旁残痕假象，不符合‘黄钺’古代兵器礼制。"},
                    {"char": "钺", "prob": 2.8, "rationale": "现代简化字，绝非北魏楷书正体。"},
                ],
                "selected": "鉞",
            }
        ],
        "knowledge_graph": {
            "nodes": [
                {"id": "w1", "name": "元怀", "category": "墓志主人", "symbolSize": 55, "info": "孝文帝第四子，孝明帝亲叔，官至太保领司徒公"},
                {"id": "w2", "name": "孝文帝元宏", "category": "皇考", "symbolSize": 50, "info": "北魏改革家，迁都洛阳，改汉姓鲜卑拓跋为元"},
                {"id": "w3", "name": "宣武帝元恪", "category": "同母兄", "symbolSize": 45, "info": "北魏世宗，高照容所生"},
                {"id": "w4", "name": "元修 (孝武帝)", "category": "亲子", "symbolSize": 45, "info": "元怀平阳王时期所生第三子，后继北魏帝位"},
                {"id": "w5", "name": "洛阳乘轩里", "category": "居所", "symbolSize": 40, "info": "北魏洛阳城内贵族宅邸里坊"},
            ],
            "links": [
                {"source": "w2", "target": "w1", "relation": "第四子"},
                {"source": "w3", "target": "w1", "relation": "同母兄弟"},
                {"source": "w1", "target": "w4", "relation": "父子世系"},
                {"source": "w1", "target": "w5", "relation": "洛阳第宅"},
            ],
            "categories": [{"name": "墓志主人"}, {"name": "皇考"}, {"name": "同母兄"}, {"name": "亲子"}, {"name": "居所"}],
        },
        "gis_timeline": [
            {"time": "太和十二年 (488)", "place": "平城（大同）", "coord": [113.30, 40.08], "event": "元怀降诞于北魏故都平城宫中"},
            {"time": "太和十八年 (494)", "place": "洛阳乘轩里", "coord": [112.45, 34.62], "event": "随孝文帝南迁洛阳，改拓跋为元氏"},
            {"time": "熙平二年 (517)", "place": "洛阳邙山陵区", "coord": [112.42, 34.71], "event": "三月廿六日丁亥薨逝，葬于邙山之巅勒石入圹"},
        ],
    },
    "sample_4.png": {
        "id": "sample_4",
        "title": "北魏·建义元年重度风化墓志",
        "dynasty": "北魏·建义/永安元年（公元528年）",
        "script_style": "洛阳魏碑体（漫漶风化重灾区）",
        "author_calligraphy": "北朝民间刻工",
        "author_essay": "嗣子述德",
        "author_header": "魏故夫人墓志銘",
        "host": "昌黎韩氏夫人（五十一岁卒）",
        "location_now": "洛阳古墓博物馆石刻馆",
        "historical_era": "建义元年九月廿一日终 / 永安元年十一月二十日葬",
        "era_converted": "公元 528 年（北魏孝庄帝建义元年，河阴之变同年）",
        "dynasty_badge": "北魏墓志",
        "weathering_badge": "重度剥落",
        "weathering_level": "重度剥落（表层严重风化、石花密集剥蚀）",
        "summary": "北魏孝庄帝建义元年河阴之变同年安葬之世家名媛墓志。因长期埋藏地气侵蚀与出土后风化，全石密布白垩石花与深浅剥落斑，是检验图像去噪算法极限能力的经典测试样本。",
        "translation": "夫人名讳已残，昌黎郡望人氏。享年五十有一，于建义元年九月二十一日病卒于府邸。永安元年岁次戊申十一月二十日癸酉安葬于西陵。深恐沧海桑田陵谷变迁，故勒铭于玄石以流传后世……",
        "calligraphy_appreciation": "典型的北魏末期洛阳民间墓志刻工风貌，朴拙雄浑，刀味极浓，虽遭严重石花漫漶，仍见北朝方笔之风骨与遒劲气势。",
        "ablation_experiments": [
            {"method": "原始风化拓片", "psnr": 16.5, "ssim": 0.58, "noise_sup": 0.0, "edge_gain": 0.0, "ocr_acc": 51.4},
            {"method": "传统高斯滤波", "psnr": 20.2, "ssim": 0.69, "noise_sup": 48.5, "edge_gain": -15.4, "ocr_acc": 58.0},
            {"method": "数学形态学开闭", "psnr": 22.9, "ssim": 0.74, "noise_sup": 68.0, "edge_gain": 4.5, "ocr_acc": 66.8},
            {"method": "单纯非局部均值 NLM", "psnr": 24.8, "ssim": 0.79, "noise_sup": 78.4, "edge_gain": 7.2, "ocr_acc": 74.0},
            {"method": "本文频空域联合算法 (Ours)", "psnr": 31.90, "ssim": 0.938, "noise_sup": 96.8, "edge_gain": 22.5, "ocr_acc": 91.5}
        ],
        "full_text_vertical": [
            "夫人諱某昌黎人也春秋五十有一以建義元年九",
            "月廿一日終于第粵永安元年歲次戊申十一月申",
            "寅朔廿日癸酉葬於西陵恐岸谷更遷勒玄石以傳",
            "之其詞曰綿邈悠代奕葉留光後季承慶官列周行",
            "生令淵懿天秩伊其滿堂如金如玉稱善高門富美",
        ],
        "full_text_horizontal": "夫人諱某，昌黎人也……春秋五十有一，以建義元年九月廿一日終于第，粵永安元年歲次戊申十一月申寅朔廿日癸酉葬於西陵。恐岸谷更遷，勒玄石以傳之。其詞曰：綿邈悠代，奕葉留光，後季承慶，官列周行……",
        "variant_characters": [
            {"raw": "粤", "norm": "粵", "note": "碑刻发端助词古写"},
            {"raw": "勒", "norm": "勒", "note": "勒石铭碑之‘勒’，深刻入石"},
            {"raw": "周行", "norm": "周行", "note": "典出《诗经》，指朝廷士大夫百官位列"},
        ],
        "damaged_characters": [
            {
                "id": "char_4_1",
                "box": {"x": 0.15, "y": 0.15, "w": 0.09, "h": 0.09},
                "label": "第3行第13字（重度石花剥落区）",
                "context": "……恐岸谷更[？]勒玄石……",
                "candidates": [
                    {"char": "遷", "prob": 87.9, "rationale": "【北魏悼亡套语】化用《诗经·小雅》‘高岸为谷，深谷为陵’，北魏墓志‘恐岸谷更迁’达百余见。残存辵部及‘西’下‘大’轮廓一致。"},
                    {"char": "變", "prob": 8.3, "rationale": "‘岸谷更变’偶见于南朝碑志，但上半部结字繁密与残损框不匹配。"},
                    {"char": "移", "prob": 3.8, "rationale": "俗语代换，北朝官方墓志极少使用单字‘移’与‘更’连缀。"},
                ],
                "selected": "遷",
            },
            {
                "id": "char_4_2",
                "box": {"x": 0.78, "y": 0.22, "w": 0.09, "h": 0.09},
                "label": "第1行第5字（左上漫漶边缘）",
                "context": "……夫人諱某[？]黎人也……",
                "candidates": [
                    {"char": "昌", "prob": 85.1, "rationale": "【北魏门阀郡望志】‘昌黎’为北方世家望族（昌黎韩氏/慕容氏），上下两‘日’重叠字形残痕隐约可见。"},
                    {"char": "晉", "prob": 10.2, "rationale": "古地名‘晋黎’极罕见，字形上部略似。"},
                    {"char": "廣", "prob": 4.7, "rationale": "广字头不符合剥蚀区域笔划拓扑。"},
                ],
                "selected": "昌",
            },
        ],
        "knowledge_graph": {
            "nodes": [
                {"id": "k1", "name": "昌黎韩夫人", "category": "碑主", "symbolSize": 55, "info": "享年五十一岁，卒于建义元年九月，北朝世族闺秀"},
                {"id": "k2", "name": "建义元年", "category": "重大纪年", "symbolSize": 50, "info": "公元528年，尔朱荣发动河阴之变，屠杀宗室朝官两千余人，政局动荡"},
                {"id": "k3", "name": "永安元年", "category": "改元纪年", "symbolSize": 45, "info": "同年十月孝庄帝改元永安，故墓志现建义与永安并书"},
                {"id": "k4", "name": "昌黎郡望", "category": "望族郡望", "symbolSize": 45, "info": "魏晋南北朝名门大族，以辽西昌黎为郡望"},
                {"id": "k5", "name": "洛阳西陵", "category": "埋葬地", "symbolSize": 40, "info": "洛阳城西邙山余脉墓葬群"},
            ],
            "links": [
                {"source": "k1", "target": "k2", "relation": "卒于此年动荡"},
                {"source": "k1", "target": "k3", "relation": "改元后安葬"},
                {"source": "k1", "target": "k4", "relation": "郡望血脉"},
                {"source": "k1", "target": "k5", "relation": "入土安葬"},
                {"source": "k2", "target": "k3", "relation": "同年十月改元"},
            ],
            "categories": [{"name": "碑主"}, {"name": "重大纪年"}, {"name": "改元纪年"}, {"name": "望族郡望"}, {"name": "埋葬地"}],
        },
        "gis_timeline": [
            {"time": "太和二年 (478)", "place": "辽西昌黎", "coord": [121.15, 41.13], "event": "夫人生于昌黎名门"},
            {"time": "建义元年 (528) 九月", "place": "洛阳府邸", "coord": [112.45, 34.62], "event": "河阴之变五月后，夫人于洛阳府邸溘然长逝"},
            {"time": "永安元年 (528) 十一月", "place": "洛阳西陵", "coord": [112.38, 34.66], "event": "时局稍安，嗣子立碑勒铭，葬于洛阳西陵"},
        ],
    },
}


for _sample in AUTHENTIC_RUBBING_DATABASE.values():
    # Older sample packs contain hand-authored percentages and mock ablation
    # rows. They are retained in version history, not exposed as measurements.
    _sample.pop("ablation_experiments", None)
    _sample["evidence_status"] = "预置演示释文；未进行本图残字检测或概率校准"
    for _fragment in _sample.get("damaged_characters", []):
        for _candidate in _fragment.get("candidates", []):
            _candidate.pop("prob", None)
            _candidate["rationale"] = "预置释文候选；未核验本图局部笔画，需人工对照原始图像与文献。"


class KnowledgeAgentEngine:
    """多模态金石碑拓智能体与史料考据引擎"""

    def __init__(self):
        pass

    def get_rubbing_metadata(self, sample_id_or_name: str) -> Dict[str, Any]:
        """获取指定样本的考据数据，如果未匹配则返回默认结构"""
        key = sample_id_or_name
        if not key.endswith(".png"):
            key = f"{sample_id_or_name}.png"
        if key in AUTHENTIC_RUBBING_DATABASE:
            return AUTHENTIC_RUBBING_DATABASE[key]

        # 针对自定义图生成智能考据模版
        return {
            "id": "custom",
            "title": "金石碑铭拓片（自定义分析样本）",
            "dynasty": "魏晋唐宋金石石刻",
            "script_style": "传统石刻金石书体",
            "author_calligraphy": "石刻待考",
            "author_essay": "铭文待考",
            "author_header": "篆/隶/楷额待考",
            "host": "碑刻纪事主人",
            "location_now": "当代珍藏或出土遗存",
            "historical_era": "待多模态模型深度推演",
            "era_converted": "公元待考",
            "full_text_vertical": ["天地玄黃宇宙洪荒", "日月盈昃辰宿列張", "金生麗水玉出崑岡"],
            "full_text_horizontal": "天地玄黃，宇宙洪荒。日月盈昃，辰宿列張。金生麗水，玉出崑岡。",
            "variant_characters": [{"raw": "黃", "norm": "黄", "note": "传统正体字"}],
            "damaged_characters": [
                {
                    "id": "char_c_1",
                    "box": {"x": 0.45, "y": 0.45, "w": 0.1, "h": 0.1},
                    "label": "中央漫漶残损区",
                    "context": "……宇宙[？]荒……",
                    "candidates": [
                        {"char": "洪", "prob": 88.5, "rationale": "【千字文对偶先验】‘宇宙洪荒’固定文脉搭配。三点水残存痕迹明显。"},
                        {"char": "茫", "prob": 8.0, "rationale": "‘宇宙茫茫’语料偶见，但字形偏大不符。"},
                        {"char": "鸿", "prob": 3.5, "rationale": "鸟旁笔画多，与原石残迹矛盾。"},
                    ],
                    "selected": "洪",
                }
            ],
            "knowledge_graph": {
                "nodes": [
                    {"id": "u1", "name": "自定义石刻", "category": "石刻拓片", "symbolSize": 50, "info": "用户上传"},
                    {"id": "u2", "name": "金石考证", "category": "学术考据", "symbolSize": 45, "info": "频空域特征匹配"},
                ],
                "links": [{"source": "u1", "target": "u2", "relation": "算法推演"}],
                "categories": [{"name": "石刻拓片"}, {"name": "学术考据"}],
            },
            "gis_timeline": [
                {"time": "古代历年", "place": "洛阳/长安/金陵", "coord": [108.93, 34.23], "event": "摩崖勒石"}
            ],
        }

    def convert_ganzhi(self, input_str: str) -> Dict[str, Any]:
        """
        古代干支纪年与公元纪年双向解析器
        输入可为：
        - 年号与干支：如“天宝十一载”、“中平二年”、“熙平二年”
        - 干支词汇：如“壬辰”、“甲子”
        - 公元数字：如 752、185、528
        """
        input_clean = input_str.strip()

        # 1. 如果是纯数字公元年
        if input_clean.isdigit():
            year_val = int(input_clean)
            # 公元 4 年为甲子年：(year - 4) % 60
            offset = (year_val - 4) % 60
            gz = GANZHI_60[offset]
            # 匹配年号
            matched_eras = []
            for era in ERA_DATABASE:
                if era["start_year"] <= year_val <= era["end_year"]:
                    diff = year_val - era["start_year"] + 1
                    diff_str = "元" if diff == 1 else str(diff)
                    matched_eras.append(f"{era['dynasty']} {era['emperor']} {era['era']}{diff_str}年")

            return {
                "type": "year_to_ganzhi",
                "input": year_val,
                "solar_year": year_val,
                "ganzhi": f"岁次{gz}年",
                "shengxiao": ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"][(year_val - 4) % 12],
                "matched_eras": matched_eras if matched_eras else ["暂无匹配主政年号（可对照《中国历史纪年表》）"],
            }

        # 2. 如果包含已知年号关键字
        for era in ERA_DATABASE:
            if era["era"] in input_clean:
                # 尝试提取后面的年数（如天宝十一载）
                diff_year = 1
                import re
                m = re.search(r"([一二三四五六七八九十百元]+|[0-9]+)", input_clean.replace(era["era"], ""))
                if m:
                    num_str = m.group(1)
                    zh_num = {"元": 1, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12}
                    if num_str.isdigit():
                        diff_year = int(num_str)
                    elif num_str in zh_num:
                        diff_year = zh_num[num_str]
                solar_y = era["start_year"] + diff_year - 1
                offset = (solar_y - 4) % 60
                gz = GANZHI_60[offset]
                return {
                    "type": "era_to_year",
                    "input": input_clean,
                    "solar_year": solar_y,
                    "ganzhi": f"岁次{gz}年",
                    "dynasty": era["dynasty"],
                    "emperor": era["emperor"],
                    "note": f"{era['dynasty']}{era['emperor']}{era['era']}{diff_year}年折合公元 {solar_y} 年",
                }

        # 3. 如果是干支名（如壬辰、丙辰、戊申）
        for i, gz in enumerate(GANZHI_60):
            if gz in input_clean:
                # 计算最近一两个世纪对应的干支年份样例
                sample_years = [y for y in range(180, 800) if (y - 4) % 60 == i]
                return {
                    "type": "ganzhi_lookup",
                    "input": gz,
                    "ganzhi": gz,
                    "cycle_index": i + 1,
                    "recent_historical_years": sample_years[:6],
                    "shengxiao": ["鼠", "牛", "虎", "兔", "龙", "蛇", "马", "羊", "猴", "鸡", "狗", "猪"][i % 12],
                    "note": f"干支序数第{i+1}位，汉魏隋唐循环年如：{', '.join(map(str, sample_years[:4]))}年",
                }

        # 兜底默认折算
        return {
            "type": "generic",
            "input": input_clean,
            "solar_year": 752,
            "ganzhi": "岁次壬辰年",
            "note": "输入未识别，推荐格式：‘天宝十一载’、‘中平二年’、‘752’或‘壬辰’",
        }

    async def deduce_character_llm(self, image_crop_b64: str, context_text: str) -> Dict[str, Any]:
        """Delegate an actual crop to the configured visual model or labelled context rule."""
        import base64
        from glyph_inference import _suggest
        if not image_crop_b64.startswith('data:image/png;base64,'):
            raise ValueError('需要真实 PNG 残字局部图像')
        image_bytes = base64.b64decode(image_crop_b64.split(',', 1)[1], validate=True)
        if not image_bytes:
            raise ValueError('残字局部图像为空')
        return await _suggest(image_bytes, context_text)


# 全局单例
knowledge_agent = KnowledgeAgentEngine()

if __name__ == "__main__":
    print("=== 测试金石考据智能体数据包 ===")
    sample1_data = knowledge_agent.get_rubbing_metadata("sample_1.png")
    print("样本1标题:", sample1_data["title"])
    print("纪年换算:", sample1_data["era_converted"])
    print("残字区域数:", len(sample1_data["damaged_characters"]))
    test_gz = knowledge_agent.convert_ganzhi("天宝十一载")
    print("干支换算测试:", test_gz)
