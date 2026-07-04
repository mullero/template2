/** Jobs API repository module (typed request/response shapes). */
import { apiGet } from '@/api/client';

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed';

export interface Job {
  id: string;
  tenant_id: string;
  kind: string;
  status: JobStatus;
  attempts: number;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export function getJob(id: string): Promise<Job> {
  return apiGet<Job>(`/jobs/${id}`);
}
