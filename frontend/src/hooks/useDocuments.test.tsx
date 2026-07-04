import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { DocumentModel, UploadResponse } from '@/api/documents';
import { useDocuments } from '@/hooks/useDocuments';

const { trackJob } = vi.hoisted(() => ({ trackJob: vi.fn() }));

vi.mock('@/api/documents', () => ({
  listDocuments: vi.fn(),
  uploadDocument: vi.fn(),
  reviewDocument: vi.fn(),
}));

vi.mock('@/hooks/useJobProgress', () => ({
  useJobProgress: (): { jobs: []; activeCount: number; trackJob: typeof trackJob } => ({
    jobs: [],
    activeCount: 0,
    trackJob,
  }),
}));

import { listDocuments, reviewDocument, uploadDocument } from '@/api/documents';

const mockedList = vi.mocked(listDocuments);
const mockedUpload = vi.mocked(uploadDocument);
const mockedReview = vi.mocked(reviewDocument);

function doc(overrides: Partial<DocumentModel> = {}): DocumentModel {
  return {
    id: 'd-1',
    tenant_id: 't-1',
    filename: 'invoice.pdf',
    status: 'processing',
    confidence: null,
    extraction: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

function uploadResult(overrides: Partial<UploadResponse> = {}): UploadResponse {
  return { document: doc(), job_id: 'job-1', duplicate: false, ...overrides };
}

describe('useDocuments', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads rows and counts pending review', async () => {
    mockedList.mockResolvedValue([
      doc({ id: 'd-1', status: 'committed', confidence: 0.9 }),
      doc({ id: 'd-2', status: 'needs_review' }),
    ]);

    const { result } = renderHook(() => useDocuments());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toHaveLength(2);
    expect(result.current.pendingReviewCount).toBe(1);
    expect(result.current.data[0].confidenceLabel).toBe('90%');
  });

  it('tracks the job after a non-duplicate upload', async () => {
    mockedList.mockResolvedValue([]);
    mockedUpload.mockResolvedValue(uploadResult());

    const { result } = renderHook(() => useDocuments());
    await waitFor(() => expect(result.current.loading).toBe(false));

    const file = new File(['data'], 'invoice.pdf');
    await act(async () => {
      await result.current.upload(file);
    });

    expect(mockedUpload).toHaveBeenCalledWith(file, { forceReview: false });
    expect(trackJob).toHaveBeenCalledWith('job-1', 'Documents');
  });

  it('does not track a duplicate upload', async () => {
    mockedList.mockResolvedValue([]);
    mockedUpload.mockResolvedValue(uploadResult({ job_id: '', duplicate: true }));

    const { result } = renderHook(() => useDocuments());
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.upload(new File(['x'], 'dup.pdf'));
    });

    expect(trackJob).not.toHaveBeenCalled();
  });

  it('reloads after review', async () => {
    mockedList.mockResolvedValue([doc({ status: 'needs_review' })]);
    mockedReview.mockResolvedValue(doc({ status: 'committed' }));

    const { result } = renderHook(() => useDocuments());
    await waitFor(() => expect(result.current.loading).toBe(false));

    mockedList.mockResolvedValue([doc({ status: 'committed' })]);
    await act(async () => {
      await result.current.review('d-1', true);
    });

    expect(mockedReview).toHaveBeenCalledWith('d-1', true);
    expect(result.current.pendingReviewCount).toBe(0);
  });
});
