import { ThemeProvider as ContextProvider } from '../lib/theme.jsx';

export function ThemeProvider({ children }) {
  return <ContextProvider>{children}</ContextProvider>;
}
