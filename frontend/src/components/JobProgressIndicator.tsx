/** Global background-job progress indicator (renders only while work is active). */
import { useJobProgress } from '@/hooks/useJobProgress';
import { jobStrings } from '@/constants/uiStrings';

export function JobProgressIndicator(): React.JSX.Element | null {
  const { activeCount } = useJobProgress();
  if (activeCount === 0) {
    return null;
  }
  return (
    <div className="job-progress" role="status" aria-live="polite">
      <span className="job-progress-spinner" aria-hidden="true" />
      {jobStrings.activeJobs(activeCount)}
    </div>
  );
}
