import * as THREE from 'three';

import { worldIds, type WorldId } from '@/data/worlds';

import {
  looks,
  SUN_RADIUS,
  type OrbitLook,
  type PlanetLook,
  type SignalLook,
} from './looks';
import {
  bodyVertex,
  haloFragment,
  PLANET_KIND,
  planetFragment,
  pointsFragment,
  pointsVertex,
  ringFragment,
  ringVertex,
  sunFragment,
} from './shaders';

export interface SharedUniforms {
  uTime: THREE.IUniform<number>;
  uPixelRatio: THREE.IUniform<number>;
  uFocalPx: THREE.IUniform<number>;
  uSunPos: THREE.IUniform<THREE.Vector3>;
}

export interface SharedGeometry {
  sphere: THREE.SphereGeometry;
  lowSphere: THREE.SphereGeometry;
}

export interface UmbralTextures {
  albedo: THREE.Texture;
  data: THREE.Texture;
}

export interface FrameContext {
  dt: number;
  ambientDt: number;
  orbitTime: number;
  displayScale: number;
  recede: number;
  focusId: WorldId | null;
  focus: number;
  hoverId: WorldId | null;
  faceDirection: THREE.Vector3;
  damp(rate: number): number;
}

export interface WorldBody {
  id: WorldId;
  group: THREE.Group;
  position: THREE.Vector3;
  radius: number;
  frameRadius: number;
  labelRadius: number;
  viewLift: number;
  orbit: OrbitLook;
  veil: number;
  update(context: FrameContext): void;
}

const color = (hex: string) => new THREE.Color(hex);
const TAU = Math.PI * 2;
const UP = new THREE.Vector3(0, 1, 0);

export const createSharedGeometry = (): SharedGeometry => ({
  sphere: new THREE.SphereGeometry(1, 96, 64),
  lowSphere: new THREE.SphereGeometry(1, 32, 24),
});

export function orbitPosition(
  orbit: OrbitLook,
  time: number,
  target: THREE.Vector3,
) {
  const angle =
    THREE.MathUtils.degToRad(orbit.angle) + (TAU * time) / orbit.period;
  const z = Math.sin(angle) * orbit.radius;
  return target.set(
    Math.cos(angle) * orbit.radius,
    z * Math.sin(orbit.inclination),
    z * Math.cos(orbit.inclination),
  );
}

const shortestAngle = (angle: number) =>
  Math.atan2(Math.sin(angle), Math.cos(angle));

const hoverTarget = (context: FrameContext, id: WorldId) =>
  context.hoverId === id && context.focusId !== id ? 1 : 0;

const recedeFor = (context: FrameContext, id: WorldId) =>
  context.focusId === id ? 0 : context.recede;

