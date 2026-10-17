import * as THREE from 'three';

import {
  resolveLabels,
  type LabelItem,
  type LabelPlacement,
  type LabelSide,
} from '../labels';
import { damping, settleWindow } from '../motion';
import { createResolutionGovernor } from '../resolution';
import { onInvalidate, state } from '../store';
import {
  createOrbits,
  createSharedGeometry,
  createStarfield,
  createSun,
  createWorlds,
  type FrameContext,
  type SharedUniforms,
} from './bodies';
import type { Obstacle, ScreenRect } from './composition';
import { createConstellation } from './constellation';
import { createRig, FOV, type FrameName, type Frames } from './rig';

export interface UniverseElements {
  canvas: HTMLCanvasElement;
  frames: Record<FrameName, HTMLElement>;
  protect: HTMLElement;
  worldMarkers: Map<string, HTMLElement>;
  starMarkers: Map<string, HTMLElement>;
}

export interface UniverseStats {
  mode: 'idle' | 'ambient' | 'interactive';
  frames: number;
  frameMs: number;
  cpuMs: number;
  pixelRatio: number;
  drawCalls: number;
  triangles: number;
}

const MAX_PIXEL_RATIO = 2;
const MIN_PIXEL_RATIO = 1;
const AMBIENT_INTERVAL = 1000 / 30;
const SUN_GLOW_RADIUS = 2.2;
const VEIL_MARGIN = 14;

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

interface Projection {
  x: number;
  y: number;
  radius: number;
  onScreen: boolean;
}

