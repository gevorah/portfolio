import { describe, expect, it } from 'vitest';

import { resolveLabels, type LabelItem } from './labels';

const item = (overrides: Partial<LabelItem> & { id: string }): LabelItem => ({
  x: 400,
  y: 300,
  bodyRadius: 30,
  labelRadius: 30,
  halfWidth: 50,
  height: 18,
  priority: 1,
  prefer: 'below',
  ...overrides,
});

describe('resolveLabels', () => {
  it('keeps the preferred side when nothing is in the way', () => {
    const result = resolveLabels([item({ id: 'a' })], 1440);
    expect(result.get('a')).toEqual({ placement: 'below', nudge: 0 });
  });

  it('moves a label to the other side when it would cover another label', () => {
    const result = resolveLabels(
      [
        item({ id: 'a', priority: 2 }),
        item({ id: 'b', x: 430, bodyRadius: 4, labelRadius: 30 }),
      ],
      1440,
    );
    expect(result.get('a')?.placement).toBe('below');
    expect(result.get('b')?.placement).toBe('above');
  });

  it('never places a label over another body', () => {
    const result = resolveLabels(
      [
        item({ id: 'a', priority: 2 }),
        item({
          id: 'planet',
          y: 360,
          bodyRadius: 40,
          priority: 0,
          halfWidth: 1,
        }),
      ],
      1440,
    );
    expect(result.get('a')?.placement).toBe('above');
  });

  it('hides a label when both sides are blocked', () => {
    const result = resolveLabels(
      [
        item({ id: 'a', priority: 3, halfWidth: 60 }),
        item({ id: 'b', priority: 2, prefer: 'above', halfWidth: 60 }),
        item({ id: 'c', priority: 1, x: 410, bodyRadius: 2 }),
      ],
      1440,
    );
    expect(result.get('c')?.placement).toBe('hidden');
  });

  it('keeps labels off the areas it is asked to avoid', () => {
    const text = { left: 300, right: 500, top: 330, bottom: 420 };
    const flipped = resolveLabels([item({ id: 'a' })], 1440, undefined, [text]);
    expect(flipped.get('a')?.placement).toBe('above');
    const covered = resolveLabels([item({ id: 'a' })], 1440, undefined, [
      { ...text, top: 200 },
    ]);
    expect(covered.get('a')?.placement).toBe('hidden');
  });

  it('nudges a label back inside the viewport', () => {
    const result = resolveLabels([item({ id: 'a', x: 20 })], 390);
    expect(result.get('a')?.nudge).toBe(40);
  });

  it('prefers the previous side to avoid flicker', () => {
    const result = resolveLabels(
      [item({ id: 'a' })],
      1440,
      new Map([['a', 'above']]),
    );
    expect(result.get('a')?.placement).toBe('above');
  });
});
