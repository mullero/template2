/** Projects page — the frontend end of the vertical slice. */
import { useState, type FormEvent } from 'react';

import { Spinner } from '@/components/ui/Spinner';
import { useToaster } from '@/components/ui/toaster-context';
import { projectStrings } from '@/constants/uiStrings';
import { useProjects } from '@/hooks/useProjects';

export function ProjectsPage(): React.JSX.Element {
  const { data, kpis, loading, error, create, remove } = useProjects();
  const { notify } = useToaster();
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const onCreate = async (event: FormEvent): Promise<void> => {
    event.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      await create({ name: name.trim() });
      setName('');
    } catch {
      notify(projectStrings.createError, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const onDelete = async (id: string): Promise<void> => {
    try {
      await remove(id);
    } catch {
      notify(projectStrings.deleteError, 'error');
    }
  };

  return (
    <div className="stack">
      <h1>{projectStrings.pageTitle}</h1>

      <div className="row">
        <div className="card">
          <div className="text-muted">{projectStrings.totalKpi}</div>
          <strong>{kpis.total}</strong>
        </div>
        <div className="card">
          <div className="text-muted">{projectStrings.activeKpi}</div>
          <strong>{kpis.active}</strong>
        </div>
      </div>

      <form className="row" onSubmit={(e) => void onCreate(e)}>
        <input
          className="input"
          placeholder={projectStrings.nameLabel}
          value={name}
          onChange={(e) => setName(e.target.value)}
          aria-label={projectStrings.nameLabel}
        />
        <button className="btn btn-primary" type="submit" disabled={submitting}>
          {submitting ? projectStrings.creating : projectStrings.createButton}
        </button>
      </form>

      {loading ? (
        <Spinner />
      ) : error !== null ? (
        <p className="text-danger">{projectStrings.loadError}</p>
      ) : data.length === 0 ? (
        <p className="text-muted">{projectStrings.empty}</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>{projectStrings.columnName}</th>
              <th>{projectStrings.columnStatus}</th>
              <th>{projectStrings.columnCreated}</th>
              <th>{projectStrings.columnActions}</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.id}>
                <td>{row.name}</td>
                <td>{row.status}</td>
                <td>{row.createdAtLabel}</td>
                <td>
                  <button
                    className="btn btn-danger"
                    type="button"
                    onClick={() => void onDelete(row.id)}
                  >
                    {projectStrings.deleteButton}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
