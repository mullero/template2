/** 404 page. */
import { Link } from 'react-router-dom';

import { commonStrings } from '@/constants/uiStrings';

export function NotFoundPage(): React.JSX.Element {
  return (
    <div className="app-main stack">
      <h1>{commonStrings.notFound}</h1>
      <Link to="/">{commonStrings.retry}</Link>
    </div>
  );
}
