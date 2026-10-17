import { isStageId, stageIds, type StageId } from '@/data/career';
import { isWorldId, worldIds, type WorldId } from '@/data/worlds';

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
  stopTransitions,
  subscribe,
  watchMotionPreference,
} from './store';
import { resolveTimeline, sectionProgress } from './timeline';

const root = document.documentElement;
function one<T extends HTMLElement>(selector: string) {
  const element = document.querySelector<T>(selector);
  if (!element)
    throw new Error(`Universe: missing required element ${selector}`);
  return element;
}
const all = <T extends HTMLElement>(selector: string) => [
  ...document.querySelectorAll<T>(selector),
];
function byData<Id extends string>(
  attribute: string,
  isId: (value: string) => value is Id,
) {
  return new Map(
    all(`[data-${attribute}]`).map((element) => {
      const value = element.getAttribute(`data-${attribute}`)!;
      if (!isId(value))
        throw new Error(`Universe: unknown data-${attribute} "${value}"`);
      return [value, element] as const;
    }),
  );
}

const inspecting =
  import.meta.env.DEV || new URLSearchParams(location.search).has('stats');

export function mountExperience() {
  const controller = new AbortController();
  const { signal } = controller;
  const cleanup: Array<() => void> = [];

  const universeSection = one('#universe');
  const workSection = one('#work');
  const careerSection = one('#experience');
  const aboutSection = one('#about');
  const contactSection = one('#contact');
  const workDetail = one('.work-detail');
  const worldDetails = byData('world-detail', isWorldId);
  const worldMarkers = byData('world-marker', isWorldId);
  const worldStatus = one('[data-world-status]');
  const stepButtons = all('[data-step]');
  const stageStatus = one('[data-stage-status]');
  const stageDetails = byData('stage-detail', isStageId);
  const stageButtons = byData('stage-select', isStageId);
  const starMarkers = byData('star-marker', isStageId);
  const navLinks = all<HTMLAnchorElement>('[data-nav]');
  const scene = one<HTMLCanvasElement>('#scene');
  const returnButton = one('[data-return]');
  const frames = {
    hero: one('[data-frame="hero"]'),
    atlas: one('[data-frame="atlas"]'),
    focus: one('[data-frame="focus"]'),
    career: one('[data-frame="career"]'),
    about: one('[data-frame="about"]'),
    contact: one('[data-frame="contact"]'),
  };

  const scrollBehavior = (): ScrollBehavior =>
    state.motion.transitions ? 'smooth' : 'auto';

  function readScroll() {
    const viewport = window.innerHeight;
    const timeline = resolveTimeline(
      sectionProgress(workSection.getBoundingClientRect().top, viewport),
      sectionProgress(careerSection.getBoundingClientRect().top, viewport),
      sectionProgress(aboutSection.getBoundingClientRect().top, viewport),
      sectionProgress(contactSection.getBoundingClientRect().top, viewport),
    );
    setScroll(timeline.zone, timeline.weights);
    root.style.setProperty('--work', timeline.weights.work.toFixed(3));
    root.style.setProperty('--career', timeline.weights.career.toFixed(3));
    root.style.setProperty('--about', timeline.weights.about.toFixed(3));
    root.style.setProperty('--contact', timeline.weights.contact.toFixed(3));

    root.toggleAttribute(
      'data-outro',
      timeline.weights.about + timeline.weights.contact > 0.5,
    );
    navLinks.forEach((link) => {
      if (link.dataset.nav === timeline.zone)
        link.setAttribute('aria-current', 'location');
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
  window.addEventListener('scroll', scheduleScroll, { passive: true, signal });
  window.addEventListener('resize', scheduleScroll, { passive: true, signal });

  const worldHeading = (id: WorldId) =>
    worldDetails.get(id)?.querySelector<HTMLElement>('[data-world-heading]');

  const isShown = (element: HTMLElement | null | undefined) =>
    !!element?.isConnected && element.getClientRects().length > 0;

  function announceWorld(id: WorldId | null) {
    if (!id) {
      worldStatus.textContent = 'Full system. Select a world.';
      return;
    }
    const position = worldIds.indexOf(id) + 1;
    worldStatus.textContent = `${worldHeading(id)?.textContent?.trim()}. World ${position} of ${worldIds.length}.`;
  }

  let awaitingBack = false;

  function syncHistory(previous: WorldId | null, next: WorldId | null) {
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
    const stage = frames[frame].getBoundingClientRect();
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

  function showWorld(id: WorldId, options: WorldChange = {}) {
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

  byData('world-select', isWorldId).forEach((button, id) => {
    button.addEventListener('click', () => showWorld(id, { trigger: button }), {
      signal,
    });
    button.addEventListener('pointerenter', () => setHover(id), { signal });
    button.addEventListener('pointerleave', () => setHover(null), { signal });
    button.addEventListener('focus', () => setHover(id), { signal });
    button.addEventListener('blur', () => setHover(null), { signal });
  });

  worldMarkers.forEach((marker, id) => {
    marker.addEventListener('click', () => showWorld(id, { trigger: marker }), {
      signal,
    });
    marker.addEventListener('pointerenter', () => setHover(id), { signal });
    marker.addEventListener('pointerleave', () => setHover(null), { signal });
    marker.addEventListener('focus', () => setHover(id), { signal });
    marker.addEventListener('blur', () => setHover(null), { signal });
  });

  function stepWorld(direction: 1 | -1) {
    const next = adjacentWorld(direction);
    if (next) showWorld(next);
  }

  returnButton.addEventListener('click', () => hideWorld(), { signal });
  stepButtons.forEach((button) =>
    button.addEventListener(
      'click',
      () => stepWorld(button.dataset.step === '1' ? 1 : -1),
      { signal },
    ),
  );

  document.addEventListener(
    'keydown',
    (event) => {
      if (selectedWorld() === null || state.zone !== 'work') return;
      const target = event.target as HTMLElement;
      if (target !== document.body && !workSection.contains(target)) return;
      if (event.key === 'Escape') hideWorld();
      if (event.key === 'ArrowRight') stepWorld(1);
      if (event.key === 'ArrowLeft') stepWorld(-1);
    },
    { signal },
  );

  window.addEventListener(
    'popstate',
    () => {
      if (awaitingBack) {
        awaitingBack = false;
        const reopened = selectedWorld();
        if (reopened) syncHistory(null, reopened);
        return;
      }
      const id = worldFromUrl(window.location.href, worldIds);
      if (id) showWorld(id, { history: false });
      else hideWorld({ history: false });
    },
    { signal },
  );

  document.addEventListener(
    'click',
    (event) => {
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
    },
    { signal },
  );

  function openStage(id: StageId) {
    selectStage(id);
    const heading = stageDetails.get(id)?.querySelector('h3');
    const role = stageDetails.get(id)?.querySelector('[data-role]');
    stageStatus.textContent = `${heading?.textContent?.trim()}, ${role?.textContent?.trim()}. Stage ${stageIds.indexOf(id) + 1} of ${stageIds.length}.`;
    if (state.zone !== 'career')
      careerSection.scrollIntoView({ behavior: scrollBehavior() });
  }
  stageButtons.forEach((button, id) =>
    button.addEventListener('click', () => openStage(id), { signal }),
  );
  starMarkers.forEach((marker, id) =>
    marker.addEventListener('click', () => openStage(id), { signal }),
  );
  all('[data-stage-step]').forEach((button) =>
    button.addEventListener(
      'click',
      () => openStage(adjacentStage(button.dataset.stageStep === '1' ? 1 : -1)),
      { signal },
    ),
  );

  document.addEventListener(
    'keydown',
    (event) => {
      if (state.zone !== 'career') return;
      if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey)
        return;
      const target = event.target as HTMLElement;
      if (target !== document.body && !careerSection.contains(target)) return;
      if (event.key === 'ArrowRight') openStage(adjacentStage(1));
      if (event.key === 'ArrowLeft') openStage(adjacentStage(-1));
    },
    { signal },
  );

  let renderedWorld: WorldId | null = null;

  function render() {
    root.dataset.zone = state.zone;

    const selected = selectedWorld();
    if (selected !== renderedWorld && !state.motion.transitions) {
      scene.animate([{ opacity: 0 }, {}], {
        duration: 260,
        easing: 'ease-out',
      });
    }
    renderedWorld = selected;
    workSection.toggleAttribute('data-focus', selected !== null);
    worldDetails.forEach((detail, id) =>
      detail.toggleAttribute('data-active', id === selected),
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
  cleanup.push(subscribe(render));

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
        { once: true, signal },
      );
  } else if (new URL(window.location.href).searchParams.has(WORLD_PARAM)) {
    history.replaceState(null, '', urlForWorld(window.location.href, null));
  }

  function setSceneAvailable(available: boolean) {
    root.classList.toggle('no-webgl', !available);
    if (available) invalidate();
  }

  async function startUniverse() {
    try {
      const { createUniverse } = await import('./scene/universe');
      if (signal.aborted) return;
      const universe = await createUniverse(
        {
          canvas: scene,
          frames,
          protect: workDetail,
          worldMarkers,
          starMarkers,
          onAvailabilityChange(available) {
            if (!signal.aborted) setSceneAvailable(available);
          },
        },
        signal,
      );
      if (signal.aborted) {
        universe.dispose();
        return;
      }
      cleanup.push(() => {
        universe.dispose();
        scene.removeAttribute('data-ready');
      });
      scene.toggleAttribute('data-ready', true);
      invalidate();
      if (inspecting)
        Object.assign(window, { __universe: universe, __experience: state });
    } catch (error) {
      if (signal.aborted) return;
      setSceneAvailable(false);
      console.warn('Universe: the 3D scene could not start.', error);
    }
  }

  cleanup.push(watchMotionPreference(), stopTransitions, () => {
    delete root.dataset.experience;
  });
  root.dataset.experience = 'ready';
  startUniverse();

  return () => {
    controller.abort();
    cleanup.reverse().forEach((release) => release());
  };
}

let unmount = mountExperience();
import.meta.hot?.dispose(() => unmount());
if (inspecting)
  Object.assign(window, {
    __remount() {
      unmount();
      unmount = mountExperience();
    },
  });
