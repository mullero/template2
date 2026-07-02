/** Toaster context object, value type, and `useToaster` accessor hook.
 * Separated from the provider component to keep Toaster.tsx react-refresh clean. */
import { createContext, useContext } from 'react';

export interface ToasterContextValue {
  notify: (message: string, variant?: 'info' | 'error') => void;
}

export const ToasterContext = createContext<ToasterContextValue | undefined>(undefined);

export function useToaster(): ToasterContextValue {
  const ctx = useContext(ToasterContext);
  if (ctx === undefined) {
    throw new Error('useToaster must be used within a ToasterProvider');
  }
  return ctx;
}
