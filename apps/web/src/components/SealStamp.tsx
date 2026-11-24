import React from 'react';

interface SealStampProps {
  text: string;
  variant?: 'zhuwen' | 'baiwen';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
  title?: string;
}

/**
 * 传统篆刻朱文 / 白文印章微件
 * - zhuwen (朱文阳刻): 宿宣底色 + 朱砂边框与文字
 * - baiwen (白文阴刻): 朱砂满印 + 宿宣阴文
 */
export const SealStamp: React.FC<SealStampProps> = ({
  text,
  variant = 'baiwen',
  size = 'sm',
  className = '',
  title,
}) => {
  const sizeClasses = {
    xs: 'w-6 h-6 text-[10px] leading-[1.05] p-0.5 rounded-[3px]',
    sm: 'w-8 h-8 text-[11px] leading-[1.05] p-1 rounded-[4px]',
    md: 'w-11 h-11 text-[13px] leading-[1.08] p-1 rounded-[4px]',
    lg: 'w-14 h-14 text-[16px] leading-[1.1] p-1.5 rounded-[5px]',
  }[size];

  const isFourChar = text.length === 4;
  const gridText = isFourChar ? (
    <span className="grid grid-cols-2 grid-rows-2 w-full h-full place-items-center font-serif font-bold">
      <span>{text[2]}</span>
      <span>{text[0]}</span>
      <span>{text[3]}</span>
      <span>{text[1]}</span>
    </span>
  ) : (
    <span className="font-serif font-black tracking-tight flex items-center justify-center w-full h-full">
      {text}
    </span>
  );

  const styleClasses =
    variant === 'baiwen'
      ? 'bg-[var(--rm-cinnabar)] text-[#faf6ee] border border-[#e36b57]/55 shadow-[0_3px_12px_rgba(195,57,39,0.34)] rm-keep-light-ink'
      : 'bg-transparent text-[var(--rm-cinnabar)] border-[1.5px] border-[var(--rm-cinnabar)] shadow-[inset_0_0_0_1px_rgba(195,57,39,0.22)]';

  return (
    <span
      title={title || text}
      aria-label={title || text}
      className={`inline-flex shrink-0 items-center justify-center select-none ${sizeClasses} ${styleClasses} ${className}`}
    >
      {gridText}
    </span>
  );
};
