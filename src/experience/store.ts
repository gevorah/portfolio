import gsap from 'gsap';

import { defaultStageId } from '@/data/career';
import { worldIds } from '@/data/worlds';

import type { Zone, ZoneWeights } from './timeline';

export interface ExperienceState {
  zone: Zone;
  weights: ZoneWeights;
  outro: number;
  focusId: string | null;
  focused: boolean;
  focus: number;
  focusShift: number;
  recede: number;
  hoverId: string | null;
  stageId: string;
  reducedMotion: boolean;
}

type Listener = (state: ExperienceState) => void;

const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

export const state: ExperienceState = {
  zone: 'hero',
  weights: { hero: 1, work: 0, career: 0 },
  outro: 0,
  focusId: null,
  focused: false,
  focus: 0,
  focusShift: 0,
  recede: 0,
  hoverId: null,
  stageId: defaultStageId,
  reducedMotion: motionQuery.matches,
};

const listeners = new Set<Listener>();

export function subscribe(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

const notify = () => listeners.forEach((listener) => listener(state));

motionQuery.addEventListener('change', (event) => {
  state.reducedMotion = event.matches;
  notify();
});

const FOCUS_SCALARS = ['focus', 'focusShift', 'recede'] as const;

function animateFocus(target: 0 | 1) {
  gsap.killTweensOf(state, FOCUS_SCALARS.join(','));
  if (state.reducedMotion) {
    FOCUS_SCALARS.forEach((key) => (state[key] = target));
    if (target === 0) clearFocus();
    return;
  }
  if (target === 1) {
    gsap.to(state, { focus: 1, duration: 1.7, ease: 'power3.inOut' });
    gsap.to(state, {
      focusShift: 1,
      duration: 1.5,
      delay: 0.12,
      ease: 'power2.inOut',
    });
    gsap.to(state, { recede: 1, duration: 1.1, delay: 0.2, ease: 'sine.out' });
  } else {
    gsap.to(state, { recede: 0, duration: 1.2, ease: 'sine.inOut' });
    gsap.to(state, { focusShift: 0, duration: 1.3, ease: 'power2.inOut' });
    gsap.to(state, {
      focus: 0,
      duration: 1.45,
      ease: 'power3.inOut',
      onComplete: clearFocus,
    });
  }
}

function clearFocus() {
  if (state.focused) return;
  state.focusId = null;
  notify();
}

export function focusWorld(id: string) {
  if (!worldIds.includes(id)) return;
  if (state.focused && state.focusId === id) return;
  state.focusId = id;
  state.focused = true;
  animateFocus(1);
  notify();
}

export function returnToSystem() {
  if (!state.focused) return;
  state.focused = false;
  animateFocus(0);
  notify();
}

export function stepWorld(direction: 1 | -1) {
  const index = worldIds.indexOf(state.focusId ?? '');
  if (index < 0) return;
  focusWorld(worldIds[(index + direction + worldIds.length) % worldIds.length]);
}

export function setHover(id: string | null) {
  state.hoverId = id;
}

export function selectStage(id: string) {
  if (state.stageId === id) return;
  state.stageId = id;
  notify();
}

export function setScroll(zone: Zone, weights: ZoneWeights, outro: number) {
  state.weights = weights;
  state.outro = outro;
  if (zone === state.zone) return;
  state.zone = zone;
  notify();
}
