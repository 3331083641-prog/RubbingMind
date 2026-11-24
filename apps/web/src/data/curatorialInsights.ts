import { SteleItem } from '../types/stele';

export interface BilingualPassage {
  id: string;
  classical: string;
  vernacular: string;
  highlightChars: string[];
  note: string;
}

export interface GlyphEvolutionNote {
  char: string;
  scriptEvolution: string;
  brushwork: string;
  culturalMeaning: string;
}

export interface CuratorialInsight {
  steleId: string;
  tagline: string;
  calligraphySchool: string;
  brushworkSummary: string;
  historicalContext: string;
  passages: BilingualPassage[];
  glyphNotes: GlyphEvolutionNote[];
  suggestedQuestions: string[];
  keepsakeQuotes: { text: string; colophon: string }[];
}

const CURATED_INSIGHTS: Record<string, CuratorialInsight> = {
  'tang-duobao': {
    steleId: 'tang-duobao',
    tagline: '盛唐法度初成 · 颜书早年端严气象',
    calligraphySchool: '唐楷 · 颜真卿四十四岁早年楷法',
    brushworkSummary:
      '此碑结体严密整饬、横细竖粗特征初露端倪，折笔方劲而内含圆润，承褚遂良清劲而开颜体宽博先声，是唐代楷书尚法精神的典范样本。',
    historicalContext:
      '立于唐天宝十一载（公元752年）长安千福寺，由岑勋撰文、颜真卿书丹、徐浩题额，记述楚金禅师诵《法华经》感多宝佛塔涌现而发愿建塔之史事，原石今藏西安碑林。',
    passages: [
      {
        id: 'p1',
        classical: '大唐西京千福寺多寶佛塔感應碑文。南陽岑勛撰，琅邪顏真卿書，東海徐浩題額。',
        vernacular:
          '大唐西京长安千福寺多宝佛塔感应碑文。由南阳人岑勋撰写碑文，琅邪人颜真卿书写碑石，东海人徐浩篆书碑额。',
        highlightChars: ['大', '唐', '多', '寶', '感', '顏'],
        note: '开篇点明“三绝”署名体制：撰文、书丹、题额各司其职，体现盛唐大型佛寺刻碑的礼制规格。',
      },
      {
        id: 'p2',
        classical: '粵妙法蓮華，諸佛之秘藏也；多寶佛塔，證經之踴現也。發明資乎十力，弘建在於四依。',
        vernacular:
          '《妙法莲华经》是诸佛最深奥的法藏；多宝佛塔则是为印证经义而从地涌现的瑞相。阐发经旨仰赖佛之十力，宏建佛塔则有赖弘扬佛法的大德。',
        highlightChars: ['妙', '法', '塔', '感', '應'],
        note: '四六骈偶句式铿锵华美，与颜真卿规矩森严的楷法相得益彰。',
      },
      {
        id: 'p3',
        classical: '有禪師法號楚金，姓程，廣平人也。祖父並信著釋門，慶歸法胤。',
        vernacular:
          '有一位法号楚金的禅师，俗姓程，广平郡人。其祖辈与父辈皆笃信佛门，福泽绵延至法脉后裔。',
        highlightChars: ['禪', '師', '楚', '金', '法'],
        note: '由此转入碑主楚金禅师行状叙事，是研究盛唐长安佛教寺院社会网络的重要一手石刻史料。',
      },
    ],
    glyphNotes: [
      {
        char: '感',
        scriptEvolution: '甲骨文从心从咸，小篆结构趋匀，唐楷收束上密下宽，戈钩舒展定全字重心。',
        brushwork: '右上斜钩长而挺拔，挑钩顿挫有力；下部“心”字三点呼应顾盼，卧钩承托稳如磐石。',
        culturalMeaning: '指“至诚感应”，贯穿全碑宗教与人文精神核心。',
      },
      {
        char: '寶',
        scriptEvolution: '从宀从玉从貝从缶，象征藏于室中的珍器，后世简化为“宝”，石刻拓本完整保存古构。',
        brushwork: '宝盖头宽博覆下，内部笔画繁而不乱，横画间距匀密如算子，尽显唐楷“尚法”精微。',
        culturalMeaning: '既指佛典法宝，亦喻金石刻铭历久弥珍。',
      },
      {
        char: '唐',
        scriptEvolution: '金文作口、庚会意，隶变后广头渐成，唐楷以中宫紧结凸显盛世威仪。',
        brushwork: '广字撇画长舒有力，中间竖画直贯中轴，下口方正饱满，起收笔藏锋严谨。',
        culturalMeaning: '国号题首，字势堂皇正大。',
      },
    ],
    suggestedQuestions: [
      '《多宝塔碑》的撰文者、书丹者与题额者分别是谁？',
      '颜真卿书写《多宝塔碑》时的书法笔法有何艺术特征？',
      '原石现藏何处？碑文与长安千福寺有何历史关联？',
      '如何区分本系统中的“史料著录”与“AI 辅助推演”？',
    ],
    keepsakeQuotes: [
      { text: '多寶佛塔 證經踴現', colophon: '录唐天宝十一载多宝塔感应碑' },
      { text: '發明資乎十力 弘建在於四依', colophon: '盛唐颜真卿楷法微赏' },
      { text: '金石永壽 墨韻長存', colophon: '墨韵智考 · 数字碑林藏印' },
    ],
  },

  'han-caoquan': {
    steleId: 'han-caoquan',
    tagline: '汉隶秀逸绝响 · 蚕头燕尾波磔分明',
    calligraphySchool: '东汉成熟八分隶书',
    brushworkSummary:
      '用笔以圆笔为主、方圆兼备，主横与捺画“蚕头燕尾”舒展飘逸，字形扁方舒朗、行气疏密有致，为东汉隶书秀美一路的巅峰代表。',
    historicalContext:
      '刻于东汉中平二年（公元185年），记述郃阳令曹全（字景完）平定疏勒、抚恤乡里与兴学惠民之政绩；明万历年间出土于陕西合阳，石质细腻故字口历千余年犹存神采。',
    passages: [
      {
        id: 'p1',
        classical: '君諱全，字景完，敦煌效穀人也。其先蓋周之冑。',
        vernacular: '曹君名全，字景完，敦煌郡效穀县人。他的先祖出自周王室后裔。',
        highlightChars: ['君', '全', '景', '完', '敦'],
        note: '东汉碑铭标准起笔体例，先述名讳、表字、籍贯与世系渊源。',
      },
      {
        id: 'p2',
        classical: '重親致歡曹景完，易世載德，不隕其名。及其從政，清擬夷齊，直慕史魚。',
        vernacular: '乡里歌谣称颂曹景完孝敬双亲使全家和乐，世代传承美德不坠家声；步入仕途后清廉比肩伯夷叔齐，刚直仰慕史鱼。',
        highlightChars: ['德', '名', '清', '直', '政'],
        note: '反映汉代察举制下“孝廉”伦理与循吏政治理想。',
      },
      {
        id: 'p3',
        classical: '風雨時節，歲獲豐年，農夫織婦，百工戴恩。中平二年十月丙辰造。',
        vernacular: '风调雨顺、连年丰收，农夫、织妇与百工都感念其德政。中平二年十月丙辰日刊刻立碑。',
        highlightChars: ['風', '雨', '豐', '年', '造'],
        note: '结尾纪年明确，是研究东汉灵帝时期地方治理与丝路军政史的珍贵实物。',
      },
    ],
    glyphNotes: [
      {
        char: '全',
        scriptEvolution: '由篆文人下从玉（或工）隶变而来，汉隶拉宽撇捺成展翼之势。',
        brushwork: '上部人字头如飞檐舒张，末笔波磔挑出轻盈优雅，三横平行而微带弧度。',
        culturalMeaning: '碑主名讳，亦含完满纯粹之德意。',
      },
      {
        char: '德',
        scriptEvolution: '古文字从彳从直从心，表循正道而行于心，汉隶将繁复偏旁化为舒朗横势。',
        brushwork: '左窄右宽，心字底横势延展，点画灵动而不失端雅。',
        culturalMeaning: '汉代颂德碑核心母题。',
      },
    ],
    suggestedQuestions: [
      '《曹全碑》为何被誉为东汉隶书秀美一路的代表？',
      '碑文记述了曹全在西域与郃阳的哪些历史事迹？',
      '“蚕头燕尾”在《曹全碑》中是如何体现的？',
    ],
    keepsakeQuotes: [
      { text: '易世載德 不隕其名', colophon: '录东汉中平二年曹全碑' },
      { text: '風雨時節 歲獲豐年', colophon: '汉隶八分波磔微赏' },
      { text: '清擬夷齊 直慕史魚', colophon: '墨韵智考 · 汉碑留痕' },
    ],
  },

  'wei-yuanhuai': {
    steleId: 'wei-yuanhuai',
    tagline: '北魏洛阳墓志 · 刀笔峻峭骨力洞达',
    calligraphySchool: '北魏楷书（洛阳皇室墓志体）',
    brushworkSummary:
      '方笔峻利、斩钉截铁，横画斜耸上扬、撇捺如刀劈斧削，兼具雄强气骨与精致规整，展现北魏孝文帝迁洛后中原书风与北方刚健气象的融合。',
    historicalContext:
      '北魏熙平年间皇室宗亲元怀墓志，出土于洛阳邙山一带，反映北魏宗室礼制、官职序列与迁洛汉化后的文辞格律。',
    passages: [
      {
        id: 'p1',
        classical: '魏故持節都督諸軍事、驃騎大將軍、太傅、領尚書令、廣平武穆王墓誌銘。',
        vernacular: '北魏已故持节都督诸军事、骠骑大将军、太傅、领尚书令、广平武穆王元怀墓志铭。',
        highlightChars: ['魏', '故', '將', '軍', '誌'],
        note: '北魏宗室墓志题首详列追赠官衔与谥号，是考证北朝职官史的直接金石依据。',
      },
      {
        id: 'p2',
        classical: '風神爽拔，器宇淵深，刊石幽泉，式昭令德。',
        vernacular: '风度神采俊逸超拔，胸襟气度深沉广博，谨刊铭贞石安放幽宫，以长久昭彰美德。',
        highlightChars: ['風', '神', '石', '德'],
        note: '“刊石幽泉”道出了中国古代墓志“防陵谷迁变、存千秋之名”的文化本心。',
      },
    ],
    glyphNotes: [
      {
        char: '魏',
        scriptEvolution: '由委、鬼合体，魏碑刻工常强化折角方棱，赋予结构凌厉雕塑感。',
        brushwork: '左部撇捺开张，右部鬼字竖弯钩遒劲有力，刀意与笔意浑然一体。',
        culturalMeaning: '北朝国号，承载民族融合与书风新变时代印记。',
      },
    ],
    suggestedQuestions: [
      '北魏墓志的“刀笔方折”与唐楷有何风格差异？',
      '元怀墓志与北魏迁都洛阳的历史背景有何关系？',
      '为何墓志常强调“刊石幽泉”？',
    ],
    keepsakeQuotes: [
      { text: '刊石幽泉 式昭令德', colophon: '录北魏洛阳墓志风骨' },
      { text: '風神爽拔 器宇淵深', colophon: '魏碑方笔峻骨微赏' },
    ],
  },

  'wei-jianyi': {
    steleId: 'wei-jianyi',
    tagline: '漫漶残片挑战 · 极端风化微痕抢救样本',
    calligraphySchool: '北魏残石断片（身份待考实验标本）',
    brushworkSummary:
      '石面历经强烈风化与斑驳剥蚀，字口浅淡且伴随密集纸纹与裂隙干扰，是最能检验频空域去噪保真门控与人工协同残字考据边界的高难度样本。',
    historicalContext:
      '本件作为高退化断片实验标本，系统严格遵循“身份待核不臆造人物、不虚构地理迁移轨迹”的学术规范，展示算法如何在信息残缺时保持克制与透明。',
    passages: [
      {
        id: 'p1',
        classical: '建義元年……殘石漫漶，微痕尚存，待考其文。',
        vernacular: '纪年标为建义元年之残断刻石，因风化剥蚀字迹漫漶，残留微弱笔画轮廓，须结合实物与多方史料谨慎互证。',
        highlightChars: ['建', '義', '殘', '石'],
        note: '残片样本凸显数字保护的紧迫性——许多石刻尚未及释读便已濒临消失。',
      },
    ],
    glyphNotes: [
      {
        char: '石',
        scriptEvolution: '象悬崖下磐石之形，历经数千年构形极简而稳固。',
        brushwork: '残片中虽仅存半撇残口，仍可借侧光掠影与骨架提取追踪原刀锋走向。',
        culturalMeaning: '金石不朽之愿与自然风化之力间的永恒对话。',
      },
    ],
    suggestedQuestions: [
      '面对严重漫漶残片，为什么算法不能强行“脑补”缺字？',
      '自适应频空域处理中的“保真门控”起什么作用？',
      '为什么本件样本在时空图谱中不自动生成迁移路线？',
    ],
    keepsakeQuotes: [
      { text: '微痕猶存 守望千年', colophon: '墨韵智考 · 残石抢救数字志' },
      { text: '拂塵見字 格物致知', colophon: '以谦逊算法敬畏残缺史料' },
    ],
  },
};

