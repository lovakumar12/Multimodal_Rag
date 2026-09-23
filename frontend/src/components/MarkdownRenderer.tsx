import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { FileText } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  onOpenCitation?: (docName: string, page: number) => void;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, onOpenCitation }) => {
  // Regex to detect citations like [king_Ashoka.pdf, Page 1] or [Doc: filename, Page X]
  // We can render custom citation pills by transforming bracketed citations
  const renderTextWithCitations = (text: string) => {
    // Matches patterns like [filename.pdf, Page X] or [Doc: filename.pdf, Page X]
    const citationRegex = /\[(?:Doc:\s*)?([a-zA-Z0-9_\-\.\s]+?),\s*Page\s*(\d+)(?:,\s*Page\s*(\d+))?\]/g;

    const parts: (string | React.ReactNode)[] = [];
    let lastIndex = 0;
    let match;

    while ((match = citationRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.substring(lastIndex, match.index));
      }

      const docName = match[1].trim();
      const pageNum1 = parseInt(match[2], 10);
      const pageNum2 = match[3] ? parseInt(match[3], 10) : null;

      parts.push(
        <button
          key={`cite-${match.index}`}
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (onOpenCitation) {
              onOpenCitation(docName, pageNum1);
            }
          }}
          className="inline-flex items-center space-x-1 mx-1 px-2 py-0.5 rounded-full bg-sky-500/15 hover:bg-sky-500/25 text-sky-400 hover:text-sky-300 border border-sky-500/30 text-[11px] font-medium transition-all shadow-xs align-baseline cursor-pointer"
          title={`Click to view ${docName} at Page ${pageNum1}`}
        >
          <FileText className="w-3 h-3 text-sky-400" />
          <span>{docName.replace(/\.[^/.]+$/, '')} · p.{pageNum1}{pageNum2 ? `, ${pageNum2}` : ''}</span>
        </button>
      );

      lastIndex = match.index + match[0].length;
    }

    if (lastIndex < text.length) {
      parts.push(text.substring(lastIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  return (
    <div className="chatgpt-markdown text-slate-100 text-[14.5px] leading-7 font-sans space-y-3">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => {
            // Process children to find text nodes with citations
            return (
              <p className="my-2.5 leading-relaxed text-slate-200">
                {React.Children.map(children, (child) => {
                  if (typeof child === 'string') {
                    return renderTextWithCitations(child);
                  }
                  return child;
                })}
              </p>
            );
          },
          ul: ({ children }) => (
            <ul className="my-3 space-y-2.5 pl-6 list-disc marker:text-sky-400 text-slate-200">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="my-3 space-y-2.5 pl-6 list-decimal marker:text-sky-400 font-medium text-slate-200">
              {children}
            </ol>
          ),
          li: ({ children }) => {
            return (
              <li className="leading-relaxed pl-1">
                {React.Children.map(children, (child) => {
                  if (typeof child === 'string') {
                    return renderTextWithCitations(child);
                  }
                  return child;
                })}
              </li>
            );
          },
          strong: ({ children }) => (
            <strong className="font-semibold text-white tracking-wide">
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em className="text-sky-200 italic font-medium">
              {children}
            </em>
          ),
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-white mt-5 mb-2.5 border-b border-slate-800 pb-1.5 flex items-center space-x-2">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-semibold text-white mt-4 mb-2 flex items-center space-x-2">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold text-slate-100 mt-3 mb-1.5">
              {children}
            </h3>
          ),
          blockquote: ({ children }) => (
            <blockquote className="my-3 pl-4 border-l-4 border-sky-500/60 bg-sky-500/5 py-1.5 pr-3 rounded-r-lg italic text-slate-300 text-sm">
              {children}
            </blockquote>
          ),
          code: ({ children, className }) => {
            const isInline = !className;
            return isInline ? (
              <code className="px-1.5 py-0.5 rounded-md bg-slate-800 border border-slate-700/60 text-sky-300 font-mono text-[12px]">
                {children}
              </code>
            ) : (
              <pre className="my-3 p-3.5 rounded-xl bg-slate-950 border border-slate-800 overflow-x-auto font-mono text-xs text-slate-200 leading-relaxed">
                <code>{children}</code>
              </pre>
            );
          },
          table: ({ children }) => (
            <div className="overflow-x-auto my-3 border border-slate-800 rounded-xl">
              <table className="min-w-full divide-y divide-slate-800 text-left text-xs">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="px-3.5 py-2.5 bg-slate-950 font-semibold text-white">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3.5 py-2 text-slate-300 border-t border-slate-800/60">
              {children}
            </td>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
