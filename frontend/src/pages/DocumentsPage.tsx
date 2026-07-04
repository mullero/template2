/** Documents page — the frontend end of the async AI-extraction slice. */
import { useRef, type ChangeEvent } from 'react';

import { Spinner } from '@/components/ui/Spinner';
import { useToaster } from '@/components/ui/toaster-context';
import { documentStrings } from '@/constants/uiStrings';
import { useDocuments } from '@/hooks/useDocuments';

export function DocumentsPage(): React.JSX.Element {
  const { data, pendingReviewCount, loading, error, upload, review } = useDocuments();
  const { notify } = useToaster();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onUpload = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      await upload(file);
    } catch {
      notify(documentStrings.uploadError, 'error');
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const onReview = async (id: string, accept: boolean): Promise<void> => {
    try {
      await review(id, accept);
    } catch {
      notify(documentStrings.uploadError, 'error');
    }
  };

  return (
    <div className="stack">
      <h1>{documentStrings.pageTitle}</h1>

      {pendingReviewCount > 0 && (
        <div className="banner" role="status">
          {documentStrings.reviewBanner(pendingReviewCount)}
        </div>
      )}

      <div className="row">
        <label className="btn btn-primary">
          {documentStrings.uploadButton}
          <input
            ref={fileInputRef}
            type="file"
            hidden
            onChange={(e) => void onUpload(e)}
            aria-label={documentStrings.uploadButton}
          />
        </label>
      </div>

      {loading ? (
        <Spinner />
      ) : error !== null ? (
        <p className="text-danger">{documentStrings.loadError}</p>
      ) : data.length === 0 ? (
        <p className="text-muted">{documentStrings.empty}</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>{documentStrings.columnName}</th>
              <th>{documentStrings.columnStatus}</th>
              <th>{documentStrings.columnConfidence}</th>
              <th>{documentStrings.columnCreated}</th>
              <th>{documentStrings.columnActions}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.id}>
                <td>{row.filename}</td>
                <td>{row.status}</td>
                <td>{row.confidenceLabel}</td>
                <td>{row.createdAtLabel}</td>
                <td>
                  {row.status === 'needs_review' && (
                    <div className="row">
                      <button
                        className="btn btn-primary"
                        type="button"
                        onClick={() => void onReview(row.id, true)}
                      >
                        {documentStrings.acceptButton}
                      </button>
                      <button
                        className="btn btn-danger"
                        type="button"
                        onClick={() => void onReview(row.id, false)}
                      >
                        {documentStrings.rejectButton}
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
