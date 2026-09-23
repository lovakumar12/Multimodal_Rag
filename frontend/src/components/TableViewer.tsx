import React, { useState } from 'react';
import { Table, Copy, Check, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import { SearchResultTable } from '../types';

interface TableViewerProps {
  table: SearchResultTable;
  onOpenSource?: (docId: string, page: number) => void;
}

export const TableViewer: React.FC<TableViewerProps> = ({ table, onOpenSource }) => {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const copyMarkdown = () => {
    navigator.clipboard.writeText(table.markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const hasStructuredData =
    table.headers &&
    table.headers.length > 0 &&
    table.rows &&
    table.rows.length > 0;

  return (
    <div className="bg-slate-950/70 border border-slate-800 rounded-xl overflow-hidden shadow-xs my-2.5 transition-all">
      {/* Header bar */}
      <div className="px-3.5 py-2.5 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 truncate">
          <div className="p-1 rounded bg-emerald-500/10 text-emerald-400 flex-shrink-0">
            <Table className="w-3.5 h-3.5" />
          </div>
          <span className="font-semibold text-slate-200 truncate max-w-[240px]">
            {table.caption || `Table from ${table.document_name}`}
          </span>
          <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px] flex-shrink-0">
            Page {table.page}
          </span>
        </div>

        <div className="flex items-center space-x-2 flex-shrink-0">
          {onOpenSource && (
            <button
              onClick={() => onOpenSource(table.document_id, table.page)}
              className="text-xs text-sky-400 hover:text-sky-300 font-medium transition-colors"
            >
              View in Doc
            </button>
          )}
          <button
            onClick={copyMarkdown}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors flex items-center space-x-1"
            title="Copy as Markdown"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="text-[10px] hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Table grid or preview */}
      <div className={`p-3 overflow-x-auto ${isExpanded ? 'max-h-96' : 'max-h-40'} overflow-y-auto transition-all`}>
        {hasStructuredData ? (
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-700 bg-slate-900 text-slate-200 font-semibold sticky top-0">
                {table.headers.map((h, idx) => (
                  <th key={idx} className="p-2 whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono text-[11px]">
              {table.rows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-slate-800/40 transition-colors">
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="p-2 whitespace-nowrap text-slate-300">
                      {String(cell || '')}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-slate-300 text-xs leading-relaxed font-sans whitespace-pre-wrap bg-slate-900/50 p-2.5 rounded-lg border border-slate-800/60">
            {table.markdown}
          </div>
        )}
      </div>
    </div>
  );
};
