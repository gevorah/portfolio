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

  it('changes weights gradually in both scroll directions', () => {
    const steps = Array.from({ length: 41 }, (_, index) => index / 20);
    const positions = steps.map((step) => [
      Math.min(step, 1),
      Math.max(step - 1, 0),
    ]);
    const forward = positions.map(([work, career]) =>
      resolveTimeline(work, career, 0),
    );
    const backward = [...positions]
      .reverse()
      .map(([work, career]) => resolveTimeline(work, career, 0))
      .reverse();
    expect(backward).toEqual(forward);
    forward.slice(1).forEach((current, index) => {
      const previous = forward[index];
      expect(current.weights.hero).toBeLessThanOrEqual(previous.weights.hero);
      expect(current.weights.career).toBeGreaterThanOrEqual(
        previous.weights.career,
      );
      for (const zone of ['hero', 'work', 'career'] as const)
        expect(
          Math.abs(current.weights[zone] - previous.weights[zone]),
        ).toBeLessThanOrEqual(0.35);
    });
  });
});
