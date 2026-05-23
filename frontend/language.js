// language.js – utilities for language handling

/**
 * Get browser default language (2‑letter ISO code).
 * Falls back to 'en' if unavailable.
 */
export function getBrowserLanguage() {
  const lang = (navigator.language || navigator.userLanguage || 'en').toLowerCase();
  return lang.slice(0, 2);
}

/**
 * List of supported languages for the UI.
 * Extend as needed.
 */
export const SUPPORTED_LANGUAGES = [
  {code: 'en', label: 'English'},
  {code: 'hi', label: 'हिन्दी'},
  {code: 'es', label: 'Español'},
  {code: 'fr', label: 'Français'},
  {code: 'de', label: 'Deutsch'},
  {code: 'zh', label: '中文'},
];
