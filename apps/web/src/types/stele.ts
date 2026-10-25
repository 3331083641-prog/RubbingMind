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

export function roleText(name?: string | null, status?: string) {
  const value = name && !name.startsWith('未核定') ? name : '';
  if (status === 'verified' && value) return value;
  if (status === 'pending_review') return value ? `${value}（待复核）` : '待复核';
  if (status === 'disputed') return '存在争议';
  return '未核定';
}
export interface RubbingAssets { cover: string; readable: string; archive: string; }

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
    psnr: number | null;
    ssim: number | null;
    snr_gain: number | null;
    glyph_completeness: number | null;
    character_accuracy: number | null;
  };
  translation: string;
  // 真实馆藏数字化扩展字段 (SteleRecord Schema)
  originalYear?: string;
  rubbingPeriod?: string;
  calligraphyStyle?: string;
  inscriptionAuthor?: string;
  calligrapher?: string;
  titleCalligrapher?: string;
  engraver?: string;
  steleSubject?: string;
  authorVerification?: string;
  calligrapherVerification?: string;
  titleCalligrapherVerification?: string;
  engraverVerification?: string;
  steleSubjectVerification?: string;
  imageCondition?: string;
  imageConditionReviewStatus?: string;
  physicalStoneWeathering?: string;
  physicalWeatheringEvidence?: string | null;
  assessmentAssetUrls?: { record: string; inputRoi: string; output: string } | null;
  stoneWeathering?: string;
  assessmentRunId?: string;
  assessmentScope?: string;
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
  imageAssets?: RubbingAssets;
  artifactType?: string;
  licenseUrl?: string;
  modifications?: string;
  rubbingCollectionInstitution?: string;
  physicalCollectionInstitution?: string | null;
  evaluationStatus?: string;
  inferenceDemo?: {transcript:string;characters:CharacterItem[];damaged_summary:string;textProvenance?:TextProvenance};
  textProvenance?: TextProvenance;
}

/** Marks generator-made text so it can never be read as an authentic inscription. */
export interface TextProvenance {
  kind: 'synthetic_test_text' | string;
  label: string;
  isAuthenticInscription: boolean;
  generator?: string;
  note?: string;
}

export interface ProcessingParams {
  d0: number; // 截止频率
  filter_order: number; // 滤波器阶数
  h_nlm: number; // NLM 滤波强度
  clahe_clip: number; // CLAHE 对比度限幅
  filter_type: 'adaptive' | 'gaussian' | 'butterworth' | 'notch';
  morph_kernel: number;
}

export interface ProcessingResult {
  runId: string;
  algorithmVersion: string;
  evaluationStatus: 'unassessed' | 'paired_reference';
  outputImages: Record<string, string>;
  adaptiveDiagnostics?: Record<string, unknown> | null;
  engineDiagnosticMetrics?: Record<string, number | null>;
  restored_image: string;
  fft_spectrum?: string;
  skeleton_b64?: string;
  cinnabar_b64?: string;
  psnr: number | null;
  ssim: number | null;
  snr_gain: number | null;
  glyph_completeness: number | null;
  character_accuracy: number | null;
  processing_time_ms: number;
  stele_id: string;
}

export interface ProcessingRun extends ProcessingResult {
  workingImage?: {sourceShape:number[];workingShape:number[];scale:number;interpolation:string};
  randomSeed?: number;
  damageMaskSha256?: string|null;
  outputSha256?: Record<string,string>;
  imageRoles?: Record<string,string>;
  steleId: string;
  inputImageSha256: string;
  algorithmParameters: Record<string, string | number | null>;
  startedAt: string;
  finishedAt: string;
  evaluationMetrics: {psnr:number|null;ssim:number|null};
  diagnosticMetrics: Record<string, number | null>;
  inferenceRecords: unknown[];
  sourceRecords: {title:string|null;url:string|null;license:string|null}[];
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
  textKind?: 'synthetic_test_text' | string;
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
