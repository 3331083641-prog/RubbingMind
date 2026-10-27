/**
 * Phase2 R1 / G1 — 报告侧 ROI 辅助。
 * GlyphInferenceRecord 正式字段已由 AB-7 写入 services/api.ts（roi / inputImageSha256 / cropSha256）；
 * 本文件不再交叉扩展，只 re-export 并提供 mappedSourceBBox / formatGlyphBBox。
 */
import type { GlyphInferenceRecord } from '../../../services/api';

export type { GlyphInferenceRecord } from '../../../services/api';

/** 与后端 bbox / _map_roi 一致的 w/h 几何。 */
export type GlyphBBox = { x: number; y: number; w: number; h: number };

/** 与 api.ts GlyphInferenceRecord.roi 同形（便于局部引用）。 */
export type GlyphRoi = {
  imageBBox: GlyphBBox;
  mappedSourceBBox: GlyphBBox;
  mappedInsideSource: boolean | null;
  cropWidth: number;
  cropHeight: number;
  scaleFromSource: number;
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
