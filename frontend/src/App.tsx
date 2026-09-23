import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { FileUploadModal } from './components/FileUploadModal';
import { SourceDrawer } from './components/SourceDrawer';
import { DashboardPage } from './pages/DashboardPage';
import { KnowledgeBasesPage } from './pages/KnowledgeBasesPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ChatPage } from './pages/ChatPage';
import { KnowledgeBase } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'kb' | 'documents' | 'chat'>('dashboard');
  const [selectedKb, setSelectedKb] = useState<KnowledgeBase | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);

  // Source drawer state
  const [drawerDocId, setDrawerDocId] = useState<string | null>(null);
  const [drawerPage, setDrawerPage] = useState<number | null>(null);

  const handleOpenSource = (docId: string, page: number) => {
    setDrawerDocId(docId);
    setDrawerPage(page);
  };

  const handleCloseDrawer = () => {
    setDrawerDocId(null);
    setDrawerPage(null);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedKb={selectedKb}
        setSelectedKb={setSelectedKb}
        onOpenUpload={() => setIsUploadOpen(true)}
      />

      <main className="flex-1 overflow-x-hidden relative">
        <div className={activeTab === 'dashboard' ? 'block' : 'hidden'}>
          <DashboardPage
            onOpenUpload={() => setIsUploadOpen(true)}
            onNavigate={setActiveTab}
            selectedKb={selectedKb}
            onViewDoc={handleOpenSource}
          />
        </div>
        <div className={activeTab === 'kb' ? 'block' : 'hidden'}>
          <KnowledgeBasesPage
            selectedKb={selectedKb}
            setSelectedKb={setSelectedKb}
            onNavigate={setActiveTab}
            onOpenUpload={() => setIsUploadOpen(true)}
          />
        </div>
        <div className={activeTab === 'documents' ? 'block' : 'hidden'}>
          <DocumentsPage
            selectedKb={selectedKb}
            onOpenUpload={() => setIsUploadOpen(true)}
            onInspectDoc={handleOpenSource}
          />
        </div>
        <div className={activeTab === 'chat' ? 'block h-full' : 'hidden'}>
          <ChatPage selectedKb={selectedKb} onOpenSource={handleOpenSource} />
        </div>
      </main>

      {/* Global Modals */}
      <FileUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        selectedKb={selectedKb}
        onUploaded={() => {}}
      />

      <SourceDrawer
        documentId={drawerDocId}
        targetPage={drawerPage}
        onClose={handleCloseDrawer}
      />
    </div>
  );
};

export default App;
