import { describe, expect, it } from 'vitest';

import { resolveTimeline, sectionProgress } from './timeline';

describe('sectionProgress', () => {
  it('starts when the section enters from the bottom and ends at the top', () => {
    expect(sectionProgress(800, 800)).toBe(0);
    expect(sectionProgress(400, 800)).toBe(0.5);
    expect(sectionProgress(0, 800)).toBe(1);
    expect(sectionProgress(-300, 800)).toBe(1);
    expect(sectionProgress(2000, 800)).toBe(0);
  });
});

describe('resolveTimeline', () => {
  it('keeps the zone weights normalized at every scroll position', () => {
    for (let work = 0; work <= 1; work += 0.1) {
      for (let career = 0; career <= 1; career += 0.1) {
        const { weights } = resolveTimeline(work, career, 0);
        expect(weights.hero + weights.work + weights.career).toBeCloseTo(1);
      }
    }
  });

  it('resolves each milestone to a single zone', () => {
    expect(resolveTimeline(0, 0, 0)).toMatchObject({
      zone: 'hero',
      weights: { hero: 1, work: 0, career: 0 },
    });
    expect(resolveTimeline(1, 0, 0)).toMatchObject({
      zone: 'work',
      weights: { hero: 0, work: 1, career: 0 },
    });
    expect(resolveTimeline(1, 1, 0)).toMatchObject({
      zone: 'career',
      weights: { hero: 0, work: 0, career: 1 },
    });
  });

  it('is reversible: the same scroll position always gives the same result', () => {
    expect(resolveTimeline(0.3, 0, 0)).toEqual(resolveTimeline(0.3, 0, 0));
  });
});
