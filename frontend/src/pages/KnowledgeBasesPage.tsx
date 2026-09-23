import React, { useEffect, useState } from 'react';
import { Database, Plus, Trash2, FolderOpen, Calendar, FileText, CheckCircle2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { KnowledgeBase } from '../types';

interface KnowledgeBasesPageProps {
  selectedKb: KnowledgeBase | null;
  setSelectedKb: (kb: KnowledgeBase | null) => void;
  onNavigate: (tab: 'dashboard' | 'kb' | 'documents' | 'chat') => void;
  onOpenUpload: () => void;
}

export const KnowledgeBasesPage: React.FC<KnowledgeBasesPageProps> = ({
  selectedKb,
  setSelectedKb,
  onNavigate,
  onOpenUpload,
}) => {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [name, setName] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [creating, setCreating] = useState<boolean>(false);

  useEffect(() => {
    loadKbs();
  }, []);

  const loadKbs = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getKnowledgeBases();
      setKbs(data);
    } catch (e) {
      console.error('Failed to load KBs', e);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    try {
      const created = await apiClient.createKnowledgeBase(name.trim(), description.trim() || undefined);
      setKbs((prev) => [created, ...prev]);
      setSelectedKb(created);
      setName('');
      setDescription('');
      setShowCreateModal(false);
    } catch (err) {
      alert('Failed to create knowledge base');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this Knowledge Base and all its documents?')) return;
    try {
      await apiClient.deleteKnowledgeBase(id);
      setKbs((prev) => prev.filter((k) => k.id !== id));
      if (selectedKb?.id === id) {
        setSelectedKb(null);
      }
    } catch (err) {
      alert('Failed to delete knowledge base');
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 animate-in fade-in duration-150">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Knowledge Bases</h1>
          <p className="text-sm text-slate-400 mt-1">
            Organize documents, vector indices, and conversational context into separate workspaces.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold shadow-lg shadow-sky-600/20 transition-all flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Knowledge Base</span>
        </button>
      </div>

      {/* Grid of KBs */}
      {loading ? (
        <div className="p-12 text-center text-slate-500 text-xs">Loading Knowledge Bases...</div>
      ) : kbs.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center space-y-4">
          <Database className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-slate-200">No Knowledge Bases created yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Create your first knowledge base to organize and index PDFs, PPTX slides, and images.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 rounded-xl bg-sky-600 text-white text-xs font-medium hover:bg-sky-500"
          >
            Create Knowledge Base
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {kbs.map((kb) => {
            const isSelected = selectedKb?.id === kb.id;
            return (
              <div
                key={kb.id}
                onClick={() => setSelectedKb(kb)}
                className={`bg-slate-900 border rounded-2xl p-6 flex flex-col justify-between cursor-pointer transition-all duration-200 shadow-md ${
                  isSelected
                    ? 'border-sky-500 ring-2 ring-sky-500/20 shadow-sky-500/10'
                    : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <div className="w-10 h-10 rounded-xl bg-sky-500/10 text-sky-400 flex items-center justify-center">
                      <Database className="w-5 h-5" />
                    </div>
                    {isSelected && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-sky-500/20 text-sky-400 border border-sky-500/30">
                        ACTIVE
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-semibold text-white tracking-tight">{kb.name}</h3>
                  <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                    {kb.description || 'No description provided.'}
                  </p>
                </div>

                <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                  <div className="flex items-center space-x-1">
                    <FileText className="w-3.5 h-3.5 text-slate-500" />
                    <span>{kb.document_count} documents</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedKb(kb);
                        onNavigate('chat');
                      }}
                      className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-sky-400 text-xs font-medium"
                    >
                      Chat
                    </button>
                    <button
                      onClick={(e) => handleDelete(kb.id, e)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10"
                      title="Delete KB"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-semibold text-white">Create Knowledge Base</h3>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. AI Research Papers, Financial Reports"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Description (Optional)</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Summary of documents in this knowledge base..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500 h-20 resize-none"
                />
              </div>
              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !name.trim()}
                  className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold disabled:opacity-50"
                >
                  {creating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
