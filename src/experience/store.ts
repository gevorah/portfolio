import gsap from 'gsap';

import { defaultStageId, stageIds } from '@/data/career';
import { worldIds } from '@/data/worlds';

import { motionPolicy, type MotionPolicy } from './motion';
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
  motion: MotionPolicy;
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
  motion: motionPolicy(motionQuery.matches),
};

const listeners = new Set<Listener>();
const renderRequests = new Set<() => void>();

export function subscribe(listener: Listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function onInvalidate(request: () => void) {
  renderRequests.add(request);
  return () => renderRequests.delete(request);
}

export const invalidate = () => renderRequests.forEach((request) => request());

function notify() {
  listeners.forEach((listener) => listener(state));
  invalidate();
}

const FOCUS_SCALARS = ['focus', 'focusShift', 'recede'] as const;

function settleFocus(target: 0 | 1) {
  gsap.killTweensOf(state, FOCUS_SCALARS.join(','));
  FOCUS_SCALARS.forEach((key) => (state[key] = target));
  if (target === 0) clearFocus();
}

function animateFocus(target: 0 | 1) {
  if (!state.motion.transitions) {
    settleFocus(target);
    return;
  }
  gsap.killTweensOf(state, FOCUS_SCALARS.join(','));
  const onUpdate = invalidate;
  if (target === 1) {
    gsap.to(state, { focus: 1, duration: 1.7, ease: 'power3.inOut', onUpdate });
    gsap.to(state, {
      focusShift: 1,
      duration: 1.5,
      delay: 0.12,
      ease: 'power2.inOut',
      onUpdate,
    });
    gsap.to(state, {
      recede: 1,
      duration: 1.1,
      delay: 0.2,
      ease: 'sine.out',
      onUpdate,
    });
  } else {
    gsap.to(state, { recede: 0, duration: 1.2, ease: 'sine.inOut', onUpdate });
    gsap.to(state, {
      focusShift: 0,
      duration: 1.3,
      ease: 'power2.inOut',
      onUpdate,
    });
    gsap.to(state, {
      focus: 0,
      duration: 1.45,
      ease: 'power3.inOut',
      onUpdate,
      onComplete: clearFocus,
    });
  }
}

function clearFocus() {
  if (state.focused) return;
  state.focusId = null;
  notify();
}

motionQuery.addEventListener('change', (event) => {
  state.motion = motionPolicy(event.matches);
  if (!state.motion.transitions) settleFocus(state.focused ? 1 : 0);
  notify();
});

export const selectedWorld = () => (state.focused ? state.focusId : null);

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

export function adjacentWorld(direction: 1 | -1) {
  const index = worldIds.indexOf(state.focusId ?? '');
  if (index < 0) return null;
  return worldIds[(index + direction + worldIds.length) % worldIds.length];
}

export function setHover(id: string | null) {
  if (state.hoverId === id) return;
  state.hoverId = id;
  invalidate();
}

export function adjacentStage(direction: 1 | -1) {
  const index = stageIds.indexOf(state.stageId) + direction;
  return stageIds[(index + stageIds.length) % stageIds.length];
}

export function selectStage(id: string) {
  if (state.stageId === id || !stageIds.includes(id)) return;
  state.stageId = id;
  notify();
}

export function setScroll(zone: Zone, weights: ZoneWeights, outro: number) {
  state.weights = weights;
  state.outro = outro;
  if (zone !== state.zone) {
    state.zone = zone;
    notify();
  } else {
    invalidate();
  }
}
