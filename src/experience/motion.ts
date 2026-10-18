export interface MotionPolicy {
  ambient: boolean;
  transitions: boolean;
  parallax: boolean;
}

export const motionPolicy = (reducedMotion: boolean): MotionPolicy => ({
  ambient: !reducedMotion,
  transitions: !reducedMotion,
  parallax: !reducedMotion,
});

export const damping = (policy: MotionPolicy, rate: number, dt: number) =>
  policy.transitions ? 1 - Math.exp(-rate * dt) : 1;

export const settleWindow = (policy: MotionPolicy) =>
  policy.transitions ? 1500 : 120;
