import React, { useEffect, useState } from 'react';
import {
  FileText,
  Database,
  Image as ImageIcon,
  Table as TableIcon,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  Plus,
  Search,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { DashboardStats, DocumentItem, KnowledgeBase } from '../types';

interface DashboardPageProps {
  onOpenUpload: () => void;
  onNavigate: (tab: 'dashboard' | 'kb' | 'documents' | 'chat') => void;
  selectedKb: KnowledgeBase | null;
  onViewDoc: (docId: string, page: number) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  onOpenUpload,
  onNavigate,
  selectedKb,
  onViewDoc,
}) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentDocs, setRecentDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDashboard();
  }, [selectedKb]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [statsData, docsData] = await Promise.all([
        apiClient.getStats(),
        apiClient.getDocuments(selectedKb?.id),
      ]);
      setStats(statsData);
      setRecentDocs(docsData.slice(0, 8));
    } catch (e) {
      console.error('Failed to load dashboard data', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-150">
      {/* Hero Welcome & Quick Actions */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-800/80 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Enterprise Multimodal RAG</h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Ingest PDFs, PowerPoint slides, Word documents, and figures. The platform preserves relationships between
            text, tables, and original visual artifacts for grounded retrieval and citations.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => onNavigate('chat')}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs font-semibold border border-slate-700 transition-all flex items-center space-x-2"
          >
            <span>Ask Questions</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
          <button
            onClick={onOpenUpload}
            className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-lg shadow-sky-600/25 transition-all flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* Stats Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Documents</span>
            <FileText className="w-4 h-4 text-sky-400" />
          </div>
          <p className="text-2xl font-bold text-white">{stats?.total_documents ?? 0}</p>
          <span className="text-[11px] text-emerald-400 mt-1 block">
            {stats?.completed_documents ?? 0} indexed & ready
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Visual Assets</span>
            <ImageIcon className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-white">{stats?.total_images ?? 0}</p>
          <span className="text-[11px] text-indigo-400 mt-1 block">Diagrams, charts & figures</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Tables</span>
            <TableIcon className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-white">{stats?.total_tables ?? 0}</p>
          <span className="text-[11px] text-slate-400 mt-1 block">Extracted structured grids</span>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Text Chunks</span>
            <Database className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-white">{stats?.total_chunks ?? 0}</p>
          <span className="text-[11px] text-amber-400 mt-1 block">{stats?.total_vectors ?? 0} indexed vectors</span>
        </div>
      </div>

      {/* Recent Documents Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div>
            <h3 className="font-semibold text-slate-100 text-sm">Indexed Documents</h3>
            <p className="text-xs text-slate-400 mt-0.5">Documents uploaded to this workspace</p>
          </div>
          <button
            onClick={() => onNavigate('documents')}
            className="text-xs text-sky-400 hover:text-sky-300 font-medium"
          >
            View All Documents →
          </button>
        </div>

        <div className="overflow-x-auto">
          {recentDocs.length === 0 ? (
            <div className="p-12 text-center text-slate-500 text-xs">
              No documents uploaded yet. Click "Upload Document" to index your first file.
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/40 text-slate-400 font-medium">
                  <th className="px-6 py-3">Document Name</th>
                  <th className="px-4 py-3">Format</th>
                  <th className="px-4 py-3">Pages</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Uploaded</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentDocs.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-6 py-3.5 font-medium text-slate-200 flex items-center space-x-2.5">
                      <FileText className="w-4 h-4 text-sky-400 flex-shrink-0" />
                      <span className="truncate max-w-[240px]" title={doc.filename}>
                        {doc.filename}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 uppercase font-mono text-[11px] text-slate-400">
                      {doc.file_type}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-slate-300">{doc.page_count}</td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          doc.status === 'COMPLETED'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : doc.status === 'FAILED'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/20 animate-pulse'
                        }`}
                      >
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-500">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-3.5 text-right">
                      <button
                        onClick={() => onViewDoc(doc.id, 1)}
                        className="text-sky-400 hover:text-sky-300 font-medium hover:underline text-xs"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
