import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { Project } from '@/api/projects';
import { ToasterProvider } from '@/components/ui/Toaster';
import { projectStrings } from '@/constants/uiStrings';
import { ProjectsPage } from '@/pages/ProjectsPage';
import { renderWithProviders } from '@/test/utils';

vi.mock('@/api/projects', () => ({
  listProjects: vi.fn(),
  createProject: vi.fn(),
  deleteProject: vi.fn(),
}));

import { createProject, listProjects } from '@/api/projects';

const mockedList = vi.mocked(listProjects);
const mockedCreate = vi.mocked(createProject);

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

function renderPage(): void {
  renderWithProviders(
    <ToasterProvider>
      <ProjectsPage />
    </ToasterProvider>,
  );
}

describe('ProjectsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the empty state', async () => {
    mockedList.mockResolvedValue([]);
    renderPage();
    expect(await screen.findByText(projectStrings.empty)).toBeInTheDocument();
  });

  it('renders projects and KPIs', async () => {
    mockedList.mockResolvedValue([project({ name: 'Alpha' })]);
    renderPage();
    expect(await screen.findByText('Alpha')).toBeInTheDocument();
  });

  it('creates a project on submit', async () => {
    mockedList.mockResolvedValue([]);
    mockedCreate.mockResolvedValue(project());
    renderPage();

    await screen.findByText(projectStrings.empty);
    const input = screen.getByLabelText(projectStrings.nameLabel);
    await userEvent.type(input, 'Alpha');
    await userEvent.click(screen.getByRole('button', { name: projectStrings.createButton }));

    await waitFor(() => expect(mockedCreate).toHaveBeenCalledWith({ name: 'Alpha' }));
  });
});
