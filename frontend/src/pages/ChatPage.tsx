import React, { useEffect, useRef, useState } from 'react';
import {
  Send,
  Bot,
  User,
  Sparkles,
  FileText,
  Plus,
  Trash2,
  ChevronDown,
  ChevronUp,
  Image as ImageIcon,
  Table as TableIcon,
  Loader2,
  Copy,
  Check,
  ExternalLink,
} from 'lucide-react';
import { apiClient } from '../api/client';
import { TableViewer } from '../components/TableViewer';
import { VisualEvidenceCard } from '../components/VisualEvidenceCard';
import { MarkdownRenderer } from '../components/MarkdownRenderer';
import { ChatMessage, Conversation, KnowledgeBase, SearchResultSource } from '../types';

interface ChatPageProps {
  selectedKb: KnowledgeBase | null;
  onOpenSource: (docId: string, page: number) => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({ selectedKb, onOpenSource }) => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  
  // Toggles for multimodal sections per message
  const [activeEvidenceTab, setActiveEvidenceTab] = useState<Record<string, 'none' | 'visuals' | 'tables' | 'sources'>>({});
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (selectedKb) {
      loadConversations();
    }
  }, [selectedKb]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const loadConversations = async () => {
    if (!selectedKb) return;
    try {
      const data = await apiClient.getConversations(selectedKb.id);
      setConversations(data);
      const savedConvId = localStorage.getItem(`active_conv_${selectedKb.id}`);
      if (savedConvId && data.some((c) => c.id === savedConvId)) {
        selectConversation(savedConvId);
      } else if (data.length > 0 && !activeConvId) {
        selectConversation(data[0].id);
      } else if (data.length === 0) {
        handleNewChat();
      }
    } catch (e) {
      console.error('Failed to load conversations', e);
    }
  };

  const selectConversation = async (convId: string) => {
    setActiveConvId(convId);
    if (selectedKb) {
      localStorage.setItem(`active_conv_${selectedKb.id}`, convId);
    }
    try {
      const conv = await apiClient.getConversation(convId);
      const mappedMsgs: ChatMessage[] = conv.messages.map((m: any) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        sources: m.sources_json || m.sources || [],
        visuals: m.visuals_json || m.visuals || [],
        tables: m.tables_json || m.tables || [],
        created_at: m.created_at,
      }));
      setMessages(mappedMsgs);
    } catch (e) {
      console.error('Failed to load conversation details', e);
    }
  };

  const handleNewChat = () => {
    setActiveConvId(null);
    if (selectedKb) {
      localStorage.removeItem(`active_conv_${selectedKb.id}`);
    }
    setMessages([]);
  };

  const handleDeleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.deleteConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        handleNewChat();
      }
    } catch (e) {
      alert('Failed to delete conversation');
    }
  };

  const toggleEvidenceTab = (msgId: string, tab: 'visuals' | 'tables' | 'sources') => {
    setActiveEvidenceTab((prev) => {
      const current = prev[msgId] || 'none';
      return { ...prev, [msgId]: current === tab ? 'none' : tab };
    });
  };

  const copyMessage = (msgId: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedMsgId(msgId);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  const handleOpenCitation = (docName: string, page: number, sources?: SearchResultSource[]) => {
    if (!sources || sources.length === 0) return;
    const cleanDocName = docName.toLowerCase().replace(/\.[^/.]+$/, '');
    const matched = sources.find((s) => {
      const sName = s.document_name.toLowerCase().replace(/\.[^/.]+$/, '');
      return sName.includes(cleanDocName) || cleanDocName.includes(sName);
    });
    if (matched) {
      onOpenSource(matched.document_id, page);
    } else if (sources.length > 0) {
      onOpenSource(sources[0].document_id, page);
    }
  };

  const handleSend = async (queryText?: string) => {
    const q = queryText || inputQuery;
    if (!q.trim() || !selectedKb || loading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: q,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const res = await apiClient.sendChat(
        selectedKb.id,
        q,
        activeConvId || undefined
      );

      setActiveConvId(res.conversation_id);
      if (selectedKb) {
        localStorage.setItem(`active_conv_${selectedKb.id}`, res.conversation_id);
      }

      const assistantMsg: ChatMessage = {
        id: res.message_id,
        role: 'assistant',
        content: res.answer,
        confidence: res.confidence,
        sources: res.sources,
        visuals: res.visuals,
        tables: res.tables,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // If visuals are present, auto-open the visuals tab for this message
      if (res.visuals && res.visuals.length > 0) {
        setActiveEvidenceTab((prev) => ({ ...prev, [res.message_id]: 'visuals' }));
      }

      if (!activeConvId) {
        loadConversations();
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: err.response?.data?.error?.message || 'Failed to generate answer. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] overflow-hidden bg-slate-950">
      {/* Sidebar: Conversation history */}
      <div className="w-68 bg-slate-950 border-r border-slate-800/80 flex flex-col justify-between hidden md:flex flex-shrink-0">
        <div className="p-3.5 space-y-3">
          <button
            onClick={handleNewChat}
            className="w-full py-2 px-3.5 rounded-xl bg-slate-900 hover:bg-slate-800/80 text-sky-400 font-semibold text-xs border border-slate-800 flex items-center justify-center space-x-2 transition-all shadow-xs"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Chat</span>
          </button>

          <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-13rem)] pr-1">
            <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider px-2 block mb-1.5">
              Recent Chats
            </span>
            {conversations.map((c) => {
              const isActive = activeConvId === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => selectConversation(c.id)}
                  className={`group px-3 py-2 rounded-xl text-xs flex items-center justify-between cursor-pointer transition-all ${
                    isActive
                      ? 'bg-slate-800/90 text-white font-medium border border-slate-700/80 shadow-xs'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <span className="truncate max-w-[170px]">{c.title || 'Untitled Conversation'}</span>
                  <button
                    onClick={(e) => handleDeleteConversation(c.id, e)}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-rose-400 rounded transition-opacity"
                    title="Delete Chat"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })}
          </div>
        </div>

        <div className="p-3 border-t border-slate-800/60 text-[11px] text-slate-500 flex items-center justify-between">
          <span className="truncate">KB: <strong className="text-slate-300 font-medium">{selectedKb?.name || 'None'}</strong></span>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden">
        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-8 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto space-y-5 animate-in fade-in duration-200 my-auto py-12">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20">
                <Sparkles className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">Multimodal Document Intelligence</h2>
                <p className="text-xs text-slate-400 mt-1.5 leading-relaxed max-w-md mx-auto">
                  Ask questions to retrieve grounded answers with interactive citations, extracted original diagrams,
                  charts, and structured tables.
                </p>
              </div>

              {/* Starter prompts */}
              <div className="grid grid-cols-1 gap-2.5 w-full pt-2">
                <button
                  onClick={() => handleSend('Who is King Ashoka and what was his significance?')}
                  className="px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-sky-500/50 text-xs text-slate-300 text-left transition-all hover:bg-slate-900 group"
                >
                  <span className="text-sky-400 font-semibold block mb-0.5 group-hover:underline">King Ashoka Overview</span>
                  "Who is King Ashoka and what was his significance?"
                </button>
                <button
                  onClick={() => handleSend('What were Ashoka\'s key edicts, social reforms, and animal welfare laws?')}
                  className="px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-emerald-500/50 text-xs text-slate-300 text-left transition-all hover:bg-slate-900 group"
                >
                  <span className="text-emerald-400 font-semibold block mb-0.5 group-hover:underline">Reforms & Governance</span>
                  "What were Ashoka's key edicts, social reforms, and animal welfare laws?"
                </button>
                <button
                  onClick={() => handleSend('Explain the multimodal RAG architecture and show the system diagram.')}
                  className="px-4 py-3 rounded-xl bg-slate-900/80 border border-slate-800 hover:border-indigo-500/50 text-xs text-slate-300 text-left transition-all hover:bg-slate-900 group"
                >
                  <span className="text-indigo-400 font-semibold block mb-0.5 group-hover:underline">Architecture Diagrams</span>
                  "Explain the multimodal RAG architecture and show the system diagram."
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg) => {
              const currentTab = activeEvidenceTab[msg.id] || 'none';
              const hasVisuals = msg.visuals && msg.visuals.length > 0;
              const hasTables = msg.tables && msg.tables.length > 0;
              const hasSources = msg.sources && msg.sources.length > 0;

              return (
                <div
                  key={msg.id}
                  className={`flex space-x-3.5 max-w-3xl mx-auto ${
                    msg.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  {msg.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-md mt-1">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div
                    className={`rounded-2xl transition-all ${
                      msg.role === 'user'
                        ? 'bg-sky-600 text-white px-4 py-2.5 max-w-xl text-[14.5px] leading-relaxed shadow-sm font-medium'
                        : 'bg-slate-900/85 border border-slate-800 text-slate-100 p-5 flex-1 shadow-xs space-y-4'
                    }`}
                  >
                    {/* Message Body */}
                    {msg.role === 'user' ? (
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    ) : (
                      <>
                        {/* ChatGPT-grade Markdown Output with Clickable Citation Pills */}
                        <MarkdownRenderer
                          content={msg.content}
                          onOpenCitation={(docName, page) =>
                            handleOpenCitation(docName, page, msg.sources)
                          }
                        />

                        {/* Evidence & Action Bar */}
                        <div className="pt-3 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-xs">
                          {/* Segmented Evidence Pills */}
                          <div className="flex flex-wrap items-center gap-1.5">
                            {hasVisuals && (
                              <button
                                onClick={() => toggleEvidenceTab(msg.id, 'visuals')}
                                className={`px-2.5 py-1 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer ${
                                  currentTab === 'visuals'
                                    ? 'bg-sky-500/20 text-sky-300 border border-sky-500/40 shadow-xs'
                                    : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-800'
                                }`}
                              >
                                <ImageIcon className="w-3.5 h-3.5 text-sky-400" />
                                <span>Visual Evidence ({msg.visuals!.length})</span>
                                {currentTab === 'visuals' ? <ChevronUp className="w-3 h-3 ml-0.5" /> : <ChevronDown className="w-3 h-3 ml-0.5" />}
                              </button>
                            )}

                            {hasTables && (
                              <button
                                onClick={() => toggleEvidenceTab(msg.id, 'tables')}
                                className={`px-2.5 py-1 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer ${
                                  currentTab === 'tables'
                                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 shadow-xs'
                                    : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-800'
                                }`}
                              >
                                <TableIcon className="w-3.5 h-3.5 text-emerald-400" />
                                <span>Structured Tables ({msg.tables!.length})</span>
                                {currentTab === 'tables' ? <ChevronUp className="w-3 h-3 ml-0.5" /> : <ChevronDown className="w-3 h-3 ml-0.5" />}
                              </button>
                            )}

                            {hasSources && (
                              <button
                                onClick={() => toggleEvidenceTab(msg.id, 'sources')}
                                className={`px-2.5 py-1 rounded-lg text-xs font-medium flex items-center space-x-1.5 transition-all cursor-pointer ${
                                  currentTab === 'sources'
                                    ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-xs'
                                    : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800 hover:bg-slate-800'
                                }`}
                              >
                                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                                <span>Sources ({msg.sources!.length})</span>
                                {currentTab === 'sources' ? <ChevronUp className="w-3 h-3 ml-0.5" /> : <ChevronDown className="w-3 h-3 ml-0.5" />}
                              </button>
                            )}
                          </div>

                          {/* Action Tools */}
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => copyMessage(msg.id, msg.content)}
                              className="px-2 py-1 rounded-md text-slate-400 hover:text-white bg-slate-950 hover:bg-slate-800 border border-slate-800 text-[11px] flex items-center space-x-1 transition-all"
                              title="Copy Answer to clipboard"
                            >
                              {copiedMsgId === msg.id ? (
                                <>
                                  <Check className="w-3 h-3 text-emerald-400" />
                                  <span className="text-emerald-400 font-medium">Copied</span>
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3 h-3" />
                                  <span>Copy</span>
                                </>
                              )}
                            </button>
                          </div>
                        </div>

                        {/* Expandable Multimodal Evidence Panels */}
                        {/* 1. Visual Evidence Panel */}
                        {currentTab === 'visuals' && hasVisuals && (
                          <div className="mt-3 pt-3 border-t border-slate-800/80 animate-in fade-in duration-150">
                            <div className="flex items-center justify-between text-xs text-sky-400 font-semibold mb-2.5">
                              <span className="flex items-center space-x-1.5">
                                <ImageIcon className="w-4 h-4" />
                                <span>Original Visual Evidence from Documents</span>
                              </span>
                              <span className="text-slate-500 text-[11px] font-normal">Click any image to inspect in full resolution</span>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                              {msg.visuals!.map((visual) => (
                                <VisualEvidenceCard
                                  key={visual.asset_id}
                                  visual={visual}
                                  onOpenSource={onOpenSource}
                                />
                              ))}
                            </div>
                          </div>
                        )}

                        {/* 2. Structured Tables Panel */}
                        {currentTab === 'tables' && hasTables && (
                          <div className="mt-3 pt-3 border-t border-slate-800/80 animate-in fade-in duration-150 space-y-2">
                            <div className="flex items-center space-x-1.5 text-xs text-emerald-400 font-semibold mb-2">
                              <TableIcon className="w-4 h-4" />
                              <span>Extracted Structured Tables</span>
                            </div>
                            {msg.tables!.map((tbl) => (
                              <TableViewer key={tbl.table_id} table={tbl} onOpenSource={onOpenSource} />
                            ))}
                          </div>
                        )}

                        {/* 3. Sources & Citations Panel */}
                        {currentTab === 'sources' && hasSources && (
                          <div className="mt-3 pt-3 border-t border-slate-800/80 animate-in fade-in duration-150 space-y-2">
                            <div className="flex items-center space-x-1.5 text-xs text-indigo-400 font-semibold mb-2">
                              <FileText className="w-4 h-4" />
                              <span>Document Excerpts & Page Citations</span>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {msg.sources!.map((s, sIdx) => (
                                <div
                                  key={sIdx}
                                  onClick={() => onOpenSource(s.document_id, s.page)}
                                  className="p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-sky-500/50 cursor-pointer transition-all flex flex-col justify-between group"
                                >
                                  <div>
                                    <div className="flex items-center justify-between text-[11px] mb-1">
                                      <span className="font-semibold text-slate-200 group-hover:text-sky-300 truncate max-w-[180px]">
                                        {s.document_name}
                                      </span>
                                      <span className="px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-400 font-mono text-[10px] font-medium border border-sky-500/20">
                                        Page {s.page}
                                      </span>
                                    </div>
                                    <p className="text-[11px] text-slate-400 line-clamp-3 leading-relaxed">
                                      "{s.snippet}"
                                    </p>
                                  </div>
                                  <div className="mt-2 text-[10px] text-sky-400/80 font-medium flex items-center space-x-1">
                                    <span>View page in drawer</span>
                                    <ExternalLink className="w-2.5 h-2.5" />
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>

                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700/80 flex items-center justify-center flex-shrink-0 mt-1 shadow-xs">
                      <User className="w-4 h-4 text-slate-300" />
                    </div>
                  )}
                </div>
              );
            })
          )}

          {loading && (
            <div className="flex items-center space-x-3.5 max-w-3xl mx-auto">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-md animate-pulse">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl px-5 py-3.5 text-xs text-slate-300 flex items-center space-x-2.5 shadow-sm">
                <Loader2 className="w-4 h-4 animate-spin text-sky-400" />
                <span>Searching text, retrieving diagrams, and formulating grounded response...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* ChatGPT-style Floating Input Bar */}
        <div className="p-4 bg-gradient-to-t from-slate-950 via-slate-950/90 to-transparent">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="max-w-3xl mx-auto relative flex items-center"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder={
                selectedKb
                  ? `Ask anything about ${selectedKb.name}...`
                  : 'Select a Knowledge Base first...'
              }
              disabled={!selectedKb || loading}
              className="w-full bg-slate-900/90 border border-slate-700/80 hover:border-slate-600 focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 rounded-2xl pl-5 pr-14 py-3.5 text-sm text-slate-100 placeholder-slate-400 focus:outline-none disabled:opacity-50 shadow-xl transition-all"
            />
            <button
              type="submit"
              disabled={!selectedKb || loading || !inputQuery.trim()}
              className="absolute right-2 p-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white disabled:opacity-30 disabled:hover:bg-sky-600 transition-all shadow-md shadow-sky-600/30 flex items-center justify-center cursor-pointer"
              title="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <p className="text-[11px] text-slate-500 text-center mt-2 font-sans">
            Multimodal RAG Platform · Cites original document pages, visual evidence & structured tables
          </p>
        </div>
      </div>
    </div>
  );
};
