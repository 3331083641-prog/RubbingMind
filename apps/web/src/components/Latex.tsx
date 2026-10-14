import React from 'react';
import katex from 'katex';

interface LatexProps {
  math: string;
  block?: boolean;
  className?: string;
}

export const Latex: React.FC<LatexProps> = ({ math, block = false, className = '' }) => {
  try {
    const html = katex.renderToString(math, {
      displayMode: block,
      throwOnError: false,
    });

    return (
      <span
        className={`inline-block select-text ${className}`}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  } catch (e) {
    return <span className="font-mono text-xs">{math}</span>;
  }
};
