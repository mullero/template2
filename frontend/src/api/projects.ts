/** Project + auth API repository modules (typed request/response shapes). */
import { apiDelete, apiGet, apiPatch, apiPost } from '@/api/client';

export type ProjectStatus = 'active' | 'archived' | 'paused';

export interface Project {
  id: string;
  tenant_id: string;
  name: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectInput {
  name: string;
  description?: string | null;
  status?: string;
}

export interface UpdateProjectInput {
  name?: string;
  description?: string | null;
  status?: string;
}

export interface GraphTask {
  id: string;
  title: string;
}

export function listProjects(): Promise<Project[]> {
  return apiGet<Project[]>('/projects');
}

export function getProject(id: string): Promise<Project> {
  return apiGet<Project>(`/projects/${id}`);
}

export function createProject(input: CreateProjectInput): Promise<Project> {
  return apiPost<Project, CreateProjectInput>('/projects', input);
}

export function updateProject(id: string, input: UpdateProjectInput): Promise<Project> {
  return apiPatch<Project, UpdateProjectInput>(`/projects/${id}`, input);
}

export function deleteProject(id: string): Promise<void> {
  return apiDelete(`/projects/${id}`);
}

export function listProjectGraphTasks(id: string): Promise<GraphTask[]> {
  return apiGet<GraphTask[]>(`/projects/${id}/graph/tasks`);
}
