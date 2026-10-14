export const DYNASTY_OPTIONS = [
  { value: 'all', label: '全部', order: 0 },
  { value: 'eastern_han', label: '东汉', order: 1 },
  { value: 'northern_wei', label: '北魏', order: 2 },
  { value: 'tang', label: '唐代', order: 3 },
  { value: 'song', label: '宋代', order: 4 },
  { value: 'yuan', label: '元代', order: 5 },
  { value: 'ming', label: '明代', order: 6 },
  { value: 'qing', label: '清代', order: 7 },
] as const;

export type DynastyValue = typeof DYNASTY_OPTIONS[number]['value'];

export interface SteleItem {
  id: string;
  title: string;
  dynasty: string;
  dynasty_value?: DynastyValue;
  author: string;
  script_type: string;
  weathering_level: '轻度风化' | '中度风化' | '重度风化' | '严重漫漶' | '待评估';
  year: string;
  ganzhi: string;
  location: string;
  museum: string;
  dimensions: string;
  summary: string;
  historical_context: string;
  badges: string[];
  raw_image: string;
  clean_image: string;
  damaged_image: string;
  restored_image?: string;
  fragment_image?: string;
  metrics: {
    psnr: number;
    ssim: number;
    snr_gain: number;
    glyph_completeness: number;
    character_accuracy: number;
  };
  translation: string;
  // 真实馆藏数字化扩展字段 (SteleRecord Schema)
  originalYear?: string;
  rubbingPeriod?: string;
  calligraphyStyle?: string;
  inscriptionAuthor?: string;
  calligrapher?: string;
  collectionInstitution?: string;
  collectionNumber?: string;
  originalLocation?: string;
  currentLocation?: string;
  description?: string;
  sourceUrl?: string;
  imageUrl?: string;
  localImagePath?: string;
  license?: string;
  attribution?: string;
  weatheringLevel?: string;
  imageStatus?: string;
  isDemo?: boolean;
  source_kind?: string;
}

export interface ProcessingParams {
  d0: number; // 截止频率
  filter_order: number; // 滤波器阶数
  h_nlm: number; // NLM 滤波强度
  clahe_clip: number; // CLAHE 对比度限幅
  enhancement_level?: number;
}

export interface ProcessingResult {
  restored_image: string;
  fft_spectrum?: string;
  skeleton_b64?: string;
  cinnabar_b64?: string;
  psnr: number;
  ssim: number;
  snr_gain: number;
  glyph_completeness: number;
  character_accuracy: number;
  processing_time_ms: number;
  stele_id: string;
}

export interface CharacterItem {
  id: string;
  char: string;
  status: 'clear' | 'damaged' | 'variant' | 'restored';
  col: number;
  row: number;
  radical?: string;
  pinyin?: string;
  variant_of?: string;
  explanation?: string;
  damage_level?: number;
  inferred_candidates?: InferredCandidate[];
}

export interface InferredCandidate {
  glyph: string;
  confidence: number;
  evidence: string;
  font_style: string;
  source: string;
}

export interface GraphNode {
  id: string;
  name: string;
  category: 'stele' | 'person' | 'place' | 'office' | 'script';
  value: number;
  symbolSize: number;
  portrait?: string;
  desc?: string;
  role?: string;
  dynasty?: string;
}

export interface GraphLink {
  source: string;
  target: string;
  relation: string;
  weight?: number;
}

export interface GISWaypoint {
  name: string;
  year: string;
  event: string;
  coords: [number, number]; // [lng, lat]
  image?: string;
  role?: string;
}

export interface AblationMetric {
  name: string;
  psnr: number;
  ssim: number;
  time_ms: number;
  color: string;
}
