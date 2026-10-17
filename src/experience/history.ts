export type HistoryMode = 'none' | 'push' | 'replace' | 'back';

export const WORLD_PARAM = 'world';

export function historyMode(
  previous: string | null,
  next: string | null,
  entryWasPushed: boolean,
): HistoryMode {
  if (previous === next) return 'none';
  if (previous === null) return 'push';
  if (next === null) return entryWasPushed ? 'back' : 'replace';
  return 'replace';
}

export function worldFromUrl(href: string, validIds: readonly string[]) {
  const id = new URL(href).searchParams.get(WORLD_PARAM);
  return id !== null && validIds.includes(id) ? id : null;
}

export function urlForWorld(href: string, id: string | null) {
  const url = new URL(href);
  if (id) url.searchParams.set(WORLD_PARAM, id);
  else url.searchParams.delete(WORLD_PARAM);
  return url.href;
}
