export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  document_count: number;
}

export type DocumentStatus = 'PENDING' | 'UPLOADING' | 'PROCESSING' | 'INDEXING' | 'COMPLETED' | 'FAILED';

export interface DocumentItem {
  id: string;
  kb_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: DocumentStatus;
  page_count: number;
  error_message?: string;
  created_at: string;
  updated_at: string;
}

export interface ExtractedImage {
  id: string;
  page_id: string;
  page_number?: number;
  image_index: number;
  asset_url: string;
  width: number;
  height: number;
  caption?: string;
  semantic_description?: string;
  ocr_text?: string;
  is_diagram_or_chart: boolean;
}

export interface ExtractedTable {
  id: string;
  page_id: string;
  page_number?: number;
  table_index: number;
  headers: string[];
  rows: any[][];
  markdown_content: string;
  caption?: string;
}

export interface DocumentPage {
  id: string;
  page_number: number;
  text_content: string;
  width?: number;
  height?: number;
  rendered_image_path?: string;
  summary?: string;
  images: ExtractedImage[];
  tables: ExtractedTable[];
}

export interface DocumentDetail extends DocumentItem {
  pages: DocumentPage[];
  images_count: number;
  tables_count: number;
  chunks_count: number;
}

export interface SearchResultSource {
  document_id: string;
  document_name: string;
  page: number;
  content_type: string;
  snippet: string;
  score: number;
}

export interface SearchResultVisual {
  asset_id: string;
  type: string;
  document_id: string;
  document_name: string;
  page: number;
  url: string;
  caption?: string;
  semantic_description?: string;
  relevance_score: number;
}

export interface SearchResultTable {
  table_id: string;
  document_id: string;
  document_name: string;
  page: number;
  markdown: string;
  headers: string[];
  rows: any[][];
  caption?: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence?: number;
  sources?: SearchResultSource[];
  visuals?: SearchResultVisual[];
  tables?: SearchResultTable[];
  created_at: string;
}

export interface Conversation {
  id: string;
  kb_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessage[];
}

export interface DashboardStats {
  total_documents: number;
  processing_documents: number;
  completed_documents: number;
  failed_documents: number;
  total_images: number;
  total_tables: number;
  total_chunks: number;
  total_vectors: number;
}
