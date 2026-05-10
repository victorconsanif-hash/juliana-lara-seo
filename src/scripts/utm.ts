/**
 * UTM Capture — captura parâmetros de atribuição da URL na primeira visita
 * e persiste em cookie por 30 dias. Sobrevive a navegação entre páginas.
 *
 * Uso:
 *   import { captureUtms, getUtms } from '@/scripts/utm';
 *   captureUtms();          // chamar uma vez por página (Layout.astro)
 *   const data = getUtms(); // retorna objeto com utm_source, gclid, etc
 */

const COOKIE_NAME = 'juli_utm';
const COOKIE_DAYS = 30;

const UTM_KEYS = [
  'utm_source',
  'utm_medium',
  'utm_campaign',
  'utm_term',
  'utm_content',
  'gclid',
  'fbclid',
] as const;

export type UtmData = {
  utm_source: string | null;
  utm_medium: string | null;
  utm_campaign: string | null;
  utm_term: string | null;
  utm_content: string | null;
  gclid: string | null;
  fbclid: string | null;
  page_url: string | null;
  first_seen_at: string | null;
};

function readCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

function writeCookie(name: string, value: string, days: number) {
  if (typeof document === 'undefined') return;
  const expires = new Date(Date.now() + days * 86400000).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function emptyUtms(): UtmData {
  return {
    utm_source: null,
    utm_medium: null,
    utm_campaign: null,
    utm_term: null,
    utm_content: null,
    gclid: null,
    fbclid: null,
    page_url: null,
    first_seen_at: null,
  };
}

/**
 * Captura UTMs/click IDs da URL atual.
 * Se já existe cookie, mantém os valores antigos (first-touch attribution).
 */
export function captureUtms(): void {
  if (typeof window === 'undefined') return;

  const existing = readCookie(COOKIE_NAME);
  if (existing) {
    try {
      JSON.parse(existing);
      return; // já capturou antes — não sobrescreve
    } catch {
      // cookie corrompido — recapturar
    }
  }

  const params = new URLSearchParams(window.location.search);
  const data: UtmData = emptyUtms();
  let hasAnyParam = false;

  for (const key of UTM_KEYS) {
    const value = params.get(key);
    if (value) {
      data[key] = value;
      hasAnyParam = true;
    }
  }

  // Sempre registra a página/timestamp, mesmo sem UTM (tráfego direto/orgânico)
  data.page_url = window.location.href;
  data.first_seen_at = new Date().toISOString();

  // Só persiste se tiver pelo menos algum sinal de origem
  // OU se for primeira visita ao site (sem cookie ainda)
  if (hasAnyParam || !existing) {
    writeCookie(COOKIE_NAME, JSON.stringify(data), COOKIE_DAYS);
  }
}

/**
 * Lê UTMs do cookie. Retorna objeto vazio se não houver.
 */
export function getUtms(): UtmData {
  const raw = readCookie(COOKIE_NAME);
  if (!raw) return emptyUtms();
  try {
    return { ...emptyUtms(), ...JSON.parse(raw) };
  } catch {
    return emptyUtms();
  }
}
