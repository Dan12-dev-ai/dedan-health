/**
 * DEDAN-Health — Locale Manifest
 *
 * NOTE: The live backend localizes *clinical content* itself
 * (POST /dedan/v1/triage honors patient.language; GET /dedan/v1/conditions?language=).
 * This manifest governs UI *label* translation only.
 *
 * Status legend:
 *   live    — UI strings fully translated, shipped
 *   planned — locale structurally supported; UI strings fall back to en until translated
 */

export type LocaleStatus = 'live' | 'planned';

export interface LocaleMeta {
  code: string;
  label: string; // English label for the language switcher
  nativeLabel: string;
  direction: 'ltr' | 'rtl';
  status: LocaleStatus;
  /** Rough text-expansion factor vs English (0.9–1.1 = neutral). */
  expansionFactor: number;
}

export const locales: Record<string, LocaleMeta> = {
  en: { code: 'en', label: 'English', nativeLabel: 'English', direction: 'ltr', status: 'live', expansionFactor: 1.0 },
  sw: { code: 'sw', label: 'Swahili', nativeLabel: 'Kiswahili', direction: 'ltr', status: 'planned', expansionFactor: 1.1 },
  am: { code: 'am', label: 'Amharic', nativeLabel: 'አማርኛ', direction: 'ltr', status: 'planned', expansionFactor: 0.9 },
  es: { code: 'es', label: 'Spanish', nativeLabel: 'Español', direction: 'ltr', status: 'planned', expansionFactor: 1.1 },
  fr: { code: 'fr', label: 'French', nativeLabel: 'Français', direction: 'ltr', status: 'planned', expansionFactor: 1.05 },
};

export const supportedLocales = Object.keys(locales);
export const liveLocales = supportedLocales.filter((c) => locales[c].status === 'live');
export const defaultLocale: string = 'en';