export async function createUniverse(elements: UniverseElements) {
  const { canvas } = elements;
  const cleanup: Array<() => void> = [];
  const dispose = () => {
    cleanup.reverse().forEach((release) => release());
    cleanup.length = 0;
  };

  try {
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    });
    cleanup.push(() => renderer.dispose());
    renderer.setClearColor(0x0e0c13, 1);

    const governor = createResolutionGovernor({
      min: MIN_PIXEL_RATIO,
      max: Math.max(
        MIN_PIXEL_RATIO,
        Math.min(window.devicePixelRatio, MAX_PIXEL_RATIO),
      ),
    });
    let pixelRatio = governor.ratio;

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
    const textures = await Promise.allSettled([
      loadTexture(
        '/textures/umbral/albedo.webp',
        THREE.SRGBColorSpace,
        anisotropy,
      ),
      loadTexture('/textures/umbral/data.webp', THREE.NoColorSpace, anisotropy),
    ]);
    textures.forEach((result) => {
      if (result.status === 'fulfilled')
        cleanup.push(() => result.value.dispose());
    });
    const failed = textures.find((result) => result.status === 'rejected');
    if (failed) throw failed.reason;
    const [albedo, data] = textures.map(
      (result) => (result as PromiseFulfilledResult<THREE.Texture>).value,
    );

    const geometry = createSharedGeometry();
    const sun = createSun(shared, geometry);
    const orbits = createOrbits();
    const worlds = createWorlds(shared, geometry, { albedo, data });
    const worldById = new Map(worlds.map((world) => [world.id, world]));
    const starfield = createStarfield(shared);
    const constellation = createConstellation(shared);
    scene.add(starfield, orbits.group, sun.group, constellation.group);
    worlds.forEach((world) => scene.add(world.group));
    cleanup.push(() => {
      scene.traverse((object) => {
        const mesh = object as THREE.Mesh;
        mesh.geometry?.dispose();
        const materials = Array.isArray(mesh.material)
          ? mesh.material
          : [mesh.material];
        materials.forEach((material) => material?.dispose());
      });
      geometry.sphere.dispose();
      geometry.lowSphere.dispose();
      sun.dispose();
    });

    let width = 0;
    let height = 0;
    const fits = new Map<HTMLElement, number>();
    const labelWidths = new Map<HTMLElement, number>();

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
      invalidate();
    }

    const frames = {} as Frames;
    let origin = canvas.getBoundingClientRect();
    function readFrames() {
      origin = canvas.getBoundingClientRect();
      for (const name of Object.keys(elements.frames) as FrameName[]) {
        const element = elements.frames[name];
        const rect = element.getBoundingClientRect();
        let fit = fits.get(element);
        if (fit === undefined) {
          fit =
            parseFloat(getComputedStyle(element).getPropertyValue('--fit')) ||
            1;
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

    function readProtect(): ScreenRect | null {
      const rect = elements.protect.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) return null;
      return {
        left: rect.left - origin.left,
        top: rect.top - origin.top,
        right: rect.right - origin.left,
        bottom: rect.bottom - origin.top,
      };
    }

    const pointer = new THREE.Vector2();
    const onPointerMove = (event: PointerEvent) => {
      if (event.pointerType !== 'mouse' || !state.motion.parallax) return;
      pointer.set(
        (event.clientX / window.innerWidth) * 2 - 1,
        -((event.clientY / window.innerHeight) * 2 - 1),
      );
      invalidate();
    };
    window.addEventListener('pointermove', onPointerMove, { passive: true });
    cleanup.push(() =>
      window.removeEventListener('pointermove', onPointerMove),
    );

    const projected = new THREE.Vector3();
    const viewPosition = new THREE.Vector3();
    function project(position: THREE.Vector3, radius: number): Projection {
      viewPosition.copy(position).applyMatrix4(camera.matrixWorldInverse);
      projected.copy(position).project(camera);
      const x = (projected.x * 0.5 + 0.5) * width;
      const y = (1 - (projected.y * 0.5 + 0.5)) * height;
      const size = (radius * rig.focalPx) / Math.max(-viewPosition.z, 0.001);
      const onScreen =
        viewPosition.z < 0 &&
        x > -size &&
        x < width + size &&
        y > -size &&
        y < height + size;
      return { x, y, radius: size, onScreen };
    }

    function labelHalfWidth(marker: HTMLElement) {
      let half = labelWidths.get(marker);
      if (half === undefined) {
        half = (marker.firstElementChild as HTMLElement).offsetWidth / 2;
        if (half > 0) labelWidths.set(marker, half);
      }
      return half;
    }

    const placements = new Map<string, LabelPlacement>();
    function placeMarkers(
      entries: Array<{
        id: string;
        marker: HTMLElement;
        projection: Projection;
        labelRadius: number;
        priority: number;
        prefer: LabelSide;
        visible: boolean;
      }>,
    ) {
      const items: LabelItem[] = [];
      for (const entry of entries) {
        const { marker, projection } = entry;
        const shown = entry.visible && projection.onScreen;
        marker.toggleAttribute('data-offstage', !shown);
        if (!shown) {
          placements.delete(entry.id);
          continue;
        }
        marker.style.transform = `translate3d(${projection.x.toFixed(1)}px, ${projection.y.toFixed(1)}px, 0)`;
        marker.style.setProperty(
          '--size',
          `${(projection.radius * 2).toFixed(1)}px`,
        );
        items.push({
          id: entry.id,
          x: projection.x,
          y: projection.y,
          bodyRadius: projection.radius,
          labelRadius: entry.labelRadius,
          halfWidth: labelHalfWidth(marker),
          height: 20,
          priority: entry.priority,
          prefer: entry.prefer,
        });
      }
      const results = resolveLabels(items, width, placements);
      for (const entry of entries) {
        const result = results.get(entry.id);
        if (!result) continue;
        placements.set(entry.id, result.placement);
        entry.marker.dataset.label = result.placement;
        entry.marker.style.setProperty(
          '--label-offset',
          `${entry.labelRadius.toFixed(1)}px`,
        );
        entry.marker.style.setProperty(
          '--nudge',
          `${result.nudge.toFixed(1)}px`,
        );
      }
    }

    const intrudes = (projection: Projection, rect: ScreenRect | null) => {
      if (!rect || !projection.onScreen) return false;
      const dx =
        projection.x - Math.max(rect.left, Math.min(projection.x, rect.right));
      const dy =
        projection.y - Math.max(rect.top, Math.min(projection.y, rect.bottom));
      return Math.hypot(dx, dy) < projection.radius + VEIL_MARGIN;
    };

    const context: FrameContext = {
      dt: 0,
      ambientDt: 0,
      orbitTime: 0,
      displayScale: 1,
      recede: 0,
      focusId: null,
      focus: 0,
      hoverId: null,
      faceDirection: rig.faceDirection,
      damp: (rate) => damping(state.motion, rate, context.dt),
    };
    const sunObstacle: Obstacle = {
      position: sun.group.position,
      radius: sun.radius * SUN_GLOW_RADIUS,
      weight: 2,
    };

    const stats: UniverseStats = {
      mode: 'idle',
      frames: 0,
      frameMs: 0,
      cpuMs: 0,
      pixelRatio,
      drawCalls: 0,
      triangles: 0,
    };

    const intruders: string[] = [];
    let frameId = 0;
    let lastRender = 0;
    let lastFrame = 0;
    let activeUntil = 0;
    let wasInteractive = false;
    let contextLost = false;

    function schedule() {
      if (frameId || document.hidden || contextLost) return;
      frameId = requestAnimationFrame(frame);
    }

    function invalidate() {
      activeUntil = performance.now() + settleWindow(state.motion);
      schedule();
    }

    function frame(now: number) {
      frameId = 0;
      const interactive = now < activeUntil;
      const ambient = state.motion.ambient && state.outro < 0.98;
      if (!interactive && !ambient) {
        stats.mode = 'idle';
        wasInteractive = false;
        return;
      }
      schedule();
      if (!interactive && now - lastRender < AMBIENT_INTERVAL - 1) return;

      const started = performance.now();
      const gap = now - lastRender;
      const dt = gap > 100 ? 1 / 60 : gap / 1000;
      const interval = now - lastFrame;
      lastRender = now;
      lastFrame = now;

      readFrames();
      const engaged = state.weights.work;
      const ambientDt = ambient ? dt : 0;
      shared.uTime.value += ambientDt;
      context.dt = dt;
      context.ambientDt = ambientDt;
      context.orbitTime +=
        ambientDt * THREE.MathUtils.lerp(1, 0.06, state.focus * engaged);
      context.displayScale = rig.displayScale(frames, state);
      context.recede = state.recede * engaged;
      context.focusId = state.focusId;
      context.focus = state.focus;
      context.hoverId = state.hoverId;

      worlds.forEach((world) => world.update(context));
      const focused = state.focusId ? worldById.get(state.focusId) : undefined;
      const protect = focused ? readProtect() : null;
      const obstacles: Obstacle[] = [sunObstacle];
      worlds.forEach((world) => {
        if (world === focused) return;
        obstacles.push({
          position: world.position,
          radius: world.frameRadius,
          weight: world.orbit.radius > 16 ? 0.3 : 1,
        });
      });
      constellation.fit(rig.constellationScale(frames));
      rig.update({
        frames,
        state,
        focused,
        obstacles,
        protect,
        constellationCenter: constellation.center,
        selectedStar: constellation.starPositions.get(state.stageId),
        pointer,
        damp: context.damp,
      });
      starfield.position.copy(camera.position);

      const systemVisibility = 1 - state.weights.career;
      const veiling = state.recede * engaged;
      const sunProjection = project(
        sun.group.position,
        sun.radius * SUN_GLOW_RADIUS,
      );
      sun.update(context, intrudes(sunProjection, protect) ? veiling : 0);
      orbits.update(context, systemVisibility);
      constellation.update(context.damp, state.weights.career, state.stageId);

      const worldsOnStage = systemVisibility > 0.45;
      intruders.length = 0;
      const worldEntries = worlds.map((world) => {
        const projection = project(world.position, world.radius);
        const reach = project(world.position, world.frameRadius);
        const intruding = world !== focused && intrudes(reach, protect);
        if (intruding) intruders.push(world.id);
        world.veil = intruding ? veiling : 0;
        const current = world === focused && state.focused && engaged > 0.5;
        return {
          id: world.id,
          marker: elements.worldMarkers.get(world.id)!,
          projection,
          labelRadius: (world.labelRadius / world.radius) * projection.radius,
          priority:
            (state.hoverId === world.id ? 4 : 0) +
            (world.orbit.radius > 16 ? 1 : 2),
          prefer: 'below' as LabelSide,
          visible: worldsOnStage && !current,
        };
      });

      renderer.render(scene, camera);

      placeMarkers(worldEntries.filter((entry) => entry.marker));
      placeMarkers(
        [...constellation.starPositions].flatMap(([id, position]) => {
          const marker = elements.starMarkers.get(id);
          if (!marker) return [];
          return [
            {
              id: `star:${id}`,
              marker,
              projection: { ...project(position, 0), radius: 12 },
              labelRadius: 16,
              priority: id === state.stageId ? 3 : 1,
              prefer: (marker.dataset.prefer === 'below'
                ? 'below'
                : 'above') as LabelSide,
              visible: state.weights.career > 0.55,
            },
          ];
        }),
      );

      const cpu = performance.now() - started;
      stats.mode = interactive ? 'interactive' : 'ambient';
      stats.frames += 1;
      stats.frameMs = interval;
      stats.cpuMs = cpu;
      stats.drawCalls = renderer.info.render.calls;
      stats.triangles = renderer.info.render.triangles;

      const next = governor.sample({
        interval,
        cpu,
        throttled: !(interactive && wasInteractive),
        now,
      });
      wasInteractive = interactive;
      if (next !== null) {
        pixelRatio = next;
        stats.pixelRatio = next;
        resize();
      }
    }

    cleanup.push(() => cancelAnimationFrame(frameId));
    cleanup.push(onInvalidate(invalidate));

    const onVisibility = () => {
      if (!document.hidden) invalidate();
    };
    document.addEventListener('visibilitychange', onVisibility);
    cleanup.push(() =>
      document.removeEventListener('visibilitychange', onVisibility),
    );

    const onContextLost = (event: Event) => {
      event.preventDefault();
      contextLost = true;
    };
    const onContextRestored = () => {
      contextLost = false;
      invalidate();
    };
    canvas.addEventListener('webglcontextlost', onContextLost);
    canvas.addEventListener('webglcontextrestored', onContextRestored);
    cleanup.push(() => {
      canvas.removeEventListener('webglcontextlost', onContextLost);
      canvas.removeEventListener('webglcontextrestored', onContextRestored);
    });

    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    cleanup.push(() => observer.disconnect());
    resize();

    return {
      stats,
      dispose,
      setOrbitTime(seconds: number) {
        context.orbitTime = seconds;
        invalidate();
      },
      inspect: () => ({
        intruders: [...intruders],
        veils: Object.fromEntries(
          worlds.map((world) => [world.id, world.veil]),
        ),
        labels: Object.fromEntries(placements),
      }),
    };
  } catch (error) {
    dispose();
    throw error;
  }
}
