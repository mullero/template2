/** Documents API repository module — the async AI-extraction slice. */
import { apiClient, apiGet, apiPost } from '@/api/client';

export type DocumentStatus =
  | 'processing'
  | 'needs_review'
  | 'committed'
  | 'duplicate'
  | 'failed';

export interface DocumentModel {
  id: string;
  tenant_id: string;
  filename: string;
  status: string;
  confidence: number | null;
  extraction: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface UploadResponse {
  document: DocumentModel;
  job_id: string;
  duplicate: boolean;
}

export async function uploadDocument(
  file: File,
  opts?: { forceReview?: boolean },
): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  const query = opts?.forceReview === true ? '?force_review=true' : '';
  const response = await apiClient.post<UploadResponse>(`/documents/upload${query}`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export function listDocuments(pendingReview = false): Promise<DocumentModel[]> {
  const query = pendingReview ? '?pending_review=true' : '';
  return apiGet<DocumentModel[]>(`/documents${query}`);
}

export function getDocument(id: string): Promise<DocumentModel> {
  return apiGet<DocumentModel>(`/documents/${id}`);
}

export function reviewDocument(id: string, accept: boolean): Promise<DocumentModel> {
  return apiPost<DocumentModel>(`/documents/${id}/review?accept=${String(accept)}`);
}
