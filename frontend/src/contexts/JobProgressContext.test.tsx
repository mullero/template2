import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Job } from '@/api/jobs';
import { JobProgressProvider } from '@/contexts/JobProgressContext';
import { useJobProgress } from '@/hooks/useJobProgress';

vi.mock('@/api/jobs', () => ({ getJob: vi.fn() }));

import { getJob } from '@/api/jobs';

const mockedGetJob = vi.mocked(getJob);

function job(status: Job['status']): Job {
  return {
    id: 'job-1',
    tenant_id: 't-1',
    kind: 'extract_document',
    status,
    attempts: 1,
    error: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

function Consumer(): React.JSX.Element {
  const { activeCount, trackJob, jobs } = useJobProgress();
  return (
    <div>
      <span data-testid="active">{activeCount}</span>
      <span data-testid="status">{jobs[0]?.status ?? 'none'}</span>
      <button type="button" onClick={() => trackJob('job-1', 'Docs')}>
        track
      </button>
    </div>
  );
}

describe('JobProgressProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('tracks a job and polls until it reaches a terminal state', async () => {
    mockedGetJob.mockResolvedValue(job('succeeded'));
    const user = userEvent.setup();

    render(
      <JobProgressProvider>
        <Consumer />
      </JobProgressProvider>,
    );

    expect(screen.getByTestId('active').textContent).toBe('0');

    await user.click(screen.getByRole('button', { name: 'track' }));
    expect(screen.getByTestId('active').textContent).toBe('1');
    expect(screen.getByTestId('status').textContent).toBe('queued');

    // Poller (real timers) transitions the job to a terminal state.
    await vi.waitFor(
      () => {
        expect(screen.getByTestId('status').textContent).toBe('succeeded');
        expect(screen.getByTestId('active').textContent).toBe('0');
      },
      { timeout: 4000 },
    );
    expect(mockedGetJob).toHaveBeenCalledWith('job-1');
  });
});
