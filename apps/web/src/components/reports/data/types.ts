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
  maxAbsDiff?: number | null;
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

export interface DiagnosisCase { sampleId: string; degradation: string; negativeLift?: boolean; unchangedFromInput?: boolean; psnrDeltaFromInput?: number | null; fidelityAccepted?: boolean | null; cause?: string }
export interface Diagnosis { experimentId?: string; method?: string; negativeLiftCount?: number; unchangedCount?: number; causeCounts?: Record<string, number>; cases?: DiagnosisCase[]; caveat?: string; notRetuned?: string }

export type Loadable<T> =
  | { state: 'loading' }
  | { state: 'ok'; data: T }
  | { state: 'missing'; status: number; message: string }
  | { state: 'error'; message: string };

export type Grade = '已验证（受控退化）' | '有限支持' | '未评测' | '待人工复核';
