import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

export type AestheticTheme = 'obsidian' | 'xuan';

interface ExperienceContextValue {
  theme: AestheticTheme;
  setTheme: (theme: AestheticTheme) => void;
  toggleTheme: () => void;
  showcaseMode: boolean;
  setShowcaseMode: (enabled: boolean) => void;
  toggleShowcaseMode: () => void;
  manifestoOpen: boolean;
  setManifestoOpen: (open: boolean) => void;
  prefersReducedMotion: boolean;
}

const ExperienceContext = createContext<ExperienceContextValue | null>(null);

const THEME_STORAGE_KEY = 'rubbingmind.aestheticTheme';

function detectReducedMotion(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export const ExperienceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<AestheticTheme>(() => {
    if (typeof window === 'undefined') return 'obsidian';
    try {
      const saved = window.localStorage.getItem(THEME_STORAGE_KEY);
      if (saved === 'xuan' || saved === 'obsidian') return saved;
    } catch {
      // Ignore storage access restrictions
    }
    return 'obsidian';
  });

  const [showcaseMode, setShowcaseModeState] = useState<boolean>(false);
  const [manifestoOpen, setManifestoOpen] = useState<boolean>(false);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(detectReducedMotion);

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setPrefersReducedMotion(mq.matches);
    onChange();
    mq.addEventListener?.('change', onChange);
    return () => mq.removeEventListener?.('change', onChange);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = theme;
    root.dataset.showcase = showcaseMode ? '1' : '0';
    document.body.dataset.theme = theme;
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Ignore storage restrictions
    }
  }, [theme, showcaseMode]);

  useEffect(() => {
    if (!showcaseMode) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowcaseModeState(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [showcaseMode]);

  const setTheme = useCallback((next: AestheticTheme) => setThemeState(next), []);
  const toggleTheme = useCallback(
    () => setThemeState((prev) => (prev === 'obsidian' ? 'xuan' : 'obsidian')),
    [],
  );
  const setShowcaseMode = useCallback((enabled: boolean) => setShowcaseModeState(enabled), []);
  const toggleShowcaseMode = useCallback(() => setShowcaseModeState((prev) => !prev), []);

  return (
    <ExperienceContext.Provider
      value={{
        theme,
        setTheme,
        toggleTheme,
        showcaseMode,
        setShowcaseMode,
        toggleShowcaseMode,
        manifestoOpen,
        setManifestoOpen,
        prefersReducedMotion,
      }}
    >
      {children}
    </ExperienceContext.Provider>
  );
};

export function useExperience(): ExperienceContextValue {
  const ctx = useContext(ExperienceContext);
  if (!ctx) {
    throw new Error('useExperience must be used inside ExperienceProvider');
  }
  return ctx;
}
