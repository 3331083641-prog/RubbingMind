import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BookOpenText, MessageSquareText, Send, Sparkles, ShieldCheck, ExternalLink, Feather } from 'lucide-react';
import { SteleItem, CharacterItem } from '../types/stele';
import { getCuratorialInsight } from '../data/curatorialInsights';
import { SteleService } from '../services/api';
import { useExperience } from '../context/ExperienceContext';
import { SealStamp } from './SealStamp';

interface ScholarlyCompanionPanelProps {
  stele: SteleItem;
  activeChar?: CharacterItem;
  isBackendConnected: boolean;
  onHighlightChar?: (char: string) => void;
  onSendQuoteToKeepsake?: (quote: string) => void;
}

interface CompanionTurn {
  id: string;
  question: string;
  archivalEvidence: string;
  archivalSources: { title: string; url?: string; level?: string }[];
  aiInterpretation: string;
  mode: 'live_fts' | 'curated_offline';
  timestamp: string;
}

function buildInterpretativeGuidance(question: string, stele: SteleItem, activeChar?: CharacterItem): string {
  const insight = getCuratorialInsight(stele);
  const q = question.toLowerCase();
  if (q.includes('笔法') || q.includes('书体') || q.includes('楷') || q.includes('隶') || q.includes('魏')) {
    return `${insight.calligraphySchool}。${insight.brushworkSummary}`;
  }
  if (q.includes('边界') || q.includes('推演') || q.includes('门控') || q.includes('算法') || q.includes('脑补')) {
    return '本系统恪守数字人文边界：频空域自适应引擎会先检验频谱周期峰与残差特征，若图像无有效退化则通过保真门控直通原图；史料问答优先调用本地 SQLite FTS5/BM25 检索真实馆藏记录，不以大模型臆造未考证的缺字或人物。';
  }
  if (activeChar && q.includes(activeChar.char)) {
    const note = insight.glyphNotes.find((g) => g.char === activeChar.char);
    if (note) {
      return `关于单字「${note.char}」：${note.scriptEvolution} 笔法上，${note.brushwork} 文化意涵：${note.culturalMeaning}`;
    }
  }
  return `${insight.historicalContext} 艺术赏析方面，${insight.brushworkSummary}`;
}

