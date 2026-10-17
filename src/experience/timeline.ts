export type Zone = 'hero' | 'work' | 'career';

export interface ZoneWeights {
  hero: number;
  work: number;
  career: number;
}

export interface ScrollTimeline {
  weights: ZoneWeights;
  outro: number;
  zone: Zone;
}

export const clamp01 = (value: number) => Math.min(1, Math.max(0, value));

export const smoothstep = (value: number) => {
  const t = clamp01(value);
  return t * t * (3 - 2 * t);
};

export const sectionProgress = (sectionTop: number, viewportHeight: number) =>
  clamp01(1 - sectionTop / viewportHeight);

export function resolveTimeline(
  workProgress: number,
  careerProgress: number,
  outroProgress: number,
): ScrollTimeline {
  const toWork = smoothstep(workProgress);
  const toCareer = smoothstep(careerProgress);
  const weights = {
    hero: (1 - toWork) * (1 - toCareer),
    work: toWork * (1 - toCareer),
    career: toCareer,
  };
  const zone: Zone =
    careerProgress > 0.5 ? 'career' : workProgress > 0.5 ? 'work' : 'hero';
  return { weights, outro: smoothstep(outroProgress), zone };
}
