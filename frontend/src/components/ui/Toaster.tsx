/** A tiny toaster for surfacing errors/notifications. */
import { useCallback, useMemo, useState, type ReactNode } from 'react';
import clsx from 'clsx';

import { ToasterContext, type ToasterContextValue } from '@/components/ui/toaster-context';

interface ToastState {
  message: string;
  variant: 'info' | 'error';
}

export function ToasterProvider({ children }: { children: ReactNode }): React.JSX.Element {
  const [toast, setToast] = useState<ToastState | null>(null);

  const notify = useCallback((message: string, variant: 'info' | 'error' = 'info') => {
    setToast({ message, variant });
    window.setTimeout(() => setToast(null), 4000);
  }, []);

  const value = useMemo<ToasterContextValue>(() => ({ notify }), [notify]);

  return (
    <ToasterContext.Provider value={value}>
      {children}
      {toast !== null && (
        <div
          role="alert"
          className={clsx('toast', toast.variant === 'error' && 'toast-error')}
        >
          {toast.message}
        </div>
      )}
    </ToasterContext.Provider>
  );
}
