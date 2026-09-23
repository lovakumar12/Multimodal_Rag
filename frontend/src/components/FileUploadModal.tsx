import React, { useState } from 'react';
import { UploadCloud, X, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { apiClient } from '../api/client';
import { KnowledgeBase } from '../types';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedKb: KnowledgeBase | null;
  onUploaded: () => void;
}

interface UploadQueueItem {
  file: File;
  status: 'PENDING' | 'UPLOADING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  docId?: string;
  error?: string;
}

export const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  onClose,
  selectedKb,
  onUploaded,
}) => {
  const [queue, setQueue] = useState<UploadQueueItem[]>([]);
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);

  if (!isOpen) return null;

  const handleFiles = (files: FileList | null) => {
    if (!files) return;
    const newItems: UploadQueueItem[] = Array.from(files).map((f) => ({
      file: f,
      status: 'PENDING',
    }));
    setQueue((prev) => [...prev, ...newItems]);
  };

  const startUpload = async () => {
    if (!selectedKb) {
      alert('Please select or create a Knowledge Base first.');
      return;
    }

    setIsProcessing(true);

    for (let i = 0; i < queue.length; i++) {
      if (queue[i].status === 'COMPLETED') continue;

      // Update to UPLOADING
      setQueue((prev) =>
        prev.map((item, idx) => (idx === i ? { ...item, status: 'UPLOADING' } : item))
      );

      try {
        const doc = await apiClient.uploadDocument(selectedKb.id, queue[i].file);

        // Update to PROCESSING
        setQueue((prev) =>
          prev.map((item, idx) => (idx === i ? { ...item, status: 'PROCESSING', docId: doc.id } : item))
        );

        // Poll for completion
        let isDone = false;
        let attempts = 0;
        while (!isDone && attempts < 40) {
          await new Promise((r) => setTimeout(r, 1500));
          attempts++;
          try {
            const statusRes = await apiClient.getDocumentStatus(doc.id);
            if (statusRes.status === 'COMPLETED') {
              setQueue((prev) =>
                prev.map((item, idx) => (idx === i ? { ...item, status: 'COMPLETED' } : item))
              );
              isDone = true;
            } else if (statusRes.status === 'FAILED') {
              setQueue((prev) =>
                prev.map((item, idx) =>
                  idx === i ? { ...item, status: 'FAILED', error: 'Extraction or indexing failed' } : item
                )
              );
              isDone = true;
            }
          } catch (e) {
            // ignore polling transient error
          }
        }
      } catch (err: any) {
        setQueue((prev) =>
          prev.map((item, idx) =>
            idx === i
              ? {
                  ...item,
                  status: 'FAILED',
                  error: err.response?.data?.error?.message || 'Upload failed',
                }
              : item
          )
        );
      }
    }

    setIsProcessing(false);
    onUploaded();
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div>
            <h3 className="font-semibold text-slate-100 text-sm">Upload Documents</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Knowledge Base: <span className="text-sky-400 font-medium">{selectedKb?.name || 'None'}</span>
            </p>
          </div>
          <button onClick={onClose} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Drag & drop zone */}
        <div className="p-6 space-y-4">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              handleFiles(e.dataTransfer.files);
            }}
            className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all cursor-pointer ${
              isDragging
                ? 'border-sky-500 bg-sky-500/10'
                : 'border-slate-700 hover:border-slate-600 bg-slate-950/50'
            }`}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <div className="p-3 rounded-xl bg-sky-500/10 text-sky-400 mb-3">
              <UploadCloud className="w-8 h-8" />
            </div>
            <p className="text-sm font-semibold text-slate-200">
              Drag & Drop your documents here or <span className="text-sky-400 underline">Browse</span>
            </p>
            <p className="text-xs text-slate-500 mt-1">
              Supports PDF, PowerPoint (PPTX), Word (DOCX), and Images (PNG, JPG)
            </p>
            <input
              id="file-input"
              type="file"
              multiple
              accept=".pdf,.pptx,.docx,.png,.jpg,.jpeg,.webp"
              className="hidden"
              onChange={(e) => handleFiles(e.target.files)}
            />
          </div>

          {/* Queued files */}
          {queue.length > 0 && (
            <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
              {queue.map((item, idx) => (
                <div
                  key={idx}
                  className="px-3 py-2 bg-slate-950 border border-slate-800/90 rounded-lg flex items-center justify-between text-xs"
                >
                  <div className="flex items-center space-x-2.5 truncate">
                    <FileText className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <span className="font-medium text-slate-200 truncate">{item.file.name}</span>
                    <span className="text-[11px] text-slate-500">
                      ({(item.file.size / 1024).toFixed(0)} KB)
                    </span>
                  </div>

                  <div className="flex items-center space-x-2">
                    {item.status === 'PENDING' && (
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px]">
                        Pending
                      </span>
                    )}
                    {item.status === 'UPLOADING' && (
                      <span className="px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 flex items-center space-x-1 text-[10px]">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Uploading</span>
                      </span>
                    )}
                    {item.status === 'PROCESSING' && (
                      <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 flex items-center space-x-1 text-[10px]">
                        <Loader2 className="w-3 h-3 animate-spin" />
                        <span>Indexing</span>
                      </span>
                    )}
                    {item.status === 'COMPLETED' && (
                      <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 flex items-center space-x-1 text-[10px]">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Completed</span>
                      </span>
                    )}
                    {item.status === 'FAILED' && (
                      <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 flex items-center space-x-1 text-[10px]">
                        <AlertCircle className="w-3 h-3" />
                        <span>Failed</span>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer controls */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <button
            onClick={() => setQueue([])}
            disabled={isProcessing || queue.length === 0}
            className="text-xs text-slate-400 hover:text-slate-200 disabled:opacity-40"
          >
            Clear All
          </button>
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
            >
              Close
            </button>
            <button
              onClick={startUpload}
              disabled={isProcessing || queue.length === 0}
              className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-sky-600/20 flex items-center space-x-1.5"
            >
              {isProcessing && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{isProcessing ? 'Processing...' : 'Upload & Process'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
