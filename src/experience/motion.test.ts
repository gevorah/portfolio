import { describe, expect, it } from 'vitest';

import { damping, motionPolicy, settleWindow } from './motion';

describe('motionPolicy', () => {
  it('turns off every source of motion when reduced motion is requested', () => {
    expect(motionPolicy(true)).toEqual({
      ambient: false,
      transitions: false,
      parallax: false,
    });
  });

  it('resolves damped values instantly under reduced motion', () => {
    expect(damping(motionPolicy(true), 4, 1 / 60)).toBe(1);
    const eased = damping(motionPolicy(false), 4, 1 / 60);
    expect(eased).toBeGreaterThan(0);
    expect(eased).toBeLessThan(1);
  });

  it('needs only a short settle window when nothing eases', () => {
    expect(settleWindow(motionPolicy(true))).toBeLessThan(
      settleWindow(motionPolicy(false)),
    );
  });
});
