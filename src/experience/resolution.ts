export interface ResolutionOptions {
  min: number;
  max: number;
  step?: number;
}

export interface FrameSample {
  interval: number;
  cpu: number;
  throttled: boolean;
  now: number;
}

const WINDOW_MS = 1000;
const STALL_MS = 250;
const SLOW_WINDOWS = 3;
const BASE_RAISE_DELAY = 6000;
const MAX_RAISE_DELAY = 120000;
const RELAPSE_MS = 12000;

const median = (values: number[]) => {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.floor(sorted.length / 2)];
};

export function createResolutionGovernor(options: ResolutionOptions) {
  const step = options.step ?? 0.25;
  let ratio = options.max;
  let refresh = 1000 / 60;
  let intervals: number[] = [];
  let cpu: number[] = [];
  let windowTime = 0;
  let slowWindows = 0;
  let healthySince: number | null = null;
  let raiseDelay = BASE_RAISE_DELAY;
  let lastRaise = -Infinity;

  function closeWindow(now: number) {
    const frame = median(intervals);
    const work = median(cpu);
    intervals = [];
    cpu = [];
    windowTime = 0;
    refresh = Math.max(1000 / 144, Math.min(refresh, frame));

    const slow = frame > Math.max(refresh * 1.6, 24);
    const healthy = frame < Math.max(refresh * 1.25, 19);
    const cpuBound = work > frame * 0.6;

    if (slow && !cpuBound) {
      healthySince = null;
      slowWindows += 1;
      if (slowWindows < SLOW_WINDOWS || ratio <= options.min) return null;
      slowWindows = 0;
      if (now - lastRaise < RELAPSE_MS) {
        raiseDelay = Math.min(raiseDelay * 2, MAX_RAISE_DELAY);
      }
      ratio = Math.max(options.min, ratio - step);
      return ratio;
    }

    slowWindows = 0;
    if (!healthy) {
      healthySince = null;
      return null;
    }
    healthySince ??= now;
    if (ratio >= options.max || now - healthySince < raiseDelay) return null;
    healthySince = null;
    lastRaise = now;
    ratio = Math.min(options.max, ratio + step);
    return ratio;
  }

  return {
    get ratio() {
      return ratio;
    },
    sample({ interval, cpu: work, throttled, now }: FrameSample) {
      if (throttled || interval > STALL_MS) return null;
      intervals.push(interval);
      cpu.push(work);
      windowTime += interval;
      return windowTime >= WINDOW_MS ? closeWindow(now) : null;
    },
  };
}
