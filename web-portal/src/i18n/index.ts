import React from 'react';

/**
 * DEDAN-Health — i18n runtime (structural, not cosmetic).
 *
 * Only `en` is live-translated. Other locales are declared in localeManifest
 * but fall back to English labels until translations ship — NEVER fake content.
 */

import { locales, defaultLocale, type LocaleMeta } from './localeManifest';
import { en, type Messages, type MessageKey } from './locales/en';

const catalogs: Record<string, Messages> = { en };

export { locales, defaultLocale, type LocaleMeta, type Messages, type MessageKey };

export function getLocaleMeta(code: string): LocaleMeta {
  return locales[code] ?? locales[defaultLocale];
}

/**
 * Resolve a dotted key like "nav.home" or "results.emergency" from the catalog.
 * Falls back to the key itself if missing so missing strings are obvious.
 */
export function t(key: string, locale: string = defaultLocale, params?: Record<string, string | number>): string {
  const cat = catalogs[locale] ?? catalogs[defaultLocale];
  const parts = key.split('.');
  let node: any = cat;
  for (const p of parts) {
    if (node && Object.prototype.hasOwnProperty.call(node, p)) {
      node = node[p];
    } else {
      return withParams(key, params);
    }
  }
  if (typeof node !== 'string') return withParams(key, params);
  return withParams(node, params);
}

function withParams(template: string, params?: Record<string, string | number>): string {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (_, k) => String(params[k] ?? `{${k}}`));
}

type Listener = (locale: string) => void;
const listeners = new Set<Listener>();
let currentLocale: string =
  (typeof localStorage !== 'undefined' && localStorage.getItem('dedan:locale')) || defaultLocale;

export function getLocale(): string {
  return currentLocale;
}

export function setLocale(locale: string): void {
  if (!locales[locale]) return;
  currentLocale = locale;
  if (typeof localStorage !== 'undefined') localStorage.setItem('dedan:locale', locale);
  // Apply dir to document
  const dir = locales[locale]?.direction ?? 'ltr';
  if (typeof document !== 'undefined') document.documentElement.dir = dir;
  listeners.forEach((l) => l(currentLocale));
}

export function useTranslations() {
  const [locale, setLocaleState] = React.useState<string>(currentLocale);
  React.useEffect(() => {
    listeners.add(setLocaleState);
    return () => { listeners.delete(setLocaleState); };
  }, []);
    const tr: Messages = catalogs[locale] ?? catalogs[defaultLocale] ?? (en as unknown as Messages);
  return { t: (key: string, params?: Record<string, string | number>) => t(key, locale, params), locale, setLocale, tr };
}
