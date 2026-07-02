/** Auth API repository: sync current user + bootstrap. */
import { apiGet, apiPost } from '@/api/client';

export type UserRole = 'viewer' | 'admin' | 'superadmin';

export interface BackendUser {
  uid: string;
  email: string | null;
  role: UserRole;
  tenant_id: string | null;
}

export function fetchCurrentUser(): Promise<BackendUser> {
  return apiGet<BackendUser>('/auth/me');
}

export function bootstrapWorkspace(tenantId: string): Promise<BackendUser> {
  return apiPost<BackendUser, { tenant_id: string }>('/auth/bootstrap', {
    tenant_id: tenantId,
  });
}
