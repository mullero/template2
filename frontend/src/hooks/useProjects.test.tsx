import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Project } from '@/api/projects';
import { useProjects } from '@/hooks/useProjects';

vi.mock('@/api/projects', () => ({
  listProjects: vi.fn(),
  createProject: vi.fn(),
  deleteProject: vi.fn(),
}));

import { createProject, deleteProject, listProjects } from '@/api/projects';

const mockedList = vi.mocked(listProjects);
const mockedCreate = vi.mocked(createProject);
const mockedDelete = vi.mocked(deleteProject);

function project(overrides: Partial<Project> = {}): Project {
  return {
    id: 'p-1',
    tenant_id: 't-1',
    name: 'Alpha',
    description: null,
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

describe('useProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads rows and computes KPIs from loaded data', async () => {
    mockedList.mockResolvedValue([
      project({ id: 'p-1', status: 'active' }),
      project({ id: 'p-2', status: 'archived' }),
    ]);

    const { result } = renderHook(() => useProjects());

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toHaveLength(2);
    expect(result.current.kpis.total).toBe(2);
    expect(result.current.kpis.active).toBe(1);
  });

  it('reloads after create', async () => {
    mockedList.mockResolvedValue([]);
    mockedCreate.mockResolvedValue(project());

    const { result } = renderHook(() => useProjects());
    await waitFor(() => expect(result.current.loading).toBe(false));

    mockedList.mockResolvedValue([project()]);
    await act(async () => {
      await result.current.create({ name: 'Alpha' });
    });

    expect(mockedCreate).toHaveBeenCalledWith({ name: 'Alpha' });
    expect(result.current.data).toHaveLength(1);
  });

  it('surfaces load errors', async () => {
    mockedList.mockRejectedValue(new Error('boom'));

    const { result } = renderHook(() => useProjects());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('load');
  });

  it('reloads after delete', async () => {
    mockedList.mockResolvedValue([project()]);
    mockedDelete.mockResolvedValue();

    const { result } = renderHook(() => useProjects());
    await waitFor(() => expect(result.current.loading).toBe(false));

    mockedList.mockResolvedValue([]);
    await act(async () => {
      await result.current.remove('p-1');
    });
    expect(mockedDelete).toHaveBeenCalledWith('p-1');
    expect(result.current.data).toHaveLength(0);
  });
});
