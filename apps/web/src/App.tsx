import React, { lazy, Suspense, useState, useEffect, useRef, useCallback } from 'react';
import { SteleItem } from './types/stele';
import { SteleService, FALLBACK_STELES, backendAvailable } from './services/api';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { UploadModal } from './components/UploadModal';
import { HomePage } from './pages/HomePage';
const MuseumPage = lazy(() => import('./pages/MuseumPage').then(module => ({default:module.MuseumPage})));
const WorkbenchPage = lazy(() => import('./pages/WorkbenchPage').then(module => ({default:module.WorkbenchPage})));
const GraphPage = lazy(() => import('./pages/GraphPage').then(module => ({default:module.GraphPage})));
const ReportsPage = lazy(() => import('./pages/ReportsPage').then(module => ({default:module.ReportsPage})));
import { graphSelectionItems, resolveCoreId } from './data/graphSelection';
import { CORE_SAMPLES, resolveSelected } from './data/catalogSelection';
import { VerifiedMuseumGraph } from './components/VerifiedMuseumGraph';
import { parseUrlState, resolveExperiment, writeUrlState, UrlState } from './state/urlState';

export const App: React.FC = () => {
  // R1-6 / R2-8: initial state may come from the URL; without parameters the defaults are unchanged
  // and the URL is not rewritten until the user changes something.
  const [initialParse] = useState(() => parseUrlState());
  const initialUrl = initialParse.state;
  const userChanged = useRef(false);
  const [urlNotices, setUrlNotices] = useState<string[]>(() => initialParse.issues.map(issue => issue.message));
  const addNotice = useCallback((message: string) => setUrlNotices(items => items.includes(message) ? items : [...items, message]), []);
  const [currentTab, setCurrentTabState] = useState<string>(initialUrl.tab || 'home');
  const [steles, setSteles] = useState<SteleItem[]>(FALLBACK_STELES);
  const [selectedSteleId, setSelectedSteleId] = useState<string>(initialUrl.steleId || 'tang-duobao');
  // Shared run / experiment selection: the workbench writes it, the report page reads it.
  const [activeRunId, setActiveRunIdState] = useState<string | null>(initialUrl.runId || null);
  // experimentId is authoritative; a `batch` alias is resolved below and never kept in state or URL.
  const [activeExperimentId, setActiveExperimentId] = useState<string | null>(initialUrl.experimentId || null);
  const [experimentStatus, setExperimentStatus] = useState<'none' | 'resolving' | 'ok' | 'unknown' | 'unavailable'>(
    initialUrl.experimentId || initialUrl.batch ? 'resolving' : 'none');
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);
  const [catalogueStatus, setCatalogueStatus] = useState<'loading' | 'ready' | 'fallback'>('loading');

  // Fetch steles from FastAPI backend on mount. The status stays "loading" until that request settles.
  useEffect(() => {
    let isMounted = true;
    SteleService.getSteles()
      .then((data) => {
        if (!isMounted) return;
        if (backendAvailable && data && data.length > 0) {
          setSteles(data);
          setIsBackendConnected(true);
          setCatalogueStatus('ready');
        } else {
          setIsBackendConnected(false);
          setCatalogueStatus('fallback');
        }
      })
      .catch(() => {
        if (!isMounted) return;
        setIsBackendConnected(false);
        setCatalogueStatus('fallback');
      });
    return () => { isMounted = false; };
  }, []);

  // User-driven setters: only these make the URL writable.
  const setCurrentTab = useCallback((tab: string) => { userChanged.current = true; setCurrentTabState(tab); }, []);
  const setActiveRunId = useCallback((runId: string | null) => { userChanged.current = true; setActiveRunIdState(runId); }, []);

  // Normalise a URL that came with parameters (drop invalid values and the batch alias) without
  // adding any default value. Skipped once the user has changed state (the effect below writes then).
  const normaliseInitialUrl = useCallback((patch: Partial<UrlState>) => {
    if (userChanged.current) return;
    const provided: UrlState = { ...initialUrl, ...patch };
    delete provided.batch;
    writeUrlState(provided);
  }, [initialUrl]);

  useEffect(() => {
    if (initialParse.issues.length) normaliseInitialUrl({});
    if (!initialUrl.experimentId && !initialUrl.batch) return;
    let live = true;
    SteleService.listExperiments().then(list => {
      if (!live) return;
      const resolution = resolveExperiment(list, { experimentId: initialUrl.experimentId, batch: initialUrl.batch });
      if (resolution.status === 'ok') {
        setActiveExperimentId(resolution.experimentId);
        setExperimentStatus('ok');
        if (resolution.notice) addNotice(resolution.notice);
        normaliseInitialUrl({ experimentId: resolution.experimentId });
      } else if (resolution.status === 'unknown') {
        // Real empty state: keep the requested experimentId, never substitute another batch.
        setActiveExperimentId(resolution.experimentId);
        setExperimentStatus('unknown');
        addNotice(resolution.notice);
        normaliseInitialUrl({ experimentId: resolution.experimentId ?? undefined });
      }
    }).catch(() => { if (live) { setExperimentStatus('unavailable'); addNotice('实验登记暂不可用，链接中的实验批次尚未核对'); } });
    return () => { live = false; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // A deep-linked runId must exist for the linked artifact; otherwise clear it with a notice.
  useEffect(() => {
    const runId = initialUrl.runId;
    if (!runId) return;
    let live = true;
    SteleService.listRuns(initialUrl.steleId || selectedSteleId).then(items => {
      if (!live || userChanged.current || items.some(item => item.runId === runId)) return;
      setActiveRunIdState(null);
      addNotice(`链接中的运行 ${runId} 不属于当前文物或已不存在，已从地址中移除，未替换为其他运行`);
      normaliseInitialUrl({ runId: undefined });
    }).catch(() => undefined);
    return () => { live = false; };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const coreItems = graphSelectionItems(steles);
  // An unknown steleId (e.g. from a link) is an explicit empty state, never another artifact.
  const currentStele: SteleItem | null = (() => { try { return resolveSelected(steles, selectedSteleId); } catch { return null; } })();
  const graphHeaderItems = [...coreItems, ...steles.filter(s => !coreItems.some(c => c.id === s.id))];

  const handleSelectStele = (id: string) => {
    userChanged.current = true;
    // A runId belongs to one artifact; never carry it over to another one.
    if (id !== selectedSteleId) setActiveRunIdState(null);
    setSelectedSteleId(id);
  };

  useEffect(() => {
    if (!userChanged.current) return; // never rewrite a URL the user has not changed
    writeUrlState({
      tab: currentTab === 'home' ? undefined : currentTab,
      steleId: selectedSteleId,
      runId: activeRunId || undefined,
      experimentId: activeExperimentId || undefined,
    });
  }, [currentTab, selectedSteleId, activeRunId, activeExperimentId]);

  const handleUploaded = (newStele: SteleItem) => {
    setSteles((prev) => [newStele, ...prev]);
    setActiveRunId(null);
    setSelectedSteleId(newStele.id);
    setCurrentTab('workbench');
  };

  return (
    <div className="min-h-screen bg-[#0A0D12] text-slate-100 flex flex-col font-sans selection:bg-gold/30 selection:text-gold-light" data-catalogue-status={catalogueStatus} data-tab={currentTab} data-verified-count={steles.filter(item => item.source_kind === 'verified_review_v3').length}>
      {/* 68px Sticky App Shell Header */}
      <Header
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        steles={currentTab === 'graph' ? [...CORE_SAMPLES, ...graphHeaderItems.filter(s => !CORE_SAMPLES.some(c => c.id === s.id))] : [...CORE_SAMPLES, ...steles]}
        selectedSteleId={selectedSteleId}
        onSelectStele={handleSelectStele}
      />

      {urlNotices.length > 0 && (
        <div role="status" data-url-notices={urlNotices.length} className="mx-4 mt-2 rounded border border-gold/40 bg-slate-900/80 p-2 text-sm text-gold-light">
          {urlNotices.map(message => <p key={message}>{message}</p>)}
          <button type="button" className="mt-1 text-xs underline" onClick={() => setUrlNotices([])}>知道了</button>
        </div>
      )}

      {/* Main Dynamic View with 300ms Fade Transition */}
      <main className="flex-1 transition-opacity duration-300">
        {!currentStele && (
          <div role="status" data-stele-missing={selectedSteleId} className="p-8 text-gold">
            {catalogueStatus === 'loading' ? '正在读取文物目录…' : `没有找到文物 ${selectedSteleId}；未替换为其他文物。请从顶部选择文物。`}
          </div>
        )}
        {currentStele && (
        <Suspense fallback={<div role="status" className="p-8 text-gold">正在载入当前页面…</div>}>
        {currentTab === 'home' && (
          <HomePage
            steles={steles}
            onSelectStele={handleSelectStele}
            onNavigate={setCurrentTab}
          />
        )}

        {currentTab === 'museum' && (
          <MuseumPage
            steles={steles.filter(s => s.source_kind === 'verified_review_v3')}
            onSelectStele={handleSelectStele}
            onNavigate={setCurrentTab}
            onOpenUpload={() => setIsUploadOpen(true)}
          />
        )}

        {currentTab === 'workbench' && (
          <WorkbenchPage
            key={currentStele.id}
            stele={currentStele}
            onNavigate={setCurrentTab}
            onRunChange={setActiveRunId}
          />
        )}

        {currentTab === 'graph' && currentStele.source_kind === 'verified_review_v3' && <VerifiedMuseumGraph stele={currentStele} onNavigate={setCurrentTab} />}
        {currentTab === 'graph' && currentStele.source_kind !== 'verified_review_v3' && (
          <GraphPage
            stele={currentStele}
            onSelectStele={handleSelectStele}
            onNavigate={setCurrentTab}
          />
        )}

        {currentTab === 'reports' && (
          <ReportsPage
            key={currentStele.id}
            stele={currentStele}
            onNavigate={setCurrentTab}
            runId={activeRunId}
            onRunChange={setActiveRunId}
            experimentId={activeExperimentId}
            experimentStatus={experimentStatus}
            onExperimentChange={(experimentId) => { userChanged.current = true; setActiveExperimentId(experimentId); setExperimentStatus(experimentId ? 'ok' : 'none'); }}
          />
        )}
        </Suspense>
        )}
      </main>

      {/* Footer */}
      <Footer />

      {/* Upload Modal Drawer */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploaded={handleUploaded}
      />
    </div>
  );
};

export default App;
