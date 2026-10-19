import React from 'react';
import type { Grade } from './data/types';
const STYLE: Record<Grade, string> = {
  '已验证（受控退化）': 'bg-celadon/20 text-celadon-bright border-celadon/50',
  '有限支持': 'bg-gold/10 text-gold-light border-gold/40',
  '未评测': 'bg-slate-800 text-slate-300 border-slate-600',
  '待人工复核': 'bg-cinnabar/15 text-cinnabar-light border-cinnabar/50',
};
export const GradeBadge: React.FC<{ grade: Grade; reasons?: string[] }> = ({ grade, reasons }) => (
  <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[11px] whitespace-nowrap ${STYLE[grade]}`} title={reasons?.join('；')} data-grade={grade}>
    {grade}
  </span>
);
