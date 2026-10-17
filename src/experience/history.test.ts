import { describe, expect, it } from 'vitest';

import { historyMode, urlForWorld, worldFromUrl } from './history';

describe('historyMode', () => {
  it('adds an entry when a world is opened from the system', () => {
    expect(historyMode(null, 'umbral', false)).toBe('push');
  });

  it('updates the current entry when switching between worlds', () => {
    expect(historyMode('umbral', 'finance', true)).toBe('replace');
  });

  it('goes back when the open world owns a pushed entry', () => {
    expect(historyMode('umbral', null, true)).toBe('back');
  });

  it('replaces the entry when the world came from a direct link', () => {
    expect(historyMode('umbral', null, false)).toBe('replace');
  });

  it('does nothing when the selection is unchanged', () => {
    expect(historyMode('umbral', 'umbral', true)).toBe('none');
    expect(historyMode(null, null, false)).toBe('none');
  });
});

describe('world urls', () => {
  const ids = ['umbral', 'finance'];

  it('reads only known worlds from the url', () => {
    expect(worldFromUrl('https://x.dev/?world=umbral', ids)).toBe('umbral');
    expect(worldFromUrl('https://x.dev/?world=nope', ids)).toBeNull();
    expect(worldFromUrl('https://x.dev/', ids)).toBeNull();
  });

  it('keeps unrelated parameters when writing the world', () => {
    expect(urlForWorld('https://x.dev/?stats=', 'umbral')).toBe(
      'https://x.dev/?stats=&world=umbral',
    );
    expect(urlForWorld('https://x.dev/?stats=&world=umbral', null)).toBe(
      'https://x.dev/?stats=',
    );
  });
});
