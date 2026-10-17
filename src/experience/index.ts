import { stageIds } from '@/data/career';
import { worldIds } from '@/data/worlds';

import { historyMode, urlForWorld, WORLD_PARAM, worldFromUrl } from './history';
import {
  adjacentStage,
  adjacentWorld,
  focusWorld,
  invalidate,
  returnToSystem,
  selectedWorld,
  selectStage,
  setHover,
  setScroll,
  state,
  subscribe,
} from './store';
import { resolveTimeline, sectionProgress } from './timeline';

const root = document.documentElement;
const one = <T extends HTMLElement>(selector: string) =>
  document.querySelector<T>(selector)!;
const all = <T extends HTMLElement>(selector: string) => [
  ...document.querySelectorAll<T>(selector),
];
const byData = (attribute: string) =>
  new Map(
    all(`[data-${attribute}]`).map((element) => [
      element.getAttribute(`data-${attribute}`)!,
      element,
    ]),
  );

const universeSection = one('#universe');
const workSection = one('#work');
const careerSection = one('#experience');
const outroSection = one('.outro');
const workDetail = one('.work-detail');
const worldDetails = byData('world-detail');
const worldMarkers = byData('world-marker');
const worldStatus = one('[data-world-status]');
const stepButtons = all('[data-step]');
const stageStatus = one('[data-stage-status]');
const stageDetails = byData('stage-detail');
const stageButtons = byData('stage-select');
const starMarkers = byData('star-marker');
const navLinks = all<HTMLAnchorElement>('[data-nav]');

const scrollBehavior = (): ScrollBehavior =>
  state.motion.transitions ? 'smooth' : 'auto';

function readScroll() {
  const viewport = window.innerHeight;
  const timeline = resolveTimeline(
    sectionProgress(workSection.getBoundingClientRect().top, viewport),
    sectionProgress(careerSection.getBoundingClientRect().top, viewport),
    sectionProgress(outroSection.getBoundingClientRect().top, viewport),
  );
  setScroll(timeline.zone, timeline.weights, timeline.outro);
  root.style.setProperty('--hero', timeline.weights.hero.toFixed(3));
  root.style.setProperty('--work', timeline.weights.work.toFixed(3));
  root.style.setProperty('--career', timeline.weights.career.toFixed(3));
  root.style.setProperty('--outro', timeline.outro.toFixed(3));

  root.toggleAttribute('data-outro', timeline.outro > 0.5);
  const current = timeline.outro > 0.5 ? 'outro' : timeline.zone;
  navLinks.forEach((link) => {
    if (link.dataset.nav === current) link.setAttribute('aria-current', 'true');
    else link.removeAttribute('aria-current');
  });
}

let scrollScheduled = false;
function scheduleScroll() {
  if (scrollScheduled) return;
  scrollScheduled = true;
  requestAnimationFrame(() => {
    scrollScheduled = false;
    readScroll();
  });
}
window.addEventListener('scroll', scheduleScroll, { passive: true });
window.addEventListener('resize', scheduleScroll, { passive: true });

const worldHeading = (id: string) =>
  worldDetails.get(id)?.querySelector<HTMLElement>('[data-world-heading]');

const isShown = (element: HTMLElement | null | undefined) =>
  !!element?.isConnected && element.getClientRects().length > 0;

function announceWorld(id: string | null) {
  if (!id) {
    worldStatus.textContent = 'Full system. Select a world.';
    return;
  }
  const position = worldIds.indexOf(id) + 1;
  worldStatus.textContent = `${worldHeading(id)?.textContent?.trim()}. World ${position} of ${worldIds.length}.`;
}

let awaitingBack = false;

function syncHistory(previous: string | null, next: string | null) {
  if (awaitingBack) return;
  const pushed = history.state?.pushed === true;
  const mode = historyMode(previous, next, pushed);
  const url = urlForWorld(window.location.href, next);
  if (mode === 'push') {
    history.scrollRestoration = 'manual';
    history.pushState({ world: next, pushed: true }, '', url);
  } else if (mode === 'replace') {
    history.replaceState(
      { world: next, pushed: pushed && next !== null },
      '',
      url,
    );
  } else if (mode === 'back') {
    awaitingBack = true;
    history.back();
  }
}