function cleanTranscriptExcerpt(raw?: string): string {
  if (!raw) return '';
  return raw
    .replace(/\u0000/g, '')
    .split('授權與引用')[0]
    .split('License and attribution')[0]
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(
      (line) =>
        line.length > 0 &&
        !['（各記錄）Transcriptions', '文物統一編號', '釋文'].includes(line) &&
        !/^(?:[贈購赠购]拓[0-9A-Z]+|[ivxlcdm]{1,7})$/i.test(line),
    )
    .join('')
    .slice(0, 120);
}

/**
 * Resolve rich curatorial insight for ANY stele (4 core demos + 28 verified museum artifacts).
 * Clearly separates authentic museum metadata from AI reading guidance.
 */
export function getCuratorialInsight(stele: SteleItem): CuratorialInsight {
  if (CURATED_INSIGHTS[stele.id]) {
    return CURATED_INSIGHTS[stele.id];
  }
  if (stele.id.includes('duobao')) {
    return { ...CURATED_INSIGHTS['tang-duobao'], steleId: stele.id };
  }
  if (stele.id.includes('caoquan')) {
    return { ...CURATED_INSIGHTS['han-caoquan'], steleId: stele.id };
  }

  const excerpt = cleanTranscriptExcerpt(stele.translation);
  const firstClause = excerpt ? excerpt.slice(0, 44) + (excerpt.length > 44 ? '……' : '') : `《${stele.title}》原拓著录存世，现藏${stele.collectionInstitution || stele.museum}。`;
  const quoteText = excerpt
    ? excerpt.replace(/[。，、；：（）()□\s]/g, '').slice(0, 8) || stele.title.slice(0, 8)
    : stele.title.slice(0, 10);

  return {
    steleId: stele.id,
    tagline: `${stele.dynasty} · ${stele.script_type || '传世石刻'}真实馆藏拓本`,
    calligraphySchool: `${stele.dynasty} · ${stele.script_type || '金石刻本'}`,
    brushworkSummary: `本件《${stele.title}》属${stele.dynasty}${stele.script_type || '石刻'}传世拓本（影像状况：${stele.imageCondition || '待人工复核'}）。建议结合三维考古侧光掠影与频空域微痕对比，细察原石刀锋转折与纸墨浓淡层次。`,
    historicalContext: `原刻年代著录为 ${stele.originalYear || stele.year || '待考'}，数字拓本由 ${stele.collectionInstitution || stele.museum} 公开著录（馆藏号 ${stele.collectionNumber || '详见馆方档案'}，许可 ${stele.license || '开放著录'}）。所有人物与地点未核定项均按馆方原样保留。`,
    passages: [
      {
        id: 'p1',
        classical: firstClause,
        vernacular: `据馆藏著录整理：本段摘自《${stele.title}》馆方释文或档案记录。对于漫漶残缺处，系统保留原貌并支持进入右侧“实际残字推演”框选核验，不以模型生成替代原始考据。`,
        highlightChars: Array.from(quoteText).slice(0, 5),
        note: `来源标注：${stele.collectionInstitution || stele.museum} · ${stele.license || '馆藏著录'}`,
      },
    ],
    glyphNotes: [
      {
        char: quoteText[0] || '墨',
        scriptEvolution: `${stele.dynasty}${stele.script_type || '碑刻'}典型结体特征，反映当时书写与石刻摹勒工艺的互动。`,
        brushwork: '可切换“笔画拓扑骨架”或“考古斜射光”观察主笔骨力与边廓磨损细节。',
        culturalMeaning: '单字即时代缩影，连接古代书法审美与当代数字保护。',
      },
    ],
    suggestedQuestions: [
      `《${stele.title}》的撰文者、书丹者及馆藏来源是什么？`,
      `本件拓本的影像损伤状况与授权许可是怎样的？`,
      `如何用频空域自适应算法对这件拓本进行保守微痕增强？`,
    ],
    keepsakeQuotes: [
      {
        text: quoteText.length >= 4 ? `${quoteText.slice(0, 4)} ${quoteText.slice(4, 8)}`.trim() : stele.title,
        colophon: `${stele.dynasty} · ${stele.title}`,
      },
      { text: '貞石傳拓 墨韻流芳', colophon: `观《${stele.title}》有记` },
    ],
  };
}
