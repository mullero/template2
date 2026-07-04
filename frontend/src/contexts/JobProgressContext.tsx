/**
 * Global background-job progress provider.
 *
 * Mounted ABOVE the router so tracked jobs SURVIVE navigation: pages start work
 * and call {@link trackJob}; this provider owns the polling loop and drives the
 * global progress indicator. Polling runs only while at least one tracked job is
 * non-terminal.
 */
import { type ReactNode, useCallback, useEffect, useRef, useState } from 'react';

import { getJob } from '@/api/jobs';
import {
  JobProgressContext,
  type JobProgressContextValue,
  TERMINAL_STATUSES,
  type TrackedJob,
} from '@/contexts/job-progress-context';

const POLL_INTERVAL_MS = 1500;

function isActive(job: TrackedJob): boolean {
  return !TERMINAL_STATUSES.includes(job.status);
}

export function JobProgressProvider({ children }: { children: ReactNode }): React.JSX.Element {
  const [jobs, setJobs] = useState<TrackedJob[]>([]);
  const jobsRef = useRef<TrackedJob[]>([]);
  jobsRef.current = jobs;

  const trackJob = useCallback((jobId: string, label: string): void => {
    setJobs((current) => {
      if (current.some((job) => job.id === jobId)) {
        return current;
      }
      return [...current, { id: jobId, label, status: 'queued' }];
    });
  }, []);

  const activeCount = jobs.filter(isActive).length;

  useEffect(() => {
    if (activeCount === 0) {
      return;
    }
    let cancelled = false;

    const poll = async (): Promise<void> => {
      const active = jobsRef.current.filter(isActive);
      const results = await Promise.all(
        active.map(async (job) => {
          try {
            const fresh = await getJob(job.id);
            return { id: job.id, status: fresh.status };
          } catch {
            return null;
          }
        }),
      );
      if (cancelled) {
        return;
      }
      setJobs((current) =>
        current.map((job) => {
          const update = results.find((result) => result?.id === job.id);
          return update ? { ...job, status: update.status } : job;
        }),
      );
    };

    const timer = window.setInterval(() => void poll(), POLL_INTERVAL_MS);
    return (): void => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [activeCount]);

  const value: JobProgressContextValue = { jobs, activeCount, trackJob };
  return <JobProgressContext.Provider value={value}>{children}</JobProgressContext.Provider>;
}