function keepStageInView(frame: 'focus' | 'atlas') {
  const stage = one(`[data-frame="${frame}"]`).getBoundingClientRect();
  const hidden =
    stage.top < -stage.height * 0.25 || stage.top > window.innerHeight * 0.75;
  if (state.zone !== 'work' || hidden)
    workSection.scrollIntoView({ behavior: scrollBehavior() });
}

let worldTrigger: HTMLElement | null = null;

interface WorldChange {
  trigger?: HTMLElement;
  history?: boolean;
  focus?: boolean;
}

function showWorld(id: string, options: WorldChange = {}) {
  const previous = selectedWorld();
  if (!worldDetails.has(id)) return;
  if (previous === id) {
    keepStageInView('focus');
    return;
  }

  const active = document.activeElement as HTMLElement | null;
  const keepsFocus = previous !== null && stepButtons.includes(active!);
  if (previous === null) worldTrigger = options.trigger ?? null;

  worldDetails
    .get(id)
    ?.style.setProperty(
      '--reveal-delay',
      previous === null && state.motion.transitions ? '0.75s' : '0s',
    );
  focusWorld(id);
  if (options.history !== false) syncHistory(previous, id);
  keepStageInView('focus');

  if (options.focus === false) return;
  if (keepsFocus) announceWorld(id);
  else worldHeading(id)?.focus({ preventScroll: true });
}

function hideWorld(options: WorldChange = {}) {
  const previous = selectedWorld();
  if (previous === null) return;
  returnToSystem();
  if (options.history !== false) syncHistory(previous, null);
  announceWorld(null);

  if (options.focus === false) return;
  const fallback = worldMarkers.get(previous);
  const target = [worldTrigger, fallback, workSection].find(isShown);
  target?.focus({ preventScroll: true });
  keepStageInView('atlas');
}

all('[data-world-select]').forEach((button) => {
  const id = button.dataset.worldSelect!;
  button.addEventListener('click', () => showWorld(id, { trigger: button }));
  button.addEventListener('pointerenter', () => setHover(id));
  button.addEventListener('pointerleave', () => setHover(null));
  button.addEventListener('focus', () => setHover(id));
  button.addEventListener('blur', () => setHover(null));
});

worldMarkers.forEach((marker, id) => {
  marker.addEventListener('click', () => showWorld(id, { trigger: marker }));
  marker.addEventListener('pointerenter', () => setHover(id));
  marker.addEventListener('pointerleave', () => setHover(null));
  marker.addEventListener('focus', () => setHover(id));
  marker.addEventListener('blur', () => setHover(null));
});

function stepWorld(direction: 1 | -1) {
  const next = adjacentWorld(direction);
  if (next) showWorld(next);
}

one('[data-return]').addEventListener('click', () => hideWorld());
stepButtons.forEach((button) =>
  button.addEventListener('click', () =>
    stepWorld(button.dataset.step === '1' ? 1 : -1),
  ),
);

document.addEventListener('keydown', (event) => {
  if (selectedWorld() === null || state.zone !== 'work') return;
  const target = event.target as HTMLElement;
  if (target !== document.body && !workSection.contains(target)) return;
  if (event.key === 'Escape') hideWorld();
  if (event.key === 'ArrowRight') stepWorld(1);
  if (event.key === 'ArrowLeft') stepWorld(-1);
});

window.addEventListener('popstate', () => {
  if (awaitingBack) {
    awaitingBack = false;
    const reopened = selectedWorld();
    if (reopened) syncHistory(null, reopened);
    return;
  }
  const id = worldFromUrl(window.location.href, worldIds);
  if (id) showWorld(id, { history: false });
  else hideWorld({ history: false });
});

document.addEventListener('click', (event) => {
  if (event.defaultPrevented || event.metaKey || event.ctrlKey) return;
  const link = (event.target as Element).closest<HTMLAnchorElement>(
    'a[href^="#"]',
  );
  const target = link && document.getElementById(link.hash.slice(1));
  if (!target) return;
  event.preventDefault();
  if (target === workSection || target === universeSection)
    hideWorld({ focus: false });
  target.scrollIntoView({ behavior: scrollBehavior() });
  target.focus({ preventScroll: true });
});

