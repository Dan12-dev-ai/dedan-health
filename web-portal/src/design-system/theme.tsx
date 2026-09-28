/**
 * DEDAN-Health — Theme Provider
 *
 * Premium-bright healthcare intelligence theme built from `tokens.ts`.
 * Exposes:
 *  - `dedanTheme(mode)` — a MUI v5 theme (light | dark)
 *  - `DedanThemeProvider` — sets CSS custom properties on :root AND wraps MUI
 *  - `useDedanTheme()` — mode + toggle (persist to localStorage, reduced-motion aware)
 *  - `DEDAN_CSS_VARS` — the runtime CSS variable map (consumed by emotion/styled)
 */
import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  ReactNode,
} from 'react';
import {
  createTheme,
  ThemeProvider as MuiThemeProvider,
  CssBaseline,
  Theme,
} from '@mui/material';
import {
  palette,
  radius,
  radiusPx,
  shadows,
  typography,
  zIndex,
  breakpoints,
  containers,
  ThemeMode,
  colors,
} from './tokens';

/** Convert a rem string (e.g. "1.5rem") to a pixel number for MUI typography. */
const remToPx = (rem: string): number => parseFloat(rem) * 16;

export { type ThemeMode };

/** Map semantic tokens to CSS custom properties for runtime theme switching. */
export const DEDAN_CSS_VARS = {
  light: {
    '--dedan-color-background-default': palette.light.background.default,
    '--dedan-color-background-paper': palette.light.background.paper,
    '--dedan-color-text-primary': palette.light.text.primary,
    '--dedan-color-text-secondary': palette.light.text.secondary,
    '--dedan-color-border': palette.light.border.default,
    '--dedan-color-brand-primary': colors.brand.primary,
    '--dedan-color-critical': palette.light.state.emergency,
    '--dedan-color-warning': palette.light.state.warning,
    '--dedan-color-success': palette.light.state.success,
    '--dedan-color-info': palette.light.state.info,
  },
  dark: {
    '--dedan-color-background-default': palette.dark.background.default,
    '--dedan-color-background-paper': palette.dark.background.paper,
    '--dedan-color-text-primary': palette.dark.text.primary,
    '--dedan-color-text-secondary': palette.dark.text.secondary,
    '--dedan-color-border': palette.dark.border.default,
    '--dedan-color-brand-primary': colors.brand.primary,
    '--dedan-color-critical': palette.dark.state.emergency,
    '--dedan-color-warning': palette.dark.state.warning,
    '--dedan-color-success': palette.dark.state.success,
    '--dedan-color-info': palette.dark.state.info,
  },
} as const;

interface DedanThemeMode {
  mode: ThemeMode;
  userPreference: 'light' | 'dark' | 'system';
  reducedMotion: boolean;
  toggle: () => void;
  setMode: (m: 'light' | 'dark' | 'system') => void;
}

const ThemeContext = createContext<DedanThemeMode | undefined>(undefined);

export const useDedanTheme = (): DedanThemeMode => {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useDedanTheme must be used within DedanThemeProvider');
  }
  return ctx;
};

/** Reduced motion: respect OS-level `prefers-reduced-motion` */
function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

