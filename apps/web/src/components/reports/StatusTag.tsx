/** 每行一个 7 值状态标签（REPORT_DATA_SPEC §1(b)）。来源为 DER 时不加注；前端兜底时加“兜底”角标。 */
import React from 'react';
import type { AppliedStatus } from './data/types';
import { APPLIED_LABELS } from './data/labels';

const STYLE: Record<AppliedStatus, string> = {
  baseline: 'border-slate-500 text-slate-300',
  processed: 'border-celadon/60 text-celadon-light',
  passthrough: 'border-gold/60 text-gold-light',
  passthrough_not_applicable: 'border-gold/40 text-gold-light/80',
  processed_not_applicable_label: 'border-cinnabar/60 text-cinnabar-light',
  failed: 'border-cinnabar text-cinnabar-light',
  undetermined: 'border-slate-600 text-slate-400',
};
export const StatusTag: React.FC<{ status: AppliedStatus; source?: 'DER' | 'frontend' }> = ({ status, source }) => (
  <span data-testid="status-tag" data-status={status} className={`inline-block whitespace-nowrap rounded border px-1 py-0 text-[10px] ${STYLE[status]}`} title={source === 'DER' ? '来源：derived/applied_status（pixel-equal-v1）' : '来源：前端兜底（SHA-256 比较）'}>
    {APPLIED_LABELS[status]}{source === 'frontend' && status !== 'baseline' ? ' · 兜底' : ''}
  </span>
);
