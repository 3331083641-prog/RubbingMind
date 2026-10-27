import React, { useEffect, useRef, useState } from 'react';

export function useQuietMotion() {
  const [quiet, setQuiet] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches || ((navigator as Navigator & { hardwareConcurrency?: number }).hardwareConcurrency || 8) <= 2);
  useEffect(() => { const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setQuiet(query.matches || (navigator.hardwareConcurrency || 8) <= 2);
    query.addEventListener('change', update); return () => query.removeEventListener('change', update);
  }, []);
  return quiet;
}

export function AnimatedValue({ value, digits = 0, signed = false }: { value: number | null | undefined; digits?: number; signed?: boolean }) {
  const ref = useRef<HTMLSpanElement>(null); const previous = useRef<number | null>(null); const quiet = useQuietMotion();
  const format = (n: number) => `${signed && n > 0 ? '+' : ''}${n.toFixed(digits)}`;
  useEffect(() => {
    const el = ref.current; if (!el || value == null || !Number.isFinite(value)) return;
    const start = previous.current ?? 0; previous.current = value;
    if (quiet) { el.textContent = format(value); return; }
    let frame = 0; const time = performance.now();
    const step = (now: number) => { const t = Math.min(1, (now - time) / 520); el.textContent = format(start + (value - start) * (1 - (1 - t) ** 3)); if (t < 1) frame = requestAnimationFrame(step); };
    frame = requestAnimationFrame(step); return () => cancelAnimationFrame(frame);
  }, [value, digits, signed, quiet]);
  if (value == null || !Number.isFinite(value)) return <span className="studio-null">未评测</span>;
  return <span aria-label={format(value)} data-final-value={value}><span ref={ref} aria-hidden="true">{format(value)}</span></span>;
}
