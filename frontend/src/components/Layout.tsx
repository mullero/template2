/** App shell with header (product name, theme toggle, sign out). */
import { type ReactNode } from 'react';

import { appStrings, navStrings } from '@/constants/uiStrings';
import { useAuth } from '@/hooks/useAuth';
import { useTheme } from '@/hooks/useTheme';

export function Layout({ children }: { children: ReactNode }): React.JSX.Element {
  const { toggleTheme } = useTheme();
  const { signOut, backendUser } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <strong>{appStrings.productName}</strong>
        <div className="row">
          {backendUser?.email !== undefined && backendUser?.email !== null && (
            <span className="text-muted">{backendUser.email}</span>
          )}
          <button type="button" className="btn" onClick={toggleTheme}>
            {navStrings.toggleTheme}
          </button>
          <button type="button" className="btn" onClick={() => void signOut()}>
            {navStrings.signOut}
          </button>
        </div>
      </header>
      <main className="app-main">{children}</main>
    </div>
  );
}
