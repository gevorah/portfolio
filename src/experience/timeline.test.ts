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
        for (let about = 0; about <= 1; about += 0.25) {
          for (let contact = 0; contact <= 1; contact += 0.25) {
            const { weights } = resolveTimeline(work, career, about, contact);
            expect(
              Object.values(weights).reduce((sum, value) => sum + value),
            ).toBeCloseTo(1);
          }
        }
      }
    }
  });

  it('resolves each milestone to a single zone', () => {
    expect(resolveTimeline(0, 0, 0, 0)).toMatchObject({
      zone: 'hero',
      weights: { hero: 1, work: 0, career: 0, about: 0, contact: 0 },
    });
    expect(resolveTimeline(1, 0, 0, 0)).toMatchObject({
      zone: 'work',
      weights: { hero: 0, work: 1, career: 0, about: 0, contact: 0 },
    });
    expect(resolveTimeline(1, 1, 0, 0)).toMatchObject({
      zone: 'career',
      weights: { hero: 0, work: 0, career: 1, about: 0, contact: 0 },
    });
    expect(resolveTimeline(1, 1, 1, 0)).toMatchObject({
      zone: 'about',
      weights: { hero: 0, work: 0, career: 0, about: 1, contact: 0 },
    });
    expect(resolveTimeline(1, 1, 1, 1)).toMatchObject({
      zone: 'contact',
      weights: { hero: 0, work: 0, career: 0, about: 0, contact: 1 },
    });
  });

  it('changes weights gradually in both scroll directions', () => {
    const steps = Array.from({ length: 81 }, (_, index) => index / 20);
    const clamp = (value: number) => Math.min(Math.max(value, 0), 1);
    const positions = steps.map((step) => [
      clamp(step),
      clamp(step - 1),
      clamp(step - 2),
      clamp(step - 3),
    ]);
    const resolve = ([work, career, about, contact]: number[]) =>
      resolveTimeline(work, career, about, contact);
    const forward = positions.map(resolve);
    const backward = [...positions].reverse().map(resolve).reverse();
    expect(backward).toEqual(forward);
    forward.slice(1).forEach((current, index) => {
      const previous = forward[index];
      expect(current.weights.hero).toBeLessThanOrEqual(previous.weights.hero);
      expect(current.weights.contact).toBeGreaterThanOrEqual(
        previous.weights.contact,
      );
      for (const zone of [
        'hero',
        'work',
        'career',
        'about',
        'contact',
      ] as const)
        expect(
          Math.abs(current.weights[zone] - previous.weights[zone]),
        ).toBeLessThanOrEqual(0.35);
    });
  });
});
