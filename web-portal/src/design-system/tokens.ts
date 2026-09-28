/**
 * DEDAN-Health — Design Tokens
 *
 * Centralized design tokens for the premium bright healthcare interface.
 * All values are derived from this file and used in theme.ts and components.
 */

/**
 * Primitive status colors. Single source of truth — do not hard-code these
 * hex values anywhere else in the app.
 */
const STATUS = {
  emergency: '#DC2626', // red
  warning: '#B45309', // amber
  success: '#15803D', // green
  info: '#2563EB', // blue
} as const;

/** Foreground that is legible on each status background (WCAG AA). */
const ON_STATUS = '#FFFFFF';

/**
 * Color palette — Semantic colors for status and brand.
 *
 * `status.*` is the FLAT token set (used by the MUI theme).
 * `critical|warning|info|success` are `{ base, contrast }` pairs used by
 * severity UI (e.g. SeverityBadge) so foreground/background always travel
 * together and contrast is never decided ad-hoc at the call site.
 */
export const colors = {
  // Brand and accents
  brand: {
    primary: '#2E7D32', // healthcare green
    primaryHover: '#1B5E20', // darker green for hover/active
    secondary: '#2563EB', // intelligence blue
    sage: '#DCE8DC', // soft sage surface tint
  },
  // Status colors (semantic, flat)
  status: STATUS,
  // Severity pairs (base + safe contrast foreground)
  critical: { base: STATUS.emergency, contrast: ON_STATUS },
  warning: { base: STATUS.warning, contrast: ON_STATUS },
  info: { base: STATUS.info, contrast: ON_STATUS },
  success: { base: STATUS.success, contrast: ON_STATUS },
} as const;

/**
 * Spacing system (8px grid)
 */
export const spacing = {
  0: '0px',
  1: '4px',
  2: '8px',
  3: '12px',
  4: '16px',
  5: '20px',
  6: '24px',
  7: '28px',
  8: '32px',
  9: '36px',
  10: '40px',
  11: '44px',
  12: '48px',
  14: '56px',
  16: '64px',
  20: '80px',
  24: '96px',
  28: '112px',
  32: '128px',
};

/**
 * Border radius
 */
export const radius = {
  none: '0px',
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  '2xl': '24px',
  pill: '9999px',
  round: '50%',
};

/**
 * Numeric radius scale (px).
 *
 * MUI's `theme.shape.borderRadius` is typed as a `number`, so the string
 * `radius` tokens above cannot be used there. These stay in sync with `radius`.
 */
export const radiusPx = {
  none: 0,
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  '2xl': 24,
  pill: 9999,
} as const;

/**
 * Typography settings
 */
export const typography = {
  fontFamily: {
    base: '"Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif',
    display: '"Plus Jakarta Sans", "Inter", sans-serif', // for headlines
  },
  fontWeight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  fontSize: {
    xs: '0.75rem', // 12px
    sm: '0.875rem', // 14px
    base: '1rem', // 16px
    lg: '1.125rem', // 18px
    xl: '1.25rem', // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
    '5xl': '3rem', // 48px
    '6xl': '3.75rem', // 60px
  },
  lineHeight: {
    tight: 1.25,
    snug: 1.375,
    normal: 1.5,
    relaxed: 1.625,
    loose: 2,
  },
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0em',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },
};

/**
 * Shadow values
 */
export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
};

/**
 * Z-index layers
 */
export const zIndex = {
  // Below almost everything
  mobileStepper: 1000,
  // The fixed drawer
  speedDial: 1050,
  // The app bar
  appBar: 1100,
  // The modal backdrop
  backdrop: 1200,
  // The modal
  modal: 1300,
  // The popover
  popover: 1400,
  // The snackbar
  snackbar: 1500,
  // The tooltip
  tooltip: 1600,
};

/**
 * Motion (duration and easing)
 */
export const motion = {
  duration: {
    shortest: 150,
    shorter: 200,
    short: 250,
    standard: 300,
    complex: 375,
    entering: 225,
    leaving: 195,
  },
  easing: {
    standard: 'cubic-bezier(0.2, 0, 0, 1)',
    deceleration: 'cubic-bezier(0.0, 0, 0.2, 1)',
    acceleration: 'cubic-bezier(0.4, 0, 0.2, 1)',
    sharp: 'cubic-bezier(0.4, 0, 0.6, 1)',
  },
};

/**
 * Container widths
 */
export const containers = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1440px',
};

/**
 * Breakpoints (matching MUI)
 */
export const breakpoints = {
  xs: 0,
  sm: 600,
  md: 900,
  mdl: 1024,
  lg: 1200,
  xl: 1536,
};

/**
 * Palette for light and dark modes
 * The light mode is the bright premium mode.
 */
export const palette = {
  light: {
    background: {
      default: '#F8FAF7', // warm white
      paper: '#FFFFFF',
      elevated: '#FFFFFF',
    },
    text: {
      primary: '#2E3D2F', // deep green (almost black, but with green tint)
      secondary: '#4A554B', // muted green-gray
      disabled: '#9CA3AF',
    },
    border: {
      default: '#E5E7EB',
    },
    state: {
      emergency: colors.status.emergency,
      warning: colors.status.warning,
      success: colors.status.success,
      info: colors.status.info,
    },
  },
  dark: {
    background: {
      default: '#0B1120', // dark blue-gray
      paper: '#111827',
      elevated: '#1F2937',
    },
    text: {
      primary: '#F9FAFB', // near white
      secondary: '#D1D5DB', // gray-200
      disabled: '#6B7280', // gray-400
    },
    border: {
      default: '#374151', // gray-700
    },
    state: {
      emergency: colors.status.emergency,
      warning: colors.status.warning,
      success: colors.status.success,
      info: colors.status.info,
    },
  },
};

/**
 * ThemeMode type
 */
export type ThemeMode = 'light' | 'dark';
