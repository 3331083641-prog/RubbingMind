import React, { lazy, Suspense, useState, useEffect } from 'react';
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
import { readUrlState, writeUrlState } from './state/urlState';

export const App: React.FC = () => {
  // R1-6: initial state may come from the URL; without parameters the defaults are unchanged.
  const [initialUrl] = useState(() => readUrlState());
  const [currentTab, setCurrentTab] = useState<string>(initialUrl.tab || 'home');
  const [steles, setSteles] = useState<SteleItem[]>(FALLBACK_STELES);
  const [selectedSteleId, setSelectedSteleId] = useState<string>(initialUrl.steleId || 'tang-duobao');
  // Shared run / experiment selection: the workbench writes it, the report page reads it.
  const [activeRunId, setActiveRunId] = useState<string | null>(initialUrl.runId || null);
  const [activeExperimentId, setActiveExperimentId] = useState<string | null>(initialUrl.experimentId || null);
  const [activeBatch, setActiveBatch] = useState<string | null>(initialUrl.batch || null);
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

  const coreItems = graphSelectionItems(steles);
  const currentStele = resolveSelected(steles, selectedSteleId);
  const graphHeaderItems = [...coreItems, ...steles.filter(s => !coreItems.some(c => c.id === s.id))];

  const handleSelectStele = (id: string) => {
    // A runId belongs to one artifact; never carry it over to another one.
    if (id !== selectedSteleId) setActiveRunId(null);
    setSelectedSteleId(id);
  };

  useEffect(() => {
    writeUrlState({
      tab: currentTab === 'home' ? undefined : currentTab,
      steleId: selectedSteleId,
      runId: activeRunId || undefined,
      experimentId: activeExperimentId || undefined,
      batch: activeBatch || undefined,
    });
  }, [currentTab, selectedSteleId, activeRunId, activeExperimentId, activeBatch]);

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

      {/* Main Dynamic View with 300ms Fade Transition */}
      <main className="flex-1 transition-opacity duration-300">
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
            batch={activeBatch}
            onExperimentChange={(experimentId, batch) => { setActiveExperimentId(experimentId); setActiveBatch(batch ?? null); }}
          />
        )}
        </Suspense>
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