export const ScholarlyCompanionPanel: React.FC<ScholarlyCompanionPanelProps> = ({
  stele,
  activeChar,
  isBackendConnected,
  onHighlightChar,
  onSendQuoteToKeepsake,
}) => {
  const { prefersReducedMotion } = useExperience();
  const insight = useMemo(() => getCuratorialInsight(stele), [stele]);
  const [subTab, setSubTab] = useState<'reading' | 'companion'>('reading');
  const [activePassageId, setActivePassageId] = useState<string>(insight.passages[0]?.id || 'p1');
  const [question, setQuestion] = useState('');
  const [turns, setTurns] = useState<CompanionTurn[]>([]);
  const [streamingText, setStreamingText] = useState<string>('');
  const [busy, setBusy] = useState(false);
  const streamTimerRef = useRef<number | null>(null);

  const [selectedGlyphChar, setSelectedGlyphChar] = useState<string>(insight.glyphNotes[0]?.char || '');

  useEffect(() => {
    setActivePassageId(insight.passages[0]?.id || 'p1');
    setSelectedGlyphChar(insight.glyphNotes[0]?.char || '');
    setTurns([]);
    setStreamingText('');
    setQuestion('');
    if (streamTimerRef.current) window.clearInterval(streamTimerRef.current);
  }, [stele.id, insight]);

  useEffect(() => {
    if (activeChar && insight.glyphNotes.some((g) => g.char === activeChar.char)) {
      setSelectedGlyphChar(activeChar.char);
    }
  }, [activeChar, insight]);

  useEffect(() => {
    return () => {
      if (streamTimerRef.current) window.clearInterval(streamTimerRef.current);
    };
  }, []);

  const matchedGlyphNote = useMemo(() => {
    const exact = insight.glyphNotes.find((g) => g.char === selectedGlyphChar);
    return exact || insight.glyphNotes[0];
  }, [selectedGlyphChar, insight]);

  const askCompanion = async (rawPrompt: string) => {
    const q = rawPrompt.trim();
    if (!q || busy) return;
    setBusy(true);
    setSubTab('companion');
    setQuestion('');
    setStreamingText('');
    if (streamTimerRef.current) window.clearInterval(streamTimerRef.current);

    let archivalEvidence = '';
    let archivalSources: { title: string; url?: string; level?: string }[] = [];
    let mode: 'live_fts' | 'curated_offline' = 'curated_offline';

    if (isBackendConnected) {
      try {
        const res = (await SteleService.queryEvidence(q, stele.id, Boolean(stele.isDemo))) as {
          answer?: string;
          evidence?: { title: string; url?: string; evidenceLevel?: string }[];
          status?: string;
        };
        if (res && typeof res.answer === 'string' && res.answer.trim()) {
          archivalEvidence = res.answer.trim();
          archivalSources = (res.evidence || []).slice(0, 3).map((e) => ({
            title: e.title,
            url: e.url,
            level: e.evidenceLevel,
          }));
          mode = 'live_fts';
        }
      } catch {
        // Gracefully degrade to curated archive facts below
      }
    }

    if (!archivalEvidence) {
      archivalEvidence = `据馆藏著录档案：《${stele.title}》（${stele.dynasty} · ${stele.originalYear || stele.year}），藏所著录为「${stele.collectionInstitution || stele.museum}」${stele.collectionNumber ? `，典藏号 ${stele.collectionNumber}` : ''}。${stele.summary || ''}`;
      if (stele.sourceUrl) {
        archivalSources = [
          {
            title: `${stele.collectionInstitution || stele.museum} · 原件著录页`,
            url: stele.sourceUrl,
            level: stele.license || '馆藏著录',
          },
        ];
      }
    }

    const aiInterpretation = buildInterpretativeGuidance(q, stele, activeChar);
    const fullTurn: CompanionTurn = {
      id: `turn-${Date.now()}`,
      question: q,
      archivalEvidence,
      archivalSources,
      aiInterpretation,
      mode,
      timestamp: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    };

    if (prefersReducedMotion) {
      setTurns((prev) => [fullTurn, ...prev]);
      setBusy(false);
      return;
    }

    // Smooth museum-paced streaming preview before settling the structured card
    const previewFull = `${archivalEvidence}\n\n${aiInterpretation}`;
    let cursor = 0;
    streamTimerRef.current = window.setInterval(() => {
      cursor += Math.max(4, Math.ceil(previewFull.length / 26));
      if (cursor >= previewFull.length) {
        if (streamTimerRef.current) window.clearInterval(streamTimerRef.current);
        setStreamingText('');
        setTurns((prev) => [fullTurn, ...prev]);
        setBusy(false);
      } else {
        setStreamingText(previewFull.slice(0, cursor));
      }
    }, 28);
  };

  return (
    <section
      aria-label="人文深度释读与AI金石学伴"
      data-testid="scholarly-companion"
      className="rm-book-frame rounded-2xl p-5 space-y-4"
    >
      {/* Header & Dual Sub-Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--rm-border)] pb-3">
        <div className="flex items-center gap-2.5">
          <SealStamp text="释读" variant="zhuwen" size="xs" />
          <h3 className="font-serif font-bold text-sm text-[var(--rm-gold-light)] tracking-wide">
            人文释读 · AI 金石学伴
          </h3>
        </div>

        <div className="flex items-center gap-1 p-1 rounded-xl bg-[var(--rm-bg-subtle)] border border-[var(--rm-border)] text-xs font-serif">
          <button
            type="button"
            onClick={() => setSubTab('reading')}
            className={`px-3 py-1 rounded-lg flex items-center gap-1.5 transition-all ${
              subTab === 'reading'
                ? 'bg-[var(--rm-gold)] text-[#14110f] font-bold'
                : 'text-[var(--rm-ink-secondary)] hover:text-[var(--rm-ink-primary)]'
            }`}
          >
            <BookOpenText className="w-3.5 h-3.5" />
            <span>双栏译注微赏</span>
          </button>
          <button
            type="button"
            onClick={() => setSubTab('companion')}
            className={`px-3 py-1 rounded-lg flex items-center gap-1.5 transition-all ${
              subTab === 'companion'
                ? 'bg-[var(--rm-cinnabar)] text-[#faf6ee] font-semibold rm-keep-light-ink'
                : 'text-[var(--rm-ink-secondary)] hover:text-[var(--rm-ink-primary)]'
            }`}
          >
            <MessageSquareText className="w-3.5 h-3.5" />
            <span>AI 金石学伴</span>
          </button>
        </div>
      </div>

      {/* Sub-tab 1: Focused Single-Passage Bilingual Reader + Compact Brushwork Note */}
      {subTab === 'reading' && (
        <div className="space-y-3.5">
          {insight.passages.length > 1 && (
            <div className="flex items-center gap-1.5 text-[11px] font-serif">
              {insight.passages.map((p, idx) => (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => setActivePassageId(p.id)}
                  className={`px-2.5 py-1 rounded-lg border transition-colors ${
                    p.id === activePassageId
                      ? 'bg-[var(--rm-gold)] text-[#14110f] border-[var(--rm-gold)] font-bold'
                      : 'border-[var(--rm-border)] text-[var(--rm-ink-secondary)] hover:border-[var(--rm-gold)]'
                  }`}
                >
                  句段 {['壹', '贰', '叁', '肆'][idx] || idx + 1}
                </button>
              ))}
            </div>
          )}

          {(() => {
            const p = insight.passages.find((item) => item.id === activePassageId) || insight.passages[0];
            if (!p) return null;
            return (
              <div className="rounded-xl p-3.5 border border-[var(--rm-border-strong)] bg-[var(--rm-bg-subtle)] space-y-2.5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="space-y-1 md:border-r md:border-[var(--rm-border)] md:pr-3">
                    <span className="text-[10px] rm-mono-metric text-[var(--rm-gold)] uppercase">原碑文</span>
                    <p className="font-serif text-sm leading-relaxed text-[var(--rm-ink-primary)]">{p.classical}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] rm-mono-metric text-[var(--rm-celadon-light)] uppercase">白话译注</span>
                    <p className="font-sans text-xs leading-relaxed text-[var(--rm-ink-secondary)]">{p.vernacular}</p>
                  </div>
                </div>

                <div className="pt-2 border-t border-[var(--rm-rule-hairline)] flex flex-wrap items-center justify-between gap-2 text-[11px]">
                  <div className="flex flex-wrap items-center gap-1.5">
                    {p.highlightChars.map((ch) => (
                      <button
                        key={ch}
                        type="button"
                        onClick={() => onHighlightChar?.(ch)}
                        className="w-6 h-6 rounded border border-[var(--rm-border-strong)] bg-[var(--rm-bg-elevated)] hover:border-[var(--rm-cinnabar)] hover:text-[var(--rm-cinnabar-bright)] font-serif text-xs flex items-center justify-center transition-colors"
                        title={`定位「${ch}」字`}
                      >
                        {ch}
                      </button>
                    ))}
                  </div>
                  {onSendQuoteToKeepsake && (
                    <button
                      type="button"
                      onClick={() => onSendQuoteToKeepsake(p.classical.replace(/[。，、；：]/g, ' ').trim().slice(0, 14))}
                      className="text-[11px] font-serif text-[var(--rm-cinnabar-bright)] hover:underline inline-flex items-center gap-1"
                    >
                      <Feather className="w-3 h-3" />
                      <span>摘入留痕</span>
                    </button>
                  )}
                </div>
              </div>
            );
          })()}

          {/* Calligraphy Brushwork & Glyph Evolution Micro-Appreciation */}
          {matchedGlyphNote && (
            <div className="p-3.5 rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] space-y-2">
              <div className="flex items-start gap-3">
                <div className="w-11 h-11 shrink-0 rounded-lg bg-[var(--rm-cinnabar-soft)] border border-[var(--rm-cinnabar)]/40 flex items-center justify-center font-serif text-xl font-black text-[var(--rm-cinnabar-bright)]">
                  {matchedGlyphNote.char}
                </div>
                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-serif font-bold text-xs text-[var(--rm-gold-light)]">
                      笔法与字形微赏
                    </span>
                    {insight.glyphNotes.length > 1 && (
                      <div className="flex items-center gap-1">
                        {insight.glyphNotes.map((g) => (
                          <button
                            key={g.char}
                            type="button"
                            onClick={() => {
                              setSelectedGlyphChar(g.char);
                              onHighlightChar?.(g.char);
                            }}
                            className={`w-6 h-6 rounded text-xs font-serif border transition-colors ${
                              matchedGlyphNote.char === g.char
                                ? 'bg-[var(--rm-cinnabar)] text-[#faf6ee] border-[var(--rm-cinnabar)] rm-keep-light-ink font-bold'
                                : 'border-[var(--rm-border)] bg-[var(--rm-bg-elevated)] text-[var(--rm-ink-secondary)] hover:border-[var(--rm-gold)]'
                            }`}
                          >
                            {g.char}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-[var(--rm-ink-secondary)] leading-relaxed font-sans">
                    {matchedGlyphNote.brushwork}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sub-tab 2: AI 金石学伴 */}
      {subTab === 'companion' && (
        <div className="space-y-3">
          <div className="px-3 py-1.5 rounded-lg bg-[var(--rm-celadon-soft)] border border-[var(--rm-celadon)]/35 flex items-center gap-2 text-[11px] text-[var(--rm-ink-secondary)]">
            <ShieldCheck className="w-3.5 h-3.5 text-[var(--rm-celadon-light)] shrink-0" />
            <span>史料考据与 AI 导览分层展示，不混淆史实与推演。</span>
          </div>

          {/* Preset Deep Cultural Question Chips */}
          <div className="flex flex-wrap gap-1.5">
            {insight.suggestedQuestions.map((q) => (
              <button
                key={q}
                type="button"
                disabled={busy}
                onClick={() => askCompanion(q)}
                className="px-2.5 py-1.5 rounded-lg text-[11px] font-serif text-left border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] hover:border-[var(--rm-gold)] hover:text-[var(--rm-gold-light)] transition-colors disabled:opacity-45"
              >
                <Sparkles className="w-3 h-3 inline mr-1 text-[var(--rm-gold)]" />
                {q}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              askCompanion(question);
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              aria-label="向AI金石学伴提问"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={`就《${stele.title}》提问：如书家笔法、历史典故、残字考据…`}
              className="flex-1 px-3 py-2 rounded-xl bg-[var(--rm-bg-elevated)] border border-[var(--rm-border)] focus:border-[var(--rm-gold)] outline-none text-xs text-[var(--rm-ink-primary)]"
            />
            <button
              type="submit"
              disabled={busy || question.trim().length < 2}
              className="px-3.5 py-2 rounded-xl bg-[var(--rm-cinnabar)] text-[#faf6ee] text-xs font-serif font-semibold hover:brightness-110 disabled:opacity-40 inline-flex items-center gap-1.5 rm-keep-light-ink"
            >
              <Send className="w-3.5 h-3.5" />
              <span>{busy ? '考据中…' : '研析'}</span>
            </button>
          </form>

          {/* Streaming Draft */}
          {streamingText && (
            <div className="p-3.5 rounded-xl border border-[var(--rm-gold)]/45 bg-[var(--rm-gold-soft)] text-xs text-[var(--rm-ink-primary)] leading-relaxed whitespace-pre-wrap font-sans">
              {streamingText}
              <span className="inline-block w-1.5 h-3.5 bg-[var(--rm-cinnabar)] ml-1 align-middle animate-pulse" />
            </div>
          )}

          {/* Structured Conversation History */}
          {turns.length > 0 ? (
            <div className="space-y-3 max-h-[340px] overflow-y-auto pr-1">
              {turns.map((turn) => (
                <article
                  key={turn.id}
                  className="rounded-xl border border-[var(--rm-border)] bg-[var(--rm-bg-subtle)] p-3.5 space-y-2.5 text-xs"
                >
                  <div className="flex items-center justify-between gap-2 border-b border-[var(--rm-rule-hairline)] pb-2">
                    <p className="font-serif font-bold text-[var(--rm-ink-primary)]">问：{turn.question}</p>
                    <span className="text-[10px] rm-mono-metric text-[var(--rm-ink-muted)] shrink-0">
                      {turn.mode === 'live_fts' ? '实证检索' : '典藏演示态'} · {turn.timestamp}
                    </span>
                  </div>

                  {/* Block A: Grounded Archival Evidence */}
                  <div className="p-2.5 rounded-lg bg-[var(--rm-celadon-soft)] border border-[var(--rm-celadon)]/30 space-y-1.5">
                    <span className="text-[10px] font-serif font-bold text-[var(--rm-celadon-light)] tracking-wider block">
                      【馆藏史料考据 · 可追溯来源】
                    </span>
                    <p className="text-[var(--rm-ink-primary)] leading-relaxed whitespace-pre-wrap font-sans">
                      {turn.archivalEvidence}
                    </p>
                    {turn.archivalSources.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-1">
                        {turn.archivalSources.map((src, i) =>
                          src.url ? (
                            <a
                              key={i}
                              href={src.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-[10px] text-[var(--rm-gold)] hover:underline"
                            >
                              <span>{src.title}</span>
                              <ExternalLink className="w-2.5 h-2.5" />
                            </a>
                          ) : (
                            <span key={i} className="text-[10px] text-[var(--rm-ink-muted)]">
                              {src.title}
                            </span>
                          ),
                        )}
                      </div>
                    )}
                  </div>

                  {/* Block B: AI Cultural Interpretation */}
                  <div className="p-2.5 rounded-lg bg-[var(--rm-gold-soft)] border border-[var(--rm-border)] space-y-1">
                    <span className="text-[10px] font-serif font-bold text-[var(--rm-gold)] tracking-wider block">
                      【AI 金石导览推演 · 仅供美育参考，非新增定论】
                    </span>
                    <p className="text-[var(--rm-ink-secondary)] leading-relaxed font-sans">
                      {turn.aiInterpretation}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          ) : (
            !streamingText && (
              <p className="text-xs text-[var(--rm-ink-muted)] font-serif text-center py-4">
                点击上方任一文化问题芯片，或输入您的考据疑问，开启有据可查的金石对话。
              </p>
            )
          )}
        </div>
      )}
    </section>
  );
};
