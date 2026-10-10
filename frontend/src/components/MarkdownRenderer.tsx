import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import rehypeRaw from 'rehype-raw';
import { FileText } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  onOpenCitation?: (docName: string, page: number) => void;
}

/**
 * Normalizes LaTeX math expressions in markdown text so they are properly
 * recognized and parsed by remark-math and rendered by KaTeX without syntax breaks.
 */
function normalizeMarkdownMath(raw: string): string {
  if (!raw) return '';

  let text = raw;

  // 0. Convert Asian/Fullwidth citation brackets 【...】 to standard [...]
  text = text.replace(/【/g, '[').replace(/】/g, ']');

  // 1. Standard LaTeX block delimiters: \[ ... \] -> $$ ... $$
  text = text.replace(/\\\[([\s\S]*?)\\\]/g, (_, formula) => `\n\n$$\n${formula.trim()}\n$$\n\n`);

  // 2. Standard LaTeX inline delimiters: \( ... \) -> $ ... $
  text = text.replace(/\\\(([\s\S]*?)\\\)/g, (_, formula) => `$${formula.trim()}$`);

  // 3. Handle <br> \displaystyle ... <br> pattern
  text = text.replace(/<br\s*\/?>\s*\\displaystyle\s*([\s\S]*?)\s*<br\s*\/?>/gi, (_, formula) => {
    return `<br>\n\n$$\n${formula.trim()}\n$$\n\n<br>`;
  });

  // 4. Handle standalone LaTeX matrix or aligned blocks:
  text = text.replace(/(?:^|\n)\s*([A-Za-z0-9_'\^= ]*?\\begin\{(?:bmatrix|pmatrix|vmatrix|Vmatrix|matrix|aligned|align|gather)\}[\s\S]*?\\end\{(?:bmatrix|pmatrix|vmatrix|Vmatrix|matrix|aligned|align|gather)\}[^\n$]*)/g, (match, body) => {
    if (body.includes('$$')) return match;
    const cleaned = body.replace(/\$([^\n$]+)\$/g, '$1').trim();
    return `\n\n$$\n${cleaned}\n$$\n\n`;
  });

  // 5. Standalone math lines starting with \text{Attention}, \text{MultiHead}, etc.:
  text = text.replace(/(?:^|\n)\s*(\\text\{(?:Attention|MultiHead|Concat|Softmax|softmax)\}[^\n]+)/g, (match, line) => {
    if (line.includes('$$')) return match;
    const cleaned = line.replace(/\$([^\n$]+)\$/g, '$1').trim();
    return `\n\n$$\n${cleaned}\n$$\n\n`;
  });

  // 6. Handle table rows containing LaTeX or math variables without dollars:
  const lines = text.split('\n');
  const processedLines = lines.map(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('|') && trimmed.endsWith('|') && !trimmed.includes('---')) {
      const cells = line.split('|');
      const newCells = cells.map((cell, idx) => {
        if (idx === 0 || idx === cells.length - 1) return cell;
        // In table cells, convert block math $$ to inline math $
        let cTrim = cell.trim().replace(/\$\$/g, '$');
        if ((cTrim.includes('\\') || /([A-Za-z]_[A-Za-z0-9]+|[A-Za-z]\^[A-Za-z0-9]+)/.test(cTrim)) && !cTrim.includes('$')) {
          if (/\\(text|frac|sqrt|left|right|big|Big|cdot|times|in|mathbb|top|sum|prod|operatorname|begin)\b/.test(cTrim) || /^[A-Za-z0-9_'\^=, \\\{\}\+\-\*\/\(\)]+=[A-Za-z0-9_'\^=, \\\{\}\+\-\*\/\(\)]+$/.test(cTrim)) {
            return ` $${cTrim}$ `;
          }
        }
        return ` ${cTrim} `;
      });
      return newCells.join('|');
    }

    // Standalone lines that look like mathematical formulas without $ or $$:
    if (!trimmed.startsWith('#') && !trimmed.startsWith('-') && !trimmed.startsWith('*') && !trimmed.startsWith('|') && !trimmed.includes('$$') && !trimmed.includes('$')) {
      if (/^[A-Za-z][A-Za-z0-9_'\^]*\s*=\s*[^.\n]+$/.test(trimmed) && (trimmed.includes('_') || trimmed.includes('^') || trimmed.includes('\\'))) {
        return `\n\n$$\n${trimmed}\n$$\n\n`;
      }
    }

    return line;
  });
  text = processedLines.join('\n');

  // 7. Handle lines starting with \displaystyle:
  text = text.replace(/\\displaystyle\s+([^\n<$]+)/g, (_, formula) => {
    return `\n\n$$\n${formula.trim()}\n$$\n\n`;
  });

  // 8. Fix stray $$ at end of bullet
  text = text.replace(/([^$\n]+)\$\$\s*$/gm, (match, before) => {
    if (!before.includes('$$')) {
      return `$$${before.trim()}$$`;
    }
    return match;
  });

  return text;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, onOpenCitation }) => {
  const processedContent = React.useMemo(() => normalizeMarkdownMath(content), [content]);

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
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeRaw, [rehypeKatex, { throwOnError: false, strict: false }]]}
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
        {processedContent}
      </ReactMarkdown>
    </div>
  );
};
