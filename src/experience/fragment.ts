const SETTLE_MS = 500;

const INTERRUPTIONS = [
  'wheel',
  'touchstart',
  'pointerdown',
  'keydown',
  'hashchange',
  'popstate',
] as const;

function fragmentTarget() {
  try {
    const id = decodeURIComponent(window.location.hash.slice(1));
    return id ? document.getElementById(id) : null;
  } catch {
    return null;
  }
}

function isFreshNavigation() {
  const [entry] = performance.getEntriesByType(
    'navigation',
  ) as PerformanceNavigationTiming[];
  return entry?.type === 'navigate';
}

const scrollsSmoothly = () =>
  getComputedStyle(document.documentElement).scrollBehavior === 'smooth';

const whenLoaded = (signal: AbortSignal) =>
  document.readyState === 'complete'
    ? Promise.resolve()
    : new Promise<void>((resolve) =>
        window.addEventListener('load', () => resolve(), {
          once: true,
          signal,
        }),
      );

export function keepFragmentInView(signal: AbortSignal) {
  const target = fragmentTarget();
  if (!target || !isFreshNavigation() || scrollsSmoothly()) return;

  const page = document.documentElement;
  const watch = new AbortController();
  const stop = () => watch.abort();
  const listen = { passive: true, signal: watch.signal };
  signal.addEventListener('abort', stop, { once: true, signal: watch.signal });
  INTERRUPTIONS.forEach((type) => window.addEventListener(type, stop, listen));

  const offset = () => target.getBoundingClientRect().top + window.scrollY;
  let placed = offset();
  const drift = () => {
    const margin = parseFloat(getComputedStyle(target).scrollMarginTop) || 0;
    const limit = page.scrollHeight - window.innerHeight;
    return Math.max(0, Math.min(offset() - margin, limit)) - window.scrollY;
  };
  const align = () => {
    const distance = drift();
    const moved = Math.abs(offset() - placed) >= 1;
    if (Math.abs(distance) >= 1) {
      if (!moved && window.scrollY > 0) return stop();
      window.scrollBy({ top: distance, behavior: 'instant' });
    }
    placed = offset();
  };

  window.addEventListener('scroll', align, listen);

  let ready = false;
  let quiet: ReturnType<typeof setTimeout> | undefined;
  const settle = () => {
    clearTimeout(quiet);
    quiet = setTimeout(stop, SETTLE_MS);
  };
  const resizes = new ResizeObserver(() => {
    align();
    if (ready) settle();
  });
  resizes.observe(document.body);
  watch.signal.addEventListener(
    'abort',
    () => {
      resizes.disconnect();
      clearTimeout(quiet);
    },
    { once: true },
  );

  whenLoaded(watch.signal)
    .then(() => document.fonts.ready)
    .then(() => {
      if (watch.signal.aborted) return;
      ready = true;
      align();
      settle();
    });
}
