import * as THREE from 'three';

import { state } from '../store';
import {
  createOrbits,
  createStarfield,
  createSun,
  createWorlds,
  type FrameContext,
  type SharedUniforms,
} from './bodies';
import { createConstellation } from './constellation';
import { createRig, FOV, type FrameName, type Frames } from './rig';

export interface UniverseElements {
  canvas: HTMLCanvasElement;
  frames: Record<FrameName, HTMLElement>;
  worldMarkers: Map<string, HTMLElement>;
  starMarkers: Map<string, HTMLElement>;
}

export interface UniverseStats {
  fps: number;
  frameMs: number;
  pixelRatio: number;
  drawCalls: number;
  triangles: number;
}

const MAX_PIXEL_RATIO = 2;
const MIN_PIXEL_RATIO = 1;

async function loadTexture(
  url: string,
  colorSpace: THREE.ColorSpace,
  anisotropy: number,
) {
  const texture = await new THREE.TextureLoader().loadAsync(url);
  texture.colorSpace = colorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.anisotropy = anisotropy;
  return texture;
}

export async function createUniverse(elements: UniverseElements) {
  const { canvas } = elements;
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: 'high-performance',
  });
  renderer.setClearColor(0x0e0c13, 1);
  let pixelRatio = Math.min(window.devicePixelRatio, MAX_PIXEL_RATIO);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(FOV, 1, 0.1, 2400);
  const rig = createRig(camera);

  const shared: SharedUniforms = {
    uTime: { value: 0 },
    uPixelRatio: { value: pixelRatio },
    uFocalPx: { value: 1 },
    uSunPos: { value: new THREE.Vector3() },
  };

  const anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  const [albedo, data] = await Promise.all([
    loadTexture(
      '/textures/umbral/albedo.webp',
      THREE.SRGBColorSpace,
      anisotropy,
    ),
    loadTexture('/textures/umbral/data.webp', THREE.NoColorSpace, anisotropy),
  ]);

  const sun = createSun(shared);
  const orbits = createOrbits();
  const worlds = createWorlds(shared, { albedo, data });
  const worldById = new Map(worlds.map((world) => [world.id, world]));
  const starfield = createStarfield(shared);
  const constellation = createConstellation(shared);
  scene.add(starfield, orbits.group, sun.group, constellation.group);
  worlds.forEach((world) => scene.add(world.group));

  let width = 0;
  let height = 0;
  function resize() {
    width = canvas.clientWidth;
    height = canvas.clientHeight;
    if (!width || !height) return;
    renderer.setPixelRatio(pixelRatio);
    renderer.setSize(width, height, false);
    rig.resize(width, height);
    shared.uPixelRatio.value = pixelRatio;
    shared.uFocalPx.value = rig.focalPx;
    fits.clear();
    labelWidths.clear();
  }

  const fits = new Map<HTMLElement, number>();
  const frames = {} as Frames;
  function readFrames() {
    const origin = canvas.getBoundingClientRect();
    for (const name of Object.keys(elements.frames) as FrameName[]) {
      const element = elements.frames[name];
      const rect = element.getBoundingClientRect();
      let fit = fits.get(element);
      if (fit === undefined) {
        fit =
          parseFloat(getComputedStyle(element).getPropertyValue('--fit')) || 1;
        fits.set(element, fit);
      }
      frames[name] = {
        cx: rect.left - origin.left + rect.width / 2,
        cy: rect.top - origin.top + rect.height / 2,
        width: Math.max(rect.width, 1),
        height: Math.max(rect.height, 1),
        fit,
      };
    }
  }

  const pointer = new THREE.Vector2();
  const onPointerMove = (event: PointerEvent) => {
    if (event.pointerType !== 'mouse') return;
    pointer.set(
      (event.clientX / window.innerWidth) * 2 - 1,
      -((event.clientY / window.innerHeight) * 2 - 1),
    );
  };
  window.addEventListener('pointermove', onPointerMove, { passive: true });

  const projected = new THREE.Vector3();
  const viewPosition = new THREE.Vector3();
  function placeMarker(
    marker: HTMLElement,
    position: THREE.Vector3,
    radius: number,
    visible: boolean,
    labelRadius = radius,
  ) {
    viewPosition.copy(position).applyMatrix4(camera.matrixWorldInverse);
    projected.copy(position).project(camera);
    const x = (projected.x * 0.5 + 0.5) * width;
    const y = (1 - (projected.y * 0.5 + 0.5)) * height;
    const size =
      radius > 0
        ? (radius * rig.focalPx) / Math.max(-viewPosition.z, 0.001)
        : 0;
    const onScreen =
      visible &&
      viewPosition.z < 0 &&
      x > -size &&
      x < width + size &&
      y > -size &&
      y < height + size;
    marker.toggleAttribute('data-offstage', !onScreen);
    if (!onScreen) return;
    marker.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, 0)`;
    marker.style.setProperty('--size', `${(size * 2).toFixed(1)}px`);
    marker.style.setProperty(
      '--label-size',
      `${((size * 2 * labelRadius) / Math.max(radius, 0.0001)).toFixed(1)}px`,
    );
    const half = labelHalfWidth(marker) + 10;
    const nudge =
      half * 2 > width ? 0 : THREE.MathUtils.clamp(x, half, width - half) - x;
    marker.style.setProperty('--nudge', `${nudge.toFixed(1)}px`);
  }

  const labelWidths = new Map<HTMLElement, number>();
  function labelHalfWidth(marker: HTMLElement) {
    let half = labelWidths.get(marker);
    if (half === undefined) {
      half = (marker.firstElementChild as HTMLElement).offsetWidth / 2;
      if (half > 0) labelWidths.set(marker, half);
    }
    return half;
  }

  const context: FrameContext = {
    dt: 0,
    orbitTime: 0,
    displayScale: 1,
    recede: 0,
    focusId: null,
    focus: 0,
    hoverId: null,
    faceDirection: rig.faceDirection,
  };

  const stats: UniverseStats = {
    fps: 0,
    frameMs: 0,
    pixelRatio,
    drawCalls: 0,
    triangles: 0,
  };
  let slowFrames = 0;
  let sampleTime = 0;
  let sampleFrames = 0;
  function measure(dt: number) {
    sampleTime += dt;
    sampleFrames += 1;
    if (sampleTime < 1) return;
    stats.fps = sampleFrames / sampleTime;
    stats.frameMs = (sampleTime / sampleFrames) * 1000;
    stats.pixelRatio = pixelRatio;
    stats.drawCalls = renderer.info.render.calls;
    stats.triangles = renderer.info.render.triangles;
    slowFrames = stats.fps < 45 ? slowFrames + 1 : 0;
    if (slowFrames >= 3 && pixelRatio > MIN_PIXEL_RATIO) {
      pixelRatio = Math.max(MIN_PIXEL_RATIO, pixelRatio - 0.25);
      slowFrames = 0;
      resize();
    }
    sampleTime = 0;
    sampleFrames = 0;
  }

  let frameId = 0;
  let last = performance.now();
  let lastRender = 0;
  let running = false;

  function frame(now: number) {
    frameId = requestAnimationFrame(frame);
    if (state.outro > 0.98 && now - lastRender < 48) return;
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;
    lastRender = now;

    readFrames();
    const motion = state.reducedMotion ? 0 : 1;
    shared.uTime.value += dt * motion;
    context.dt = dt;
    context.orbitTime +=
      dt * motion * THREE.MathUtils.lerp(1, 0.06, state.focus);
    context.displayScale = rig.displayScale(frames, state);
    context.recede = state.recede;
    context.focusId = state.focusId;
    context.focus = state.focus;
    context.hoverId = state.hoverId;

    worlds.forEach((world) => world.update(context));
    const focused = state.focusId ? worldById.get(state.focusId) : undefined;
    constellation.fit(rig.constellationScale(frames));
    rig.update(
      dt,
      frames,
      state,
      focused,
      constellation.center,
      constellation.starPositions.get(state.stageId),
      pointer,
    );
    starfield.position.copy(camera.position);

    const systemVisibility = 1 - state.weights.career;
    sun.update(state.recede);
    orbits.update(context, systemVisibility);
    constellation.update(dt, state.weights.career, state.stageId);

    renderer.render(scene, camera);

    const worldsOnStage = systemVisibility > 0.45;
    worlds.forEach((world) => {
      const marker = elements.worldMarkers.get(world.id);
      if (marker) {
        placeMarker(
          marker,
          world.position,
          world.radius,
          worldsOnStage,
          world.labelRadius,
        );
      }
    });
    constellation.starPositions.forEach((position, id) => {
      const marker = elements.starMarkers.get(id);
      if (marker) placeMarker(marker, position, 0, state.weights.career > 0.55);
    });
    measure(dt);
  }

  function start() {
    if (running) return;
    running = true;
    last = performance.now();
    frameId = requestAnimationFrame(frame);
  }
  function stop() {
    running = false;
    cancelAnimationFrame(frameId);
  }
  const onVisibility = () => (document.hidden ? stop() : start());
  document.addEventListener('visibilitychange', onVisibility);

  const onContextLost = (event: Event) => {
    event.preventDefault();
    stop();
  };
  const onContextRestored = () => start();
  canvas.addEventListener('webglcontextlost', onContextLost);
  canvas.addEventListener('webglcontextrestored', onContextRestored);

  const observer = new ResizeObserver(resize);
  observer.observe(canvas);
  resize();
  if (!document.hidden) start();

  return {
    stats,
    dispose() {
      stop();
      observer.disconnect();
      window.removeEventListener('pointermove', onPointerMove);
      document.removeEventListener('visibilitychange', onVisibility);
      canvas.removeEventListener('webglcontextlost', onContextLost);
      canvas.removeEventListener('webglcontextrestored', onContextRestored);
      scene.traverse((object) => {
        const mesh = object as THREE.Mesh;
        mesh.geometry?.dispose();
        const materials = Array.isArray(mesh.material)
          ? mesh.material
          : [mesh.material];
        materials.forEach((material) => material?.dispose());
      });
      albedo.dispose();
      data.dispose();
      renderer.dispose();
    },
  };
}
