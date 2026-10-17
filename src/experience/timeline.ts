export type Zone = 'hero' | 'work' | 'career' | 'about' | 'contact';

export interface ZoneWeights {
  hero: number;
  work: number;
  career: number;
  about: number;
  contact: number;
}

export interface ScrollTimeline {
  weights: ZoneWeights;
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
  aboutProgress: number,
  contactProgress: number,
): ScrollTimeline {
  const toWork = smoothstep(workProgress);
  const toCareer = smoothstep(careerProgress);
  const toAbout = smoothstep(aboutProgress);
  const toContact = smoothstep(contactProgress);
  const weights = {
    hero: (1 - toWork) * (1 - toCareer) * (1 - toAbout) * (1 - toContact),
    work: toWork * (1 - toCareer) * (1 - toAbout) * (1 - toContact),
    career: toCareer * (1 - toAbout) * (1 - toContact),
    about: toAbout * (1 - toContact),
    contact: toContact,
  };
  const zone: Zone =
    contactProgress > 0.5
      ? 'contact'
      : aboutProgress > 0.5
        ? 'about'
        : careerProgress > 0.5
          ? 'career'
          : workProgress > 0.5
            ? 'work'
            : 'hero';
  return { weights, zone };
}
