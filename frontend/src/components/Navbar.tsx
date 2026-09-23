import React, { useEffect, useState } from 'react';
import { Database, Layers, MessageSquare, FileText, CheckCircle2, AlertCircle, Plus } from 'lucide-react';
import { apiClient } from '../api/client';
import { KnowledgeBase } from '../types';

interface NavbarProps {
  activeTab: 'dashboard' | 'kb' | 'documents' | 'chat';
  setActiveTab: (tab: 'dashboard' | 'kb' | 'documents' | 'chat') => void;
  selectedKb: KnowledgeBase | null;
  setSelectedKb: (kb: KnowledgeBase | null) => void;
  onOpenUpload: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  selectedKb,
  setSelectedKb,
  onOpenUpload,
}) => {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [isHealthy, setIsHealthy] = useState<boolean>(true);

  useEffect(() => {
    loadKbs();
    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  const loadKbs = async () => {
    try {
      const data = await apiClient.getKnowledgeBases();
      setKbs(data);
      if (data.length > 0 && !selectedKb) {
        setSelectedKb(data[0]);
      }
    } catch (e) {
      console.error('Failed to load KBs', e);
    }
  };

  const checkHealth = async () => {
    try {
      const health = await apiClient.getStats();
      setIsHealthy(true);
    } catch (e) {
      setIsHealthy(false);
    }
  };

  return (
    <header className="h-16 border-b border-slate-800 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      {/* Brand */}
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('dashboard')}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-base tracking-tight bg-gradient-to-r from-white via-slate-200 to-sky-300 bg-clip-text text-transparent">
              OmniRAG
            </span>
            <span className="text-[10px] ml-2 px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 font-mono border border-sky-500/20">
              MULTIMODAL
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1">
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'dashboard'
                ? 'bg-slate-800 text-sky-400 border border-slate-700'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('kb')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'kb'
                ? 'bg-slate-800 text-sky-400 border border-slate-700'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            Knowledge Bases
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'documents'
                ? 'bg-slate-800 text-sky-400 border border-slate-700'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            Documents
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center space-x-1.5 ${
              activeTab === 'chat'
                ? 'bg-slate-800 text-sky-400 border border-slate-700'
                : 'text-slate-400 hover:text-white hover:bg-slate-900'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>Chat</span>
          </button>
        </nav>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-4">
        {/* Active KB selector */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 hidden sm:inline">Active KB:</span>
          <select
            value={selectedKb?.id || ''}
            onChange={(e) => {
              const found = kbs.find((k) => k.id === e.target.value);
              setSelectedKb(found || null);
            }}
            className="bg-slate-900 border border-slate-700 text-slate-200 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-sky-500"
          >
            {kbs.map((k) => (
              <option key={k.id} value={k.id}>
                {k.name} ({k.document_count} docs)
              </option>
            ))}
            {kbs.length === 0 && <option value="">No Knowledge Bases</option>}
          </select>
        </div>

        {/* Upload Button */}
        <button
          onClick={onOpenUpload}
          className="bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg flex items-center space-x-1.5 shadow-md shadow-sky-600/20 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Upload</span>
        </button>

        {/* Status indicator */}
        <div className="flex items-center space-x-1.5 px-2 py-1 rounded-full bg-slate-900 border border-slate-800">
          <div className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
          <span className="text-[11px] text-slate-400">{isHealthy ? 'Online' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
};
