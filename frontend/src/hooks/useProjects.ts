/**
 * Projects data hook. Maps raw API shapes to view-model rows and exposes
 * { data, loading, error, actions }. Filter-dependent KPIs are aggregated in the
 * frontend from already-loaded rows (see kpi-placement memory).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  createProject as apiCreateProject,
  deleteProject as apiDeleteProject,
  listProjects,
  type CreateProjectInput,
  type Project,
} from '@/api/projects';

export interface ProjectRow {
  id: string;
  name: string;
  description: string | null;
  status: string;
  createdAtLabel: string;
}

export interface ProjectKpis {
  total: number;
  active: number;
}

export interface UseProjectsResult {
  data: ProjectRow[];
  kpis: ProjectKpis;
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
  create: (input: CreateProjectInput) => Promise<void>;
  remove: (id: string) => Promise<void>;
}

function toRow(project: Project): ProjectRow {
  return {
    id: project.id,
    name: project.name,
    description: project.description,
    status: project.status,
    createdAtLabel: new Date(project.created_at).toLocaleDateString(),
  };
}

export function useProjects(): UseProjectsResult {
  const [data, setData] = useState<ProjectRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const projects = await listProjects();
      setData(projects.map(toRow));
    } catch {
      setError('load');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const create = useCallback(
    async (input: CreateProjectInput): Promise<void> => {
      await apiCreateProject(input);
      await reload();
    },
    [reload],
  );

  const remove = useCallback(
    async (id: string): Promise<void> => {
      await apiDeleteProject(id);
      await reload();
    },
    [reload],
  );

  const kpis = useMemo<ProjectKpis>(
    () => ({
      total: data.length,
      active: data.filter((row) => row.status === 'active').length,
    }),
    [data],
  );

  return { data, kpis, loading, error, reload, create, remove };
}
