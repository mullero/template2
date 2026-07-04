/**
 * Documents data hook — the async AI-extraction slice.
 *
 * Maps raw API shapes to view-model rows and exposes { data, loading, error,
 * actions }. Starting an upload enqueues a background job whose id is handed to
 * the global JobProgressProvider (which owns the polling loop that survives
 * navigation); this hook does NOT own that loop.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  listDocuments,
  reviewDocument as apiReviewDocument,
  uploadDocument as apiUploadDocument,
  type DocumentModel,
} from '@/api/documents';
import { documentStrings } from '@/constants/uiStrings';
import { useJobProgress } from '@/hooks/useJobProgress';
import { formatPercent } from '@/utils/format';

export interface DocumentRow {
  id: string;
  filename: string;
  status: string;
  confidenceLabel: string;
  createdAtLabel: string;
}

export interface UseDocumentsResult {
  data: DocumentRow[];
  pendingReviewCount: number;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  upload: (file: File, forceReview?: boolean) => Promise<void>;
  review: (id: string, accept: boolean) => Promise<void>;
}

function toRow(document: DocumentModel): DocumentRow {
  return {
    id: document.id,
    filename: document.filename,
    status: document.status,
    confidenceLabel: document.confidence === null ? '—' : formatPercent(document.confidence),
    createdAtLabel: new Date(document.created_at).toLocaleDateString(),
  };
}

export function useDocuments(): UseDocumentsResult {
  const [data, setData] = useState<DocumentRow[]>([]);
  const [raw, setRaw] = useState<DocumentModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { trackJob } = useJobProgress();

  const reload = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const documents = await listDocuments();
      setRaw(documents);
      setData(documents.map(toRow));
    } catch {
      setError('load');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const upload = useCallback(
    async (file: File, forceReview = false): Promise<void> => {
      const result = await apiUploadDocument(file, { forceReview });
      if (!result.duplicate && result.job_id !== '') {
        trackJob(result.job_id, documentStrings.pageTitle);
      }
      await reload();
    },
    [reload, trackJob],
  );

  const review = useCallback(
    async (id: string, accept: boolean): Promise<void> => {
      await apiReviewDocument(id, accept);
      await reload();
    },
    [reload],
  );

  const pendingReviewCount = useMemo(
    () => raw.filter((document) => document.status === 'needs_review').length,
    [raw],
  );

  return { data, pendingReviewCount, loading, error, reload, upload, review };
}
