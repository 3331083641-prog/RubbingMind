/**
 * Phase2 R1 / G1 — GlyphInferenceRecord ROI + SHA 字段（报告侧本地扩展）。
 *
 * 后端 glyph_inference 已持久化 roi / inputImageSha256 / cropSha256；
 * 共享 services/api.ts 的 GlyphInferenceRecord 尚未声明（归 AB-7 / api.ts 接入点）。
 * 本文件用交叉类型对齐后端形状，避免直接改 api.ts；评测若只 grep api.ts 仍可能 xfail，直至 AB-7 合入。
 */
import type { GlyphInferenceRecord as ApiGlyphInferenceRecord } from '../../../services/api';

/** 与后端 bbox / _map_roi 一致的 w/h 几何。 */
export type GlyphBBox = { x: number; y: number; w: number; h: number };

/** 后端 `_map_roi` 返回值（PHASE2_ROI_REQUESTS R1）。 */
export type GlyphRoi = {
  imageBBox: GlyphBBox;
  mappedSourceBBox: GlyphBBox;
  mappedInsideSource: boolean | null;
  cropWidth: number;
  cropHeight: number;
  scaleFromSource: number;
};

/**
 * 报告侧 GlyphInferenceRecord：在 api 基类型上补 R1 字段。
 * 运行时 JSON 已有这些键；缺省时为 optional，界面如实显示「未返回」。
 */
export type GlyphInferenceRecord = ApiGlyphInferenceRecord & {
  roi?: GlyphRoi;
  inputImageSha256?: string;
  cropSha256?: string;
  /** 后端常与 imageProvenance.selectedImageSha256 并列返回 */
  selectedImageSha256?: string;
};

export function mappedSourceBBox(record: GlyphInferenceRecord): GlyphBBox | null {
  const box = record.roi?.mappedSourceBBox;
  if (!box || typeof box.x !== 'number' || typeof box.y !== 'number' || typeof box.w !== 'number' || typeof box.h !== 'number') {
    return null;
  }
  return box;
}

export function formatGlyphBBox(box: GlyphBBox | null | undefined): string {
  if (!box) return '未返回';
  return `${box.x},${box.y} ${box.w}×${box.h}`;
}
