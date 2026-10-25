/**
 * 报告页数据类型。字段沿用现有 API（f0c5886）；REPORT_DATA_SPEC v1 的新字段
 * （displayName / heldOut / appliedStatus / isPassthrough 等）均为可选，后端提供后自动生效。
 */
export type Decision = { operator: string; reason?: string };
export type FidelityGate = { accepted?: boolean; strongEdgeRetention?: number; meanAbsoluteChange?: number; contrastRatio?: number; reasons?: string[]; basis?: string };

export type AppliedStatus =
  | 'baseline' | 'processed' | 'passthrough' | 'passthrough_not_applicable'
  | 'processed_not_applicable_label' | 'failed' | 'undetermined';

export interface ExperimentRow {
  sampleId: string;
  dynasty?: string;
  split?: string;
  caseId?: string;
  degradation: string;
  strength?: number;
  seed?: number;
  method: string;
  applicability?: string;
  processingMs?: number | null;
  error?: string | null;
  sourceSha256?: string;
  reference?: string | null;
  referenceSha256?: string | null;
  input?: string | null;
  inputSha256?: string | null;
  output?: string | null;
  outputSha256?: string | null;
  algorithmVersion?: string;
  diagnostics?: { version?: string; decisions?: Decision[]; fidelityGate?: FidelityGate; selectedOutput?: string } | null;
  diagnosticsOperators?: string[];
  psnr?: number | null;
  ssim?: number | null;
  edgeF1?: number | null;
  thinStrokeMae?: number | null;
  inputPsnr?: number | null;
  inputSsim?: number | null;
  psnrDeltaFromInput?: number | null;
  negativeLift?: boolean | null;
  fidelityAccepted?: boolean | null;
  // REPORT_DATA_SPEC §1(b)/§9（可选）
  appliedStatus?: AppliedStatus;
  isPassthrough?: boolean | null;
  changedPixelRatio?: number | null;
  changedPixelCount?: number | null;
  maxAbsDiff?: number | null;
  byteIdentical?: boolean | null;
  crop?: number[];
  /** DER appliedStatusDetail：rounding / other，或 DER 长值 not-applicable-but-modified-*（E-05）；缺省不猜测。 */
  appliedStatusDetail?: string | null;
  /** 本行状态来自哪里：DER（derived/applied_status，pixel-equal-v1）或前端兜底。由适配层写入。 */
  statusSource?: 'DER' | 'frontend';
}

export interface BatchRegistry {
  id: string;
  directory?: string;
  rowCount?: number;
  sampleCount?: number;
  limitations?: string[];
  imageComparisonAvailable?: boolean;
  metricsOnly?: boolean;
  historicalWarning?: string | null;
  // REPORT_DATA_SPEC §1(a)（可选）
  displayName?: string;
  heldOut?: boolean;
  protocolNote?: string;
  appliedStatusAvailable?: boolean;
  // ExperimentBatchMeta（agent/arch-backend R1-3）
  splitAvailable?: boolean;
  splits?: Record<string, number>;
  rowsWithoutSplit?: number;
  status?: 'valid' | 'historical-leakage' | 'metrics-only';
  statusReasons?: string[];
  defaultForReport?: boolean;
  defaultForReportBasis?: string | null;
}

export interface BatchDetail {
  experimentId?: string;
  registry: BatchRegistry;
  rows: ExperimentRow[];
  summary?: Record<string, unknown>[];
  config?: Record<string, unknown> & { referenceNote?: string; limitations?: string[]; seed?: number };
  sources?: { id: string; sourceUrl?: string; license?: string; sourceSha256?: string; attribution?: string }[];
  environment?: Record<string, unknown> & { gitSha?: string; codeSha256?: Record<string, string> };
  baselineCommit?: string;
  candidateCommit?: string;
  candidateVersion?: string;
  samplingRule?: string;
  pairedReference?: string;
}

/** /api/experiments/{id}/diagnosis：通用版 baseline-delta-v1（全部批次）与同批复测的旧启发式版 heldout-legacy-heuristic。 */
export interface DiagnosisCase { caseId?: string; sampleId: string; split?: string | null; degradation: string; strength?: number; method?: string; negativeLift?: boolean; unchangedFromInput?: boolean; byteIdenticalToInput?: boolean | null; psnrDeltaFromInput?: number | null; fidelityAccepted?: boolean | null; cause?: string }
export interface Diagnosis {
  experimentId?: string; diagnosisVersion?: string; method?: string; negativeLiftCount?: number; unchangedCount?: number;
  causeCounts?: Record<string, number> | null; causeBasis?: string; cases?: DiagnosisCase[]; caveat?: string; notRetuned?: string;
  byMethod?: Record<string, { n: number; negativeLift: number; byteIdenticalToInput: number; byteIdentityUnknown: number; unmatched: number }>;
}

/* ---- agent/eval-sci 派生文件（REPORT_DATA_SPEC §0.1 DER / CI / NLC / MEC） ---- */
export interface DerRow { rowIndex: number; sampleId: string; split: string | null; degradation: string; strength?: number; method: string; appliedStatus: AppliedStatus; isPassthrough: boolean | null; criterion: string; byteIdentical: boolean | null; changedPixelCount: number | null; totalPixelCount: number | null; changedPixelRatio: number | null; maxAbsDiff: number | null; meanAbsDiff: number | null; appliedStatusDetail?: string | null; shaMatchesRecord?: boolean | null; undeterminedReason?: string | null }
export interface DerFile { experimentId: string; batch: string; derivedAt: string; derivedBy: string; sourceResultsSha256: string; imagesAvailable: boolean; criterion: string; note?: string; rows: DerRow[] }
export type GainSign = 'positive' | 'negative' | 'spans_zero' | 'zero';
export interface CiGroup {
  split: string; method: string; degradation: string; scope: 'all' | 'processed' | 'passthrough'; rowN: number; artifactN: number; seed: number; bootstrap: number; ciReliable: boolean; ciNote: string | null;
  [key: string]: unknown;
}
export interface CiFile { batch: string; experimentId: string; derivedAt: string; seed: number; bootstrap: number; percentiles: number[]; minReliableArtifacts: number; rngRule: string; gainDefinition: string; appliedStatusSha256?: string; groups: CiGroup[] }
export interface NlcEvidence { cause: string; measure: string; value: number | null; comparator: string; threshold: number; available: boolean; triggered: boolean; unavailableReason: string | null }
export interface NlcCase { rowIndex: number; sampleId: string; split: string | null; caseId?: string; degradation: string; strength?: number; method: string; psnrDelta: number; ruleInferredCause?: string; ruleInferredBasis?: string; measuredCauses: string[]; measuredEvidence: NlcEvidence[] }
export interface NlcFile { batch: string; derivedAt: string; measuredCriteriaVersion: string; note?: string; negativeLiftN: number; cases: NlcCase[] }
export interface MechanismCase { split: string; category: string; caseId: string; sampleId: string; degradation: string; strength?: number; psnrGain?: number; directory: string }
export interface MechanismIndex { batch: string; derivedAt: string; selectionRule: string; headCommit?: string; cases: MechanismCase[] }
/** 派生文件的来源：本地开发时从 agent/eval-sci 只读取出（git show），以后改为后端 API。 */
export interface Derived<T> { file: T; source: string }

export type Loadable<T> =
  | { state: 'loading' }
  | { state: 'ok'; data: T }
  | { state: 'missing'; status: number; message: string }
  | { state: 'error'; message: string };

export type Grade = '已验证（受控退化）' | '有限支持' | '未评测' | '待人工复核';
