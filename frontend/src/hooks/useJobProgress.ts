/** `useJobProgress` — thin context accessor that throws outside the provider. */
import { useContext } from 'react';

import {
  JobProgressContext,
  type JobProgressContextValue,
} from '@/contexts/job-progress-context';

export function useJobProgress(): JobProgressContextValue {
  const ctx = useContext(JobProgressContext);
  if (ctx === undefined) {
    throw new Error('useJobProgress must be used within a JobProgressProvider');
  }
  return ctx;
}