function createPlanet(
  id: WorldId,
  look: PlanetLook,
  shared: SharedUniforms,
  geometry: SharedGeometry,
  textures: UmbralTextures,
): WorldBody {
  const group = new THREE.Group();
  const tilt = new THREE.Group();
  tilt.rotation.z = look.tilt;
  group.add(tilt);

  const palette = (look.palette ?? ['#000', '#000', '#000', '#000']).map(color);
  const uniforms = {
    uTime: shared.uTime,
    uSunPos: shared.uSunPos,
    uAtmosphere: { value: color(look.atmosphere) },
    uAtmosphereStrength: { value: look.atmosphereStrength },
    uRecede: { value: 0 },
    uVeil: { value: 0 },
    uHover: { value: 0 },
    uSeed: {
      value: new THREE.Vector3(3.1, 7.7, 1.9).multiplyScalar(look.radius * 4),
    },
    uColorA: { value: palette[0] },
    uColorB: { value: palette[1] },
    uColorC: { value: palette[2] },
    uColorD: { value: palette[3] },
    uAlbedo: { value: textures.albedo },
    uData: { value: textures.data },
    uRingNormal: { value: new THREE.Vector3(0, 1, 0) },
    uRingRadii: { value: new THREE.Vector2(0, 0) },
    uCenter: { value: new THREE.Vector3() },
  };
  const surface = new THREE.Mesh(
    geometry.sphere,
    new THREE.ShaderMaterial({
      vertexShader: bodyVertex,
      fragmentShader: planetFragment,
      uniforms,
      defines: { KIND: PLANET_KIND[look.surface] },
    }),
  );
  tilt.add(surface);

  let haloUniforms:
    | { uRadius: THREE.IUniform<number>; uStrength: THREE.IUniform<number> }
    | undefined;
  if (look.halo) {
    const halo = new THREE.Mesh(
      geometry.lowSphere,
      new THREE.ShaderMaterial({
        vertexShader: bodyVertex,
        fragmentShader: haloFragment,
        uniforms: {
          uSunPos: shared.uSunPos,
          uColor: { value: color(look.halo.color) },
          uCenter: uniforms.uCenter,
          uRadius: { value: 1 },
          uExtent: { value: look.halo.extent },
          uStrength: { value: look.halo.strength },
        },
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      }),
    );
    halo.scale.setScalar(look.halo.extent * 1.02);
    haloUniforms = halo.material.uniforms as typeof haloUniforms;
    group.add(halo);
  }

  let ringUniforms:
    | {
        uPlanetRadius: THREE.IUniform<number>;
        uRecede: THREE.IUniform<number>;
        uVeil: THREE.IUniform<number>;
      }
    | undefined;
  if (look.ring) {
    const ring = new THREE.Mesh(
      new THREE.RingGeometry(look.ring.inner, look.ring.outer, 128, 1),
      new THREE.ShaderMaterial({
        vertexShader: ringVertex,
        fragmentShader: ringFragment,
        uniforms: {
          uSunPos: shared.uSunPos,
          uCenter: uniforms.uCenter,
          uPlanetRadius: { value: 1 },
          uRadii: {
            value: new THREE.Vector2(look.ring.inner, look.ring.outer),
          },
          uColorA: { value: color(look.ring.colors[0]) },
          uColorB: { value: color(look.ring.colors[1]) },
          uOpacity: { value: look.ring.opacity },
          uRecede: { value: 0 },
          uVeil: uniforms.uVeil,
        },
        transparent: true,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    ring.rotation.x = Math.PI / 2;
    ringUniforms = ring.material.uniforms as typeof ringUniforms;
    tilt.add(ring);
  }

  let moon: THREE.Mesh | undefined;
  let moonUniforms: { uCenter: THREE.IUniform<THREE.Vector3> } | undefined;
  if (look.moon) {
    moonUniforms = { uCenter: { value: new THREE.Vector3() } };
    moon = new THREE.Mesh(
      geometry.lowSphere,
      new THREE.ShaderMaterial({
        vertexShader: bodyVertex,
        fragmentShader: planetFragment,
        uniforms: {
          ...uniforms,
          ...moonUniforms,
          uColorA: { value: color(look.moon.color) },
          uAtmosphereStrength: { value: 0 },
          uHover: { value: 0 },
        },
        defines: { KIND: PLANET_KIND.moon },
      }),
    );
    moon.scale.setScalar(look.moon.radius);
    group.add(moon);
  }

  const ringNormal = new THREE.Vector3();
  const radial = new THREE.Vector3();
  const tangent = new THREE.Vector3();
  const haloStrength = look.halo?.strength ?? 0;
  let spin = 0;
  let hover = 0;
  let moonTime = 0;
  const body: WorldBody = {
    id,
    group,
    position: group.position,
    radius: look.radius,
    frameRadius: look.radius * look.frameRadius,
    labelRadius: look.radius,
    viewLift: look.viewLift ?? 0.3,
    orbit: look.orbit,
    veil: 0,
    update(context) {
      orbitPosition(look.orbit, context.orbitTime, group.position);
      const scale = look.radius * context.displayScale;
      group.scale.setScalar(scale);
      body.radius = scale;
      body.frameRadius = scale * look.frameRadius;
      body.labelRadius = scale * (look.ring ? look.ring.outer * 0.52 : 1);

      const attention = context.focusId === id ? context.focus : 0;
      spin += ((TAU * context.ambientDt) / look.spinPeriod) * (1 - attention);
      if (look.feature && attention > 0) {
        const [fx, , fz] = look.feature;
        const facing =
          Math.atan2(context.faceDirection.x, context.faceDirection.z) -
          Math.atan2(fx, fz);
        spin += shortestAngle(facing - spin) * context.damp(2.4) * attention;
      }
      surface.rotation.y = spin;

      hover += (hoverTarget(context, id) - hover) * context.damp(9);
      uniforms.uHover.value = hover;
      uniforms.uRecede.value = recedeFor(context, id);
      uniforms.uVeil.value +=
        (body.veil - uniforms.uVeil.value) * context.damp(6);
      uniforms.uCenter.value.copy(group.position);
      if (haloUniforms) {
        haloUniforms.uRadius.value = scale;
        haloUniforms.uStrength.value =
          haloStrength * (1 - 0.85 * uniforms.uVeil.value);
      }
      if (look.ring && ringUniforms) {
        tilt.updateWorldMatrix(true, false);
        ringNormal.setFromMatrixColumn(tilt.matrixWorld, 1).normalize();
        uniforms.uRingNormal.value.copy(ringNormal);
        uniforms.uRingRadii.value.set(
          look.ring.inner * scale,
          look.ring.outer * scale,
        );
        ringUniforms.uPlanetRadius.value = scale;
        ringUniforms.uRecede.value = uniforms.uRecede.value;
      }
      if (moon && look.moon && moonUniforms) {
        moonTime += context.ambientDt * 0.4 * attention;
        const angle = (TAU * (context.orbitTime + moonTime)) / look.moon.period;
        radial.copy(group.position).normalize();
        tangent.crossVectors(UP, radial).normalize();
        moon.position
          .copy(tangent)
          .multiplyScalar(Math.cos(angle))
          .addScaledVector(UP, Math.sin(angle) * 0.94)
          .addScaledVector(radial, Math.sin(angle) * 0.34)
          .multiplyScalar(look.moon.distance);
        moonUniforms.uCenter.value
          .copy(moon.position)
          .multiplyScalar(scale)
          .add(group.position);
      }
    },
  };
  return body;
}

function createSignal(
  id: WorldId,
  look: SignalLook,
  shared: SharedUniforms,
): WorldBody {
  const group = new THREE.Group();
  const count = 240;
  const positions = new Float32Array(count * 3);
  const sizes = new Float32Array(count);
  const colors = new Float32Array(count * 3);
  const phases = new Float32Array(count).fill(1);
  const tint = color(look.color);
  const pale = color('#eeedf5');
  const mixed = new THREE.Color();
  const random = seededRandom(id.length * 97 + id.charCodeAt(0));
  for (let i = 1; i < count; i++) {
    const distance = 0.25 + Math.pow(random(), 0.7) * 0.75;
    const angle = random() * TAU;
    positions[i * 3] = Math.cos(angle) * distance;
    positions[i * 3 + 1] = (random() - 0.5) * 0.9 * (1.25 - distance);
    positions[i * 3 + 2] = Math.sin(angle) * distance;
    sizes[i] = 0.035 + random() * 0.05;
    mixed.copy(tint).lerp(pale, random() * 0.5);
    mixed.toArray(colors, i * 3);
    phases[i] = 0.35 + random() * 0.65;
  }
  sizes[0] = 0.34;
  tint.clone().lerp(pale, 0.35).toArray(colors, 0);

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
  geometry.setAttribute('aColor', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1));
  const uniforms = {
    uPixelRatio: shared.uPixelRatio,
    uFocalPx: shared.uFocalPx,
    uTime: shared.uTime,
    uAttenuate: { value: 1 },
    uOpacity: { value: 1 },
    uCore: { value: 0.5 },
    uGlow: { value: 0.9 },
    uSpikes: { value: 0 },
  };
  const dust = new THREE.Points(
    geometry,
    new THREE.ShaderMaterial({
      vertexShader: pointsVertex,
      fragmentShader: pointsFragment,
      uniforms,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  dust.rotation.x = 0.5;
  group.add(dust);

  let hover = 0;
  let veil = 0;
  const body: WorldBody = {
    id,
    group,
    position: group.position,
    radius: look.radius,
    frameRadius: look.radius * look.frameRadius,
    labelRadius: look.radius,
    viewLift: look.viewLift ?? 0.3,
    orbit: look.orbit,
    veil: 0,
    update(context) {
      orbitPosition(look.orbit, context.orbitTime, group.position);
      const scale = look.radius * context.displayScale;
      group.scale.setScalar(scale);
      body.radius = scale;
      body.frameRadius = scale * look.frameRadius;
      body.labelRadius = scale;
      dust.rotation.y = (TAU * context.orbitTime) / 70;
      hover += (hoverTarget(context, id) - hover) * context.damp(9);
      veil += (body.veil - veil) * context.damp(6);
      const attention = context.focusId === id ? context.focus : 0;
      const pulse =
        0.8 + 0.2 * Math.sin(shared.uTime.value * 0.9 + look.orbit.angle);
      uniforms.uOpacity.value =
        (0.62 + 0.38 * Math.max(hover, attention)) *
        pulse *
        (1 - 0.5 * recedeFor(context, id)) *
        (1 - 0.85 * veil);
    },
  };
  return body;
}

export function seededRandom(seed: number) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

export function createWorlds(
  shared: SharedUniforms,
  geometry: SharedGeometry,
  textures: UmbralTextures,
) {
  return worldIds.map((id) => {
    const look = looks[id];
    return look.type === 'planet'
      ? createPlanet(id, look, shared, geometry, textures)
      : createSignal(id, look, shared);
  });
}

export function createSun(shared: SharedUniforms, geometry: SharedGeometry) {
  const group = new THREE.Group();
  const uniforms = { uTime: shared.uTime, uRecede: { value: 0 } };
  const core = new THREE.Mesh(
    geometry.sphere,
    new THREE.ShaderMaterial({
      vertexShader: bodyVertex,
      fragmentShader: sunFragment,
      uniforms,
    }),
  );
  core.scale.setScalar(SUN_RADIUS);
  group.add(core);

  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 256;
  const context = canvas.getContext('2d')!;
  const gradient = context.createRadialGradient(128, 128, 0, 128, 128, 128);
  gradient.addColorStop(0, 'rgba(255, 226, 178, 0.95)');
  gradient.addColorStop(0.16, 'rgba(246, 178, 124, 0.5)');
  gradient.addColorStop(0.38, 'rgba(190, 108, 124, 0.16)');
  gradient.addColorStop(0.7, 'rgba(120, 84, 150, 0.04)');
  gradient.addColorStop(1, 'rgba(120, 84, 150, 0)');
  context.fillStyle = gradient;
  context.fillRect(0, 0, 256, 256);
  const glowTexture = new THREE.CanvasTexture(canvas);
  glowTexture.colorSpace = THREE.SRGBColorSpace;
  const glowMaterial = new THREE.SpriteMaterial({
    map: glowTexture,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    transparent: true,
  });
  const glow = new THREE.Sprite(glowMaterial);
  glow.scale.setScalar(SUN_RADIUS * 9);
  group.add(glow);

  let veil = 0;
  return {
    group,
    radius: SUN_RADIUS,
    update(context: FrameContext, veilTarget: number) {
      veil += (veilTarget - veil) * context.damp(6);
      uniforms.uRecede.value = Math.min(1, context.recede + veil);
      glowMaterial.opacity = (1 - 0.45 * context.recede) * (1 - 0.8 * veil);
    },
    dispose() {
      glowTexture.dispose();
    },
  };
}

export function createOrbits() {
  const group = new THREE.Group();
  const lines = new Map<string, THREE.LineBasicMaterial>();
  const drawn = new Map<string, THREE.LineBasicMaterial>();
  const point = new THREE.Vector3();
  for (const [id, look] of Object.entries(looks)) {
    const key = `${look.orbit.radius}:${look.orbit.inclination}`;
    let material = drawn.get(key);
    if (!material) {
      const points: THREE.Vector3[] = [];
      const steps = 256;
      for (let i = 0; i <= steps; i++) {
        const time = (i / steps) * look.orbit.period;
        points.push(
          orbitPosition({ ...look.orbit, angle: 0 }, time, point).clone(),
        );
      }
      const geometry = new THREE.BufferGeometry().setFromPoints(points);
      const settings = {
        color: look.type === 'signal' ? '#8d86a8' : '#b7a6e6',
        transparent: true,
        opacity: 0,
        depthWrite: false,
      };
      if (look.type === 'signal') {
        const dashed = new THREE.LineDashedMaterial({
          ...settings,
          dashSize: 0.5,
          gapSize: 0.7,
        });
        const line = new THREE.Line(geometry, dashed);
        line.computeLineDistances();
        group.add(line);
        material = dashed;
      } else {
        material = new THREE.LineBasicMaterial(settings);
        group.add(new THREE.Line(geometry, material));
      }
      drawn.set(key, material);
    }
    lines.set(id, material);
  }
  const active = new Map([...drawn.values()].map((material) => [material, 0]));
  return {
    group,
    update(context: FrameContext, visibility: number) {
      active.forEach((_, material) => active.set(material, 0));
      lines.forEach((material, id) => {
        const lit = context.hoverId === id || context.focusId === id ? 1 : 0;
        active.set(material, Math.max(active.get(material) ?? 0, lit));
      });
      active.forEach((lit, material) => {
        const rest = material instanceof THREE.LineDashedMaterial ? 0.2 : 0.3;
        const target =
          (rest + 0.34 * lit) * (1 - 0.8 * context.recede) * visibility;
        material.opacity += (target - material.opacity) * context.damp(8);
      });
    },
  };
}

export function createStarfield(shared: SharedUniforms) {
  const count = 2200;
  const positions = new Float32Array(count * 3);
  const sizes = new Float32Array(count);
  const colors = new Float32Array(count * 3);
  const phases = new Float32Array(count);
  const random = seededRandom(271828);
  const palette = [
    color('#f3eafd'),
    color('#a9c7ee'),
    color('#efd0b5'),
    color('#c0a1ff'),
  ];
  const band = new THREE.Vector3(0.35, 0.86, 0.36).normalize();
  const direction = new THREE.Vector3();
  for (let i = 0; i < count; i++) {
    do {
      direction.set(random() * 2 - 1, random() * 2 - 1, random() * 2 - 1);
    } while (direction.lengthSq() > 1 || direction.lengthSq() < 0.01);
    direction.normalize();
    if (i % 3 === 0) {
      direction
        .addScaledVector(band, -direction.dot(band) * (0.55 + random() * 0.4))
        .normalize();
    }
    direction.multiplyScalar(900).toArray(positions, i * 3);
    const bright = random();
    sizes[i] = bright > 0.97 ? 3.2 : 1.1 + random() * 1.3;
    palette[random() > 0.7 ? 1 + Math.floor(random() * 3) : 0].toArray(
      colors,
      i * 3,
    );
    phases[i] = bright > 0.97 ? 1 : 0.32 + random() * 0.62;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
  geometry.setAttribute('aColor', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1));
  const points = new THREE.Points(
    geometry,
    new THREE.ShaderMaterial({
      vertexShader: pointsVertex,
      fragmentShader: pointsFragment,
      uniforms: {
        uPixelRatio: shared.uPixelRatio,
        uFocalPx: shared.uFocalPx,
        uTime: shared.uTime,
        uAttenuate: { value: 0 },
        uOpacity: { value: 1 },
        uCore: { value: 0.9 },
        uGlow: { value: 0 },
        uSpikes: { value: 0 },
      },
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  points.frustumCulled = false;
  return points;
}