function openStage(id: string) {
  selectStage(id);
  const heading = stageDetails.get(id)?.querySelector('h3');
  const role = stageDetails.get(id)?.querySelector('[data-role]');
  stageStatus.textContent = `${heading?.textContent?.trim()}, ${role?.textContent?.trim()}. Stage ${stageIds.indexOf(id) + 1} of ${stageIds.length}.`;
  if (state.zone !== 'career')
    careerSection.scrollIntoView({ behavior: scrollBehavior() });
}
stageButtons.forEach((button, id) =>
  button.addEventListener('click', () => openStage(id)),
);
starMarkers.forEach((marker, id) =>
  marker.addEventListener('click', () => openStage(id)),
);
all('[data-stage-step]').forEach((button) =>
  button.addEventListener('click', () =>
    openStage(adjacentStage(button.dataset.stageStep === '1' ? 1 : -1)),
  ),
);

document.addEventListener('keydown', (event) => {
  if (state.zone !== 'career') return;
  if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
  const target = event.target as HTMLElement;
  if (target !== document.body && !careerSection.contains(target)) return;
  if (event.key === 'ArrowRight') openStage(adjacentStage(1));
  if (event.key === 'ArrowLeft') openStage(adjacentStage(-1));
});

let renderedWorld: string | null = null;

function render() {
  root.dataset.zone = state.zone;

  const selected = selectedWorld();
  if (selected !== renderedWorld && !state.motion.transitions) {
    one('#scene').animate([{ opacity: 0 }, {}], {
      duration: 260,
      easing: 'ease-out',
    });
  }
  renderedWorld = selected;
  workSection.toggleAttribute('data-focus', selected !== null);
  worldDetails.forEach((detail, id) =>
    detail.toggleAttribute('data-active', id === selected),
  );
  worldMarkers.forEach((marker, id) =>
    marker.toggleAttribute('data-current', id === selected),
  );

  stageDetails.forEach((detail, id) =>
    detail.toggleAttribute('data-active', id === state.stageId),
  );
  [stageButtons, starMarkers].forEach((controls) =>
    controls.forEach((control, id) =>
      control.setAttribute('aria-pressed', String(id === state.stageId)),
    ),
  );
}
subscribe(render);

readScroll();
render();

const linkedWorld = worldFromUrl(window.location.href, worldIds);
if (linkedWorld) {
  const openLinkedWorld = () => {
    workSection.scrollIntoView({ behavior: 'instant' });
    readScroll();
    showWorld(linkedWorld, { history: false, focus: false });
    history.replaceState({ world: linkedWorld, pushed: false }, '');
  };
  if (document.readyState === 'complete') openLinkedWorld();
  else
    window.addEventListener(
      'load',
      () => requestAnimationFrame(openLinkedWorld),
      { once: true },
    );
} else if (new URL(window.location.href).searchParams.has(WORLD_PARAM)) {
  history.replaceState(null, '', urlForWorld(window.location.href, null));
}

async function startUniverse() {
  const canvas = one<HTMLCanvasElement>('#scene');
  try {
    const { createUniverse } = await import('./scene/universe');
    const universe = await createUniverse({
      canvas,
      frames: {
        hero: one('[data-frame="hero"]'),
        atlas: one('[data-frame="atlas"]'),
        focus: one('[data-frame="focus"]'),
        career: one('[data-frame="career"]'),
      },
      protect: workDetail,
      worldMarkers,
      starMarkers,
    });
    canvas.toggleAttribute('data-ready', true);
    invalidate();
    if (
      import.meta.env.DEV ||
      new URLSearchParams(location.search).has('stats')
    ) {
      Object.assign(window, { __universe: universe, __experience: state });
    }
    import.meta.hot?.dispose(() => universe.dispose());
  } catch (error) {
    root.classList.add('no-webgl');
    console.warn('Universe: the 3D scene could not start.', error);
  }
}
startUniverse();
