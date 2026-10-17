import {
  focusWorld,
  returnToSystem,
  selectStage,
  setHover,
  setScroll,
  state,
  stepWorld,
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

const workSection = one('#trabajo');
const careerSection = one('#trayectoria');
const outroSection = one('#sobre-mi');
const worldDetails = byData('world-detail');
const worldMarkers = byData('world-marker');
const stageDetails = byData('stage-detail');
const stageButtons = byData('stage-select');
const starMarkers = byData('star-marker');
const navLinks = all<HTMLAnchorElement>('[data-nav]');

const WORLD_PARAM = 'mundo';

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

  if (state.focused && timeline.weights.work > 0.6) visitedFocus = true;
  if (state.focused && visitedFocus && timeline.weights.work < 0.3)
    returnToSystem();

  const current = timeline.outro > 0.5 ? 'outro' : timeline.zone;
  navLinks.forEach((link) =>
    link.setAttribute('aria-current', String(link.dataset.nav === current)),
  );
}

let visitedFocus = false;
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

const scrollBehavior = (): ScrollBehavior =>
  state.reducedMotion ? 'auto' : 'smooth';

function openWorld(id: string, { moveFocus = false } = {}) {
  const arriving = !state.focused;
  if (arriving) visitedFocus = state.weights.work > 0.6;
  focusWorld(id);
  const stageTop = one('[data-frame="focus"]').getBoundingClientRect().top;
  if (state.zone !== 'work' || stageTop < 0)
    workSection.scrollIntoView({ behavior: scrollBehavior() });
  const detail = worldDetails.get(id);
  detail?.style.setProperty(
    '--reveal-delay',
    arriving && !state.reducedMotion ? '0.75s' : '0s',
  );
  if (moveFocus) detail?.focus({ preventScroll: true });
}

let lastWorldTrigger: HTMLElement | null = null;

all('[data-world-select]').forEach((button) => {
  const id = button.dataset.worldSelect!;
  button.addEventListener('click', () => {
    lastWorldTrigger = button;
    openWorld(id, { moveFocus: true });
  });
  button.addEventListener('pointerenter', () => setHover(id));
  button.addEventListener('pointerleave', () => setHover(null));
  button.addEventListener('focus', () => setHover(id));
  button.addEventListener('blur', () => setHover(null));
});

worldMarkers.forEach((marker, id) => {
  marker.addEventListener('click', () => openWorld(id));
  marker.addEventListener('pointerenter', () => setHover(id));
  marker.addEventListener('pointerleave', () => setHover(null));
});

function leaveWorld() {
  returnToSystem();
  lastWorldTrigger?.focus({ preventScroll: true });
  const stage = one('[data-frame="atlas"]').getBoundingClientRect();
  if (stage.top < -stage.height * 0.25)
    workSection.scrollIntoView({ behavior: scrollBehavior() });
}

one('[data-return]').addEventListener('click', leaveWorld);
all('[data-step]').forEach((button) =>
  button.addEventListener('click', () => {
    stepWorld(button.dataset.step === '1' ? 1 : -1);
    worldDetails
      .get(state.focusId ?? '')
      ?.style.setProperty('--reveal-delay', '0s');
  }),
);

document.addEventListener('keydown', (event) => {
  if (!state.focused || state.zone !== 'work') return;
  if (event.key === 'Escape') {
    leaveWorld();
    return;
  }
  const target = event.target as HTMLElement;
  if (target.closest('input, textarea, select, [contenteditable]')) return;
  if (event.key === 'ArrowRight') stepWorld(1);
  if (event.key === 'ArrowLeft') stepWorld(-1);
});

function openStage(id: string) {
  selectStage(id);
  if (state.zone !== 'career')
    careerSection.scrollIntoView({ behavior: scrollBehavior() });
}
stageButtons.forEach((button, id) =>
  button.addEventListener('click', () => openStage(id)),
);
starMarkers.forEach((marker, id) =>
  marker.addEventListener('click', () => openStage(id)),
);

let renderedWorld: string | null = null;

function render() {
  root.dataset.zone = state.zone;

  const selected = state.focused ? state.focusId : null;
  if (selected !== renderedWorld && state.reducedMotion) {
    one('#universe').animate([{ opacity: 0 }, {}], {
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

  const url = new URL(window.location.href);
  if (selected) url.searchParams.set(WORLD_PARAM, selected);
  else url.searchParams.delete(WORLD_PARAM);
  if (url.href !== window.location.href) history.replaceState(null, '', url);
}
subscribe(render);

const linkedWorld = new URL(window.location.href).searchParams.get(WORLD_PARAM);

readScroll();
render();

if (linkedWorld && worldDetails.has(linkedWorld)) {
  const openLinkedWorld = () => {
    workSection.scrollIntoView({ behavior: 'instant' });
    readScroll();
    openWorld(linkedWorld);
  };
  if (document.readyState === 'complete') openLinkedWorld();
  else
    window.addEventListener(
      'load',
      () => requestAnimationFrame(openLinkedWorld),
      { once: true },
    );
}

async function startUniverse() {
  const canvas = one<HTMLCanvasElement>('#universe');
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
      worldMarkers,
      starMarkers,
    });
    canvas.toggleAttribute('data-ready', true);
    if (
      import.meta.env.DEV ||
      new URLSearchParams(location.search).has('stats')
    ) {
      Object.assign(window, { __universe: universe, __experience: state });
    }
    import.meta.hot?.dispose(() => universe.dispose());
  } catch (error) {
    root.classList.add('no-webgl');
    console.warn('Small Worlds: no se pudo iniciar la escena 3D.', error);
  }
}
startUniverse();
