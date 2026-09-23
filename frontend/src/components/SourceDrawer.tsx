import React, { useEffect, useState } from 'react';
import { X, FileText, ChevronRight, ExternalLink } from 'lucide-react';
import { apiClient } from '../api/client';
import { DocumentDetail, DocumentPage } from '../types';

interface SourceDrawerProps {
  documentId: string | null;
  targetPage: number | null;
  onClose: () => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ documentId, targetPage, onClose }) => {
  const [docDetail, setDocDetail] = useState<DocumentDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [currentPageNum, setCurrentPageNum] = useState<number>(targetPage || 1);

  useEffect(() => {
    if (documentId) {
      loadDoc(documentId);
    }
  }, [documentId]);

  useEffect(() => {
    if (targetPage) {
      setCurrentPageNum(targetPage);
    }
  }, [targetPage]);

  const loadDoc = async (id: string) => {
    setLoading(true);
    try {
      const detail = await apiClient.getDocumentDetail(id);
      setDocDetail(detail);
    } catch (e) {
      console.error('Failed to load document details', e);
    } finally {
      setLoading(false);
    }
  };

  if (!documentId) return null;

  const activePage: DocumentPage | undefined = docDetail?.pages.find(
    (p) => p.page_number === currentPageNum
  );

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-2xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="h-16 px-6 border-b border-slate-800 flex items-center justify-between bg-slate-950/70">
        <div className="flex items-center space-x-3 overflow-hidden">
          <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400">
            <FileText className="w-5 h-5" />
          </div>
          <div className="truncate">
            <h3 className="font-semibold text-slate-100 truncate text-sm">
              {docDetail?.filename || 'Document Source'}
            </h3>
            <span className="text-xs text-slate-400">
              Page {currentPageNum} of {docDetail?.page_count || 1}
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Page Selector Tabs */}
      {docDetail && docDetail.pages.length > 1 && (
        <div className="px-6 py-2 bg-slate-950 border-b border-slate-800/80 flex items-center space-x-1.5 overflow-x-auto">
          {docDetail.pages.map((p) => (
            <button
              key={p.page_number}
              onClick={() => setCurrentPageNum(p.page_number)}
              className={`px-3 py-1 rounded-md text-xs font-mono transition-all ${
                currentPageNum === p.page_number
                  ? 'bg-sky-600 text-white font-semibold'
                  : 'bg-slate-800/70 text-slate-400 hover:text-slate-200'
              }`}
            >
              P. {p.page_number}
            </button>
          ))}
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {loading ? (
          <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
            Loading document evidence...
          </div>
        ) : (
          <>
            {/* Rendered Page Image Preview if available */}
            {activePage?.rendered_image_path && (
              <div className="space-y-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                  Original Document Page View:
                </span>
                <div className="border border-slate-800 rounded-xl overflow-hidden bg-slate-950 p-2 flex justify-center shadow-inner">
                  <img
                    src={activePage.rendered_image_path}
                    alt={`Page ${currentPageNum}`}
                    className="max-h-[380px] w-auto object-contain rounded border border-slate-800/50"
                  />
                </div>
              </div>
            )}

            {/* Extracted Images on this page */}
            {activePage?.images && activePage.images.length > 0 && (
              <div className="space-y-3">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                  Original Extracted Visuals on Page {currentPageNum}:
                </span>
                <div className="grid grid-cols-2 gap-3">
                  {activePage.images.map((img) => (
                    <div
                      key={img.id}
                      className="border border-slate-800 rounded-lg p-2 bg-slate-950 flex flex-col items-center"
                    >
                      <img
                        src={apiClient.getAssetUrl(img.asset_url)}
                        alt={img.caption || 'Extracted Visual'}
                        className="max-h-36 object-contain rounded"
                      />
                      {img.caption && (
                        <p className="text-[11px] text-slate-400 mt-2 text-center line-clamp-1">{img.caption}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Tables on this page */}
            {activePage?.tables && activePage.tables.length > 0 && (
              <div className="space-y-3">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                  Tables on Page {currentPageNum}:
                </span>
                {activePage.tables.map((tbl) => (
                  <div key={tbl.id} className="border border-slate-800 rounded-lg p-3 bg-slate-950 font-mono text-xs overflow-x-auto">
                    <pre className="text-slate-300">{tbl.markdown_content}</pre>
                  </div>
                ))}
              </div>
            )}

            {/* Extracted Text */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                Extracted Text Content:
              </span>
              <div className="border border-slate-800 rounded-xl p-4 bg-slate-950 text-xs text-slate-300 leading-relaxed font-mono whitespace-pre-wrap max-h-72 overflow-y-auto">
                {activePage?.text_content || 'No text extracted on this page.'}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