export function dedanTheme(mode: ThemeMode = 'light'): Theme {
  const p = mode === 'light' ? palette.light : palette.dark;
  const isDark = mode === 'dark';

  return createTheme({
    palette: {
      mode: isDark ? 'dark' : 'light',
      primary: {
        main: colors.brand.primary,
        contrastText: '#FFFFFF',
      },
      secondary: {
        main: '#2563EB', // intelligence blue (kept from original for consistency)
        contrastText: '#FFFFFF',
      },
      error: { main: colors.status.emergency, contrastText: '#FFFFFF' },
      warning: { main: colors.status.warning, contrastText: '#FFFFFF' },
      success: { main: colors.status.success, contrastText: '#FFFFFF' },
      info: { main: colors.status.info, contrastText: '#FFFFFF' },
      background: {
        default: p.background.default,
        paper: p.background.paper,
      },
      text: {
        primary: p.text.primary,
        secondary: p.text.secondary,
        disabled: p.text.disabled,
      },
      divider: p.border.default,
    },
    typography: {
      fontFamily: typography.fontFamily.base,
      // Headlines use the display face (Plus Jakarta Sans) for editorial
      // hierarchy; body copy stays on Inter for legibility at small sizes.
      h1: {
        fontFamily: typography.fontFamily.display,
        fontSize: remToPx(typography.fontSize['5xl']), // 3rem
        fontWeight: 800,
        lineHeight: typography.lineHeight.tight,
        letterSpacing: typography.letterSpacing.tighter,
      },
      h2: {
        fontFamily: typography.fontFamily.display,
        fontSize: remToPx(typography.fontSize['4xl']), // 2.25rem
        fontWeight: 700,
        lineHeight: typography.lineHeight.snug,
        letterSpacing: '-0.025em',
      },
      h3: {
        fontFamily: typography.fontFamily.display,
        fontSize: remToPx(typography.fontSize['3xl']), // 1.875rem
        fontWeight: 700,
        lineHeight: typography.lineHeight.snug,
      },
      h4: {
        fontFamily: typography.fontFamily.display,
        fontSize: remToPx(typography.fontSize['2xl']), // 1.5rem
        fontWeight: 700,
        lineHeight: typography.lineHeight.normal,
      },
      body1: {
        fontSize: remToPx(typography.fontSize.base), // 1rem
        lineHeight: typography.lineHeight.normal,
      },
      body2: {
        fontSize: remToPx(typography.fontSize.sm), // 0.875rem
        lineHeight: typography.lineHeight.snug,
      },
      button: {
        textTransform: 'none' as const,
        fontWeight: typography.fontWeight.medium,
        fontSize: remToPx(typography.fontSize.base),
      },
    },
    shape: {
      borderRadius: radiusPx.md,
    },
    components: {
      // Global button polish — no hover "lift" theatrics
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: radius.md,
            boxShadow: 'none',
            transition: 'background-color 140ms ease, border-color 140ms ease, color 140ms ease',
            '&:hover': { transform: 'none' },
          },
          contained: {
            background: `linear-gradient(135deg, ${colors.brand.primary} 0%, ${colors.brand.primaryHover} 100%)`,
            '&:hover': { background: `linear-gradient(135deg, ${colors.brand.primaryHover} 0%, ${colors.brand.primary} 100%)` },
          },
        },
      },
      MuiCssBaseline: {
        styleOverrides: `
          :root {
            ${Object.entries(DEDAN_CSS_VARS[mode])
              .map(([k, v]) => `${k}: ${v};`)
              .join(' ')}
            --dedan-radius-card: ${radius.lg};
            --dedan-shadow-sm: ${shadows.sm};
            --dedan-z-index-overlay: ${zIndex.modal};
            color-scheme: ${mode};
          }
          *, *::before, *::after { box-sizing: border-box; }

          html {
            scroll-behavior: smooth;
            -webkit-text-size-adjust: 100%;
          }
          body {
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
          }

          /* ---- Accessibility: visible, consistent focus (WCAG 2.2 AA) ---- */
          :focus-visible {
            outline: 2px solid ${colors.brand.primary};
            outline-offset: 2px;
            border-radius: ${radius.sm};
          }
          /* Never remove the focus ring; only soften it for mouse users. */
          :focus:not(:focus-visible) { outline: none; }

          ::selection {
            background-color: ${colors.brand.sage};
            color: #1F2937;
          }

          /* ---- Accessibility: respect prefers-reduced-motion ---- */
          @media (prefers-reduced-motion: reduce) {
            html { scroll-behavior: auto; }
            *, *::before, *::after {
              animation-duration: 0.01ms !important;
              animation-iteration-count: 1 !important;
              transition-duration: 0.01ms !important;
              scroll-behavior: auto !important;
            }
          }

          /* Skip-link target must not be hidden behind the sticky header. */
          [id] { scroll-margin-top: 96px; }
        `,
      },
    },
  });
}

interface Props {
  children: ReactNode;
}

/** Root provider. Reads persisted preference, respects reduced motion. */
export const DedanThemeProvider: React.FC<Props> = ({ children }) => {
  const STORAGE_KEY = 'dedan:theme';
  const getSystemMode = (): ThemeMode => {
    if (typeof window === 'undefined') return 'light';
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };
  const [userPreference, setUserPreference] = useState<'light' | 'dark' | 'system'>(
    (): 'light' | 'dark' | 'system' => {
      const saved = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null;
      if (saved === 'light' || saved === 'dark' || saved === 'system') return saved;
      // Master spec 3: "The final frontend MUST use a BRIGHT PREMIUM MODE.
      // The default experience should be bright." Dark mode remains available
      // via Settings, but the default is NEVER inherited from the OS.
      return 'light';
    }
  );
  const [reducedMotion] = useState<boolean>(prefersReducedMotion());

  useEffect(() => {
    const onMM = (e: MediaQueryListEvent) => {
      // reduced-motion can change at runtime
    };
    const mm = window.matchMedia('(prefers-reduced-motion: reduce)');
    mm.addEventListener?.('change', onMM);
    return () => mm.removeEventListener?.('change', onMM);
  }, []);

  const mode: ThemeMode = useMemo(() => {
    if (userPreference === 'system') return getSystemMode();
    return userPreference;
  }, [userPreference]);

  const toggle = () => {
    const next: 'light' | 'dark' | 'system' =
      userPreference === 'light' ? 'dark' : userPreference === 'dark' ? 'system' : 'light';
    localStorage.setItem(STORAGE_KEY, next);
    setUserPreference(next);
  };
  const setMode = (m: 'light' | 'dark' | 'system') => {
    localStorage.setItem(STORAGE_KEY, m);
    setUserPreference(m);
  };

  const theme = useMemo(() => dedanTheme(mode), [mode]);

  return (
    <ThemeContext.Provider value={{ mode, userPreference, reducedMotion, toggle, setMode }}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

export { type Theme };
