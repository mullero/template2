/** Job-progress context object + value type, separated from the provider. */
import { createContext } from 'react';

import type { JobStatus } from '@/api/jobs';

export interface TrackedJob {
  id: string;
  label: string;
  status: JobStatus;
}

export interface JobProgressContextValue {
  jobs: TrackedJob[];
  activeCount: number;
  /** Begin polling a background job's status until it reaches a terminal state. */
  trackJob: (jobId: string, label: string) => void;
}

export const JobProgressContext = createContext<JobProgressContextValue | undefined>(undefined);

export const TERMINAL_STATUSES: readonly JobStatus[] = ['succeeded', 'failed'];
