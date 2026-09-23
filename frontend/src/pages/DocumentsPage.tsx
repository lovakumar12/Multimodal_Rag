import React, { useEffect, useState } from 'react';
import { FileText, Trash2, Eye, Plus, RefreshCw, FileSearch, Layers } from 'lucide-react';
import { apiClient } from '../api/client';
import { DocumentItem, KnowledgeBase } from '../types';

interface DocumentsPageProps {
  selectedKb: KnowledgeBase | null;
  onOpenUpload: () => void;
  onInspectDoc: (docId: string, page: number) => void;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({
  selectedKb,
  onOpenUpload,
  onInspectDoc,
}) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    loadDocuments();
  }, [selectedKb]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getDocuments(selectedKb?.id);
      setDocuments(data);
    } catch (e) {
      console.error('Failed to load documents', e);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document and its indexed vectors?')) return;
    try {
      await apiClient.deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      alert('Failed to delete document');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Documents</h1>
          <p className="text-sm text-slate-400 mt-1">
            Browse and inspect ingested documents, extracted visual diagrams, and structured tables.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={loadDocuments}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh List"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={onOpenUpload}
            className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-lg shadow-sky-600/20 transition-all flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Upload Documents</span>
          </button>
        </div>
      </div>

      {/* Documents Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-lg">
        {loading ? (
          <div className="p-16 text-center text-slate-500 text-xs">Loading documents...</div>
        ) : documents.length === 0 ? (
          <div className="p-16 text-center space-y-3">
            <FileSearch className="w-10 h-10 text-slate-600 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-200">No documents in this view</h3>
            <p className="text-xs text-slate-500">
              Upload PDF research reports, slide decks, or diagrams to index them into this knowledge base.
            </p>
          </div>
        ) : (
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-950/60 text-slate-400 font-medium">
                <th className="px-6 py-3.5">Name</th>
                <th className="px-4 py-3.5">Format</th>
                <th className="px-4 py-3.5">Size</th>
                <th className="px-4 py-3.5">Pages</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5">Created</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-medium text-slate-200 flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="truncate max-w-[280px]">
                      <span className="truncate block font-semibold" title={doc.filename}>
                        {doc.filename}
                      </span>
                      {doc.error_message && (
                        <span className="text-[10px] text-rose-400 block truncate">{doc.error_message}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 uppercase font-mono text-[11px] text-slate-400">{doc.file_type}</td>
                  <td className="px-4 py-4 text-slate-400 font-mono text-[11px]">
                    {(doc.file_size / 1024).toFixed(0)} KB
                  </td>
                  <td className="px-4 py-4 text-slate-300 font-mono">{doc.page_count}</td>
                  <td className="px-4 py-4">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
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
                  <td className="px-4 py-4 text-slate-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button
                      onClick={() => onInspectDoc(doc.id, 1)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs font-medium transition-colors"
                      title="Inspect extracted pages and visuals"
                    >
                      Inspect
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Delete Document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
