import { ThemeProvider as ContextProvider } from '../lib/theme';

export function ThemeProvider({ children }) {
  return <ContextProvider>{children}</ContextProvider>;
}
