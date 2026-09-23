import React, { useState } from 'react';
import { Maximize2, X, Download, FileText, CheckCircle2 } from 'lucide-react';
import { SearchResultVisual } from '../types';
import { apiClient } from '../api/client';

interface VisualEvidenceCardProps {
  visual: SearchResultVisual;
  onOpenSource?: (docId: string, page: number) => void;
}

export const VisualEvidenceCard: React.FC<VisualEvidenceCardProps> = ({ visual, onOpenSource }) => {
  const [isZoomed, setIsZoomed] = useState(false);
  const fullUrl = apiClient.getAssetUrl(visual.url);
  const relevancePercent = Math.round(visual.relevance_score * 100);

  return (
    <>
      <div className="group relative bg-slate-950 border border-slate-800 hover:border-sky-500/50 rounded-xl overflow-hidden transition-all duration-200 shadow-xs hover:shadow-sky-500/10 flex flex-col">
        {/* Top bar with Badge & Relevance */}
        <div className="px-3 py-1.5 bg-slate-900/90 border-b border-slate-800/80 flex items-center justify-between text-xs">
          <div className="flex items-center space-x-1.5">
            <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20 uppercase tracking-wider">
              {visual.type}
            </span>
            <span className="text-slate-400 font-mono text-[11px]">Page {visual.page}</span>
          </div>
          <div className="flex items-center space-x-1" title="Semantic relevance score">
            <div className="w-10 h-1 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-sky-500 to-emerald-400"
                style={{ width: `${relevancePercent}%` }}
              />
            </div>
            <span className="text-[10px] font-mono text-emerald-400 font-medium">{relevancePercent}%</span>
          </div>
        </div>

        {/* Thumbnail Preview with hover zoom action */}
        <div
          onClick={() => setIsZoomed(true)}
          className="relative h-36 bg-slate-900/40 flex items-center justify-center p-2 cursor-pointer overflow-hidden"
        >
          <img
            src={fullUrl}
            alt={visual.caption || 'Extracted document visual'}
            className="max-h-full max-w-full object-contain rounded transition-transform duration-300 group-hover:scale-105"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-slate-950/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <span className="bg-slate-900/95 text-white text-xs px-2.5 py-1 rounded-lg border border-slate-700 flex items-center space-x-1 shadow-lg">
              <Maximize2 className="w-3.5 h-3.5 text-sky-400" />
              <span>Inspect</span>
            </span>
          </div>
        </div>

        {/* Description & Doc reference */}
        <div className="p-2.5 bg-slate-950 flex-1 flex flex-col justify-between text-xs border-t border-slate-800/60">
          <div>
            <p className="font-medium text-slate-200 line-clamp-1 text-[11px]" title={visual.caption || 'Visual Evidence'}>
              {visual.caption || 'Extracted Document Artifact'}
            </p>
            {visual.semantic_description && (
              <p className="text-slate-400 text-[10px] mt-1 line-clamp-2 leading-relaxed">
                {visual.semantic_description}
              </p>
            )}
          </div>
          <div className="mt-2 pt-1.5 border-t border-slate-900 flex items-center justify-between text-[10px] text-slate-500">
            <span className="truncate max-w-[120px]" title={visual.document_name}>
              {visual.document_name}
            </span>
            {onOpenSource && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenSource(visual.document_id, visual.page);
                }}
                className="text-sky-400 hover:text-sky-300 font-medium hover:underline"
              >
                View Page
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Fullscreen Zoom Modal */}
      {isZoomed && (
        <div className="fixed inset-0 z-50 bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 animate-in fade-in duration-150">
          <div className="relative max-w-4xl w-full bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col max-h-[90vh]">
            <div className="px-5 py-3.5 bg-slate-950/90 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20 uppercase tracking-wider">
                  {visual.type}
                </span>
                <h3 className="font-semibold text-white text-sm truncate max-w-md">
                  {visual.caption || `Artifact from ${visual.document_name}`}
                </h3>
                <span className="text-slate-400 font-mono text-xs">Page {visual.page}</span>
              </div>
              <div className="flex items-center space-x-2">
                <a
                  href={fullUrl}
                  download
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center space-x-1 text-xs"
                >
                  <Download className="w-4 h-4" />
                  <span className="hidden sm:inline">Save</span>
                </a>
                <button
                  onClick={() => setIsZoomed(false)}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="flex-1 bg-slate-950 flex items-center justify-center p-4 overflow-auto">
              <img
                src={fullUrl}
                alt={visual.caption || 'Enlarged visual artifact'}
                className="max-h-[65vh] max-w-full object-contain rounded-lg shadow-lg border border-slate-800"
              />
            </div>

            {visual.semantic_description && (
              <div className="p-4 bg-slate-900/90 border-t border-slate-800 text-xs text-slate-300 leading-relaxed max-h-28 overflow-y-auto">
                <span className="font-semibold text-sky-400 block mb-1">Visual Analysis & Context:</span>
                {visual.semantic_description}
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
