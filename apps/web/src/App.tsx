import React, { useState, useEffect } from 'react';
import { SteleItem } from './types/stele';
import { SteleService, FALLBACK_STELES } from './services/api';
import { Header } from './components/Header';
import { Footer } from './components/Footer';
import { UploadModal } from './components/UploadModal';
import { HomePage } from './pages/HomePage';
import { MuseumPage } from './pages/MuseumPage';
import { WorkbenchPage } from './pages/WorkbenchPage';
import { GraphPage } from './pages/GraphPage';
import { ReportsPage } from './pages/ReportsPage';
import { graphSelectionItems, resolveCoreId } from './data/graphSelection';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('home');
  const [steles, setSteles] = useState<SteleItem[]>(FALLBACK_STELES);
  const [selectedSteleId, setSelectedSteleId] = useState<string>('tang-duobao');
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  // Fetch steles from FastAPI backend on mount
  useEffect(() => {
    let isMounted = true;
    SteleService.getSteles()
      .then((data) => {
        if (isMounted && data && data.length > 0) {
          setSteles(data);
          setIsBackendConnected(true);
        }
      })
      .catch(() => {
        if (isMounted) setIsBackendConnected(false);
      });
    return () => { isMounted = false; };
  }, []);

  const coreItems = graphSelectionItems(steles);
  const currentStele = steles.find((s) => s.id === selectedSteleId)
    || coreItems.find(s => resolveCoreId(s.id) === resolveCoreId(selectedSteleId)) || steles[0];
  const graphHeaderItems = [...coreItems, ...steles.filter(s => !coreItems.some(c => c.id === s.id))];

  const handleSelectStele = (id: string) => {
    setSelectedSteleId(id);
  };

  const handleUploaded = (newStele: SteleItem) => {
    setSteles((prev) => [newStele, ...prev]);
    setSelectedSteleId(newStele.id);
    setCurrentTab('workbench');
  };

  return (
    <div className="min-h-screen bg-[#0A0D12] text-slate-100 flex flex-col font-sans selection:bg-gold/30 selection:text-gold-light">
      {/* 68px Sticky App Shell Header */}
      <Header
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        steles={currentTab === 'graph' ? graphHeaderItems : steles}
        selectedSteleId={currentStele.id}
        onSelectStele={handleSelectStele}
        onOpenUpload={() => setIsUploadOpen(true)}
        isBackendConnected={isBackendConnected}
      />

      {/* Main Dynamic View with 300ms Fade Transition */}
      <main className="flex-1 transition-opacity duration-300">
        {currentTab === 'home' && (
          <HomePage
            steles={steles}
            onSelectStele={handleSelectStele}
            onNavigate={setCurrentTab}
          />
        )}

        {currentTab === 'museum' && (
          <MuseumPage
            steles={steles}
            onSelectStele={handleSelectStele}
            onNavigate={setCurrentTab}
            onOpenUpload={() => setIsUploadOpen(true)}
          />
        )}

        {currentTab === 'workbench' && (
          <WorkbenchPage
            stele={currentStele}
            onNavigate={setCurrentTab}
          />
        )}

        {currentTab === 'graph' && (
          <GraphPage
            stele={currentStele}
            onNavigate={setCurrentTab}
            onSelectStele={handleSelectStele}
          />
        )}

        {currentTab === 'reports' && (
          <ReportsPage
            stele={currentStele}
            onNavigate={setCurrentTab}
          />
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
