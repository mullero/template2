/** A centered loading spinner. */
export function Spinner({ label }: { label?: string }): React.JSX.Element {
  return (
    <div className="row" style={{ justifyContent: 'center', padding: 'var(--space-5)' }}>
      <span className="spinner" aria-hidden="true" />
      {label !== undefined && <span className="text-muted">{label}</span>}
    </div>
  );
}
