import axios from 'axios';
import {
  Conversation,
  DashboardStats,
  DocumentDetail,
  DocumentItem,
  DocumentStatus,
  KnowledgeBase,
  SearchResultSource,
  SearchResultTable,
  SearchResultVisual,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_PREFIX = `${API_BASE_URL}/api/v1`;

const api = axios.create({
  baseURL: API_PREFIX,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Stats
  async getStats(): Promise<DashboardStats> {
    const res = await api.get('/stats');
    return res.data;
  },

  // Knowledge Bases
  async getKnowledgeBases(): Promise<KnowledgeBase[]> {
    const res = await api.get('/knowledge-bases');
    return res.data;
  },

  async createKnowledgeBase(name: string, description?: string): Promise<KnowledgeBase> {
    const res = await api.post('/knowledge-bases', { name, description });
    return res.data;
  },

  async deleteKnowledgeBase(id: string): Promise<void> {
    await api.delete(`/knowledge-bases/${id}`);
  },

  // Documents
  async getDocuments(kbId?: string): Promise<DocumentItem[]> {
    const params = kbId ? { kb_id: kbId } : {};
    const res = await api.get('/documents', { params });
    return res.data;
  },

  async getDocumentDetail(id: string): Promise<DocumentDetail> {
    const res = await api.get(`/documents/${id}`);
    return res.data;
  },

  async getDocumentStatus(id: string): Promise<{ id: string; status: DocumentStatus; page_count: number }> {
    const res = await api.get(`/documents/${id}/status`);
    return res.data;
  },

  async uploadDocument(kbId: string, file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('kb_id', kbId);
    formData.append('file', file);
    const res = await api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  async deleteDocument(id: string): Promise<void> {
    await api.delete(`/documents/${id}`);
  },

  // Chat
  async sendChat(
    kbId: string,
    query: string,
    conversationId?: string,
    topK: number = 5
  ): Promise<{
    conversation_id: string;
    message_id: string;
    answer: string;
    confidence: number;
    sources: SearchResultSource[];
    visuals: SearchResultVisual[];
    tables: SearchResultTable[];
  }> {
    const res = await api.post('/chat', {
      kb_id: kbId,
      query,
      conversation_id: conversationId,
      top_k: topK,
    });
    return res.data;
  },

  async getConversations(kbId: string): Promise<Conversation[]> {
    const res = await api.get('/conversations', { params: { kb_id: kbId } });
    return res.data;
  },

  async getConversation(id: string): Promise<Conversation> {
    const res = await api.get(`/conversations/${id}`);
    return res.data;
  },

  async deleteConversation(id: string): Promise<void> {
    await api.delete(`/conversations/${id}`);
  },

  // Helper for full asset URLs
  getAssetUrl(relativePathOrUrl: string): string {
    if (!relativePathOrUrl) return '';
    if (relativePathOrUrl.startsWith('http')) return relativePathOrUrl;
    const clean = relativePathOrUrl.startsWith('/') ? relativePathOrUrl : `/${relativePathOrUrl}`;
    return `${API_BASE_URL}${clean}`;
  },
};
