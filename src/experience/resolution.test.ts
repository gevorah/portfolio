import { describe, expect, it } from 'vitest';

import { createResolutionGovernor } from './resolution';

function run(
  governor: ReturnType<typeof createResolutionGovernor>,
  clock: { now: number },
  seconds: number,
  interval: number,
  { cpu = 1, throttled = false } = {},
) {
  const changes: number[] = [];
  const end = clock.now + seconds * 1000;
  while (clock.now < end) {
    clock.now += interval;
    const next = governor.sample({ interval, cpu, throttled, now: clock.now });
    if (next !== null) changes.push(next);
  }
  return changes;
}

describe('resolution governor', () => {
  it('ignores a deliberately throttled cadence', () => {
    const governor = createResolutionGovernor({ min: 1, max: 2 });
    const clock = { now: 0 };
    expect(run(governor, clock, 30, 50, { throttled: true })).toEqual([]);
    expect(governor.ratio).toBe(2);
  });

  it('ignores stalls such as a tab switch', () => {
    const governor = createResolutionGovernor({ min: 1, max: 2 });
    expect(run(governor, { now: 0 }, 20, 400)).toEqual([]);
  });

  it('lowers resolution after sustained slow rendering', () => {
    const governor = createResolutionGovernor({ min: 1, max: 2 });
    const clock = { now: 0 };
    run(governor, clock, 2, 16.7);
    expect(run(governor, clock, 4, 34)).toEqual([1.75]);
  });

  it('does not lower resolution when the frame is bound by script time', () => {
    const governor = createResolutionGovernor({ min: 1, max: 2 });
    const clock = { now: 0 };
    run(governor, clock, 2, 16.7);
    expect(run(governor, clock, 6, 34, { cpu: 28 })).toEqual([]);
  });

  it('recovers resolution once rendering is healthy again', () => {
    const governor = createResolutionGovernor({ min: 1, max: 2 });
    const clock = { now: 0 };
    run(governor, clock, 2, 16.7);
    run(governor, clock, 4, 34);
    expect(governor.ratio).toBe(1.75);
    expect(run(governor, clock, 10, 16.7)).toEqual([2]);
  });

  it('backs off instead of oscillating when a raise relapses', () => {
    const governor = createResolutionGovernor({ min: 1, max: 2 });
    const clock = { now: 0 };
    run(governor, clock, 2, 16.7);
    run(governor, clock, 4, 34);
    run(governor, clock, 10, 16.7);
    run(governor, clock, 4, 34);
    expect(governor.ratio).toBe(1.75);
    expect(run(governor, clock, 10, 16.7)).toEqual([]);
    expect(run(governor, clock, 6, 16.7)).toEqual([2]);
  });

  it('never leaves the configured range', () => {
    const governor = createResolutionGovernor({ min: 1, max: 1.5 });
    const clock = { now: 0 };
    run(governor, clock, 2, 16.7);
    run(governor, clock, 60, 40);
    expect(governor.ratio).toBe(1);
  });
});
