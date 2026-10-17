import * as THREE from 'three';

import { careerStages, type CareerStage } from '@/data/career';

import { seededRandom, type SharedUniforms } from './bodies';
import {
  constellation,
  CONSTELLATION_HORIZON,
  constellationThreads,
} from './looks';
import {
  pointsFragment,
  pointsVertex,
  threadFragment,
  threadVertex,
} from './shaders';

export const CONSTELLATION_VIEWPOINT = new THREE.Vector3(6, 10, 44);
export const CONSTELLATION_DIRECTION = new THREE.Vector3(
  -0.25,
  0.62,
  -0.74,
).normalize();
export const CONSTELLATION_DISTANCE = 112;

const THREAD_STEPS = 28;
const BRANCH_KEYS: Array<[number, number]> = [
  [-0.5, 0.6],
  [-0.5, -0.6],
];

const months = (date: string) => {
  const [year, month] = date.split('-').map(Number);
  return year * 12 + month;
};

function starSize(stage: CareerStage, current: boolean) {
  if (current) return 92;
  if (stage.rank === 'minor') return 30;
  const duration = months(stage.end ?? stage.start) - months(stage.start);
  return 46 + (Math.min(duration, 18) / 18) * 18;
}

export function createConstellation(shared: SharedUniforms) {
  const group = new THREE.Group();
  group.position
    .copy(CONSTELLATION_VIEWPOINT)
    .addScaledVector(CONSTELLATION_DIRECTION, CONSTELLATION_DISTANCE);
  const toViewer = CONSTELLATION_DIRECTION.clone().negate();
  const right = new THREE.Vector3()
    .crossVectors(new THREE.Vector3(0, 1, 0), toViewer)
    .normalize();
  const up = new THREE.Vector3().crossVectors(toViewer, right);
  group.quaternion.setFromRotationMatrix(
    new THREE.Matrix4().makeBasis(right, up, toViewer),
  );

  const local = (id: string) =>
    new THREE.Vector3(...constellation[id].position);
  const stars = careerStages.filter((stage) => constellation[stage.id]);
  const world = new Map(stars.map((stage) => [stage.id, new THREE.Vector3()]));
  const last = stars.length - 1;

  const path = constellationThreads.filter((thread) => thread.kind === 'path');
  const branches = constellationThreads.filter(
    (thread) => thread.kind === 'branch',
  );
  const keys = new Map<string, THREE.Vector2>();
  path.forEach((thread, index) => {
    keys.set(thread.from, new THREE.Vector2(index / path.length, 0));
    keys.set(thread.to, new THREE.Vector2((index + 1) / path.length, 0));
  });
  branches.forEach((thread, index) => {
    const [x, y] = BRANCH_KEYS[index % BRANCH_KEYS.length];
    keys.set(thread.to, new THREE.Vector2(x, y));
  });

  const positions = new Float32Array(stars.length * 3);
  const sizes = new Float32Array(stars.length);
  const colors = new Float32Array(stars.length * 3);
  const brightness = new Float32Array(stars.length);
  stars.forEach((stage, index) => {
    local(stage.id).toArray(positions, index * 3);
    sizes[index] = starSize(stage, index === last);
    new THREE.Color(
      index === last
        ? '#fff1dc'
        : stage.rank === 'minor'
          ? '#b4b1c1'
          : '#e4d8ff',
    ).toArray(colors, index * 3);
  });
  const baseSizes = Float32Array.from(sizes);
  const sizeAttribute = new THREE.BufferAttribute(sizes, 1);
  const starGeometry = new THREE.BufferGeometry();
  starGeometry.setAttribute(
    'position',
    new THREE.BufferAttribute(positions, 3),
  );
  starGeometry.setAttribute('aSize', sizeAttribute);
  starGeometry.setAttribute('aColor', new THREE.BufferAttribute(colors, 3));
  const brightnessAttribute = new THREE.BufferAttribute(brightness, 1);
  starGeometry.setAttribute('aPhase', brightnessAttribute);
  const starUniforms = {
    uPixelRatio: shared.uPixelRatio,
    uFocalPx: shared.uFocalPx,
    uTime: shared.uTime,
    uAttenuate: { value: 0 },
    uOpacity: { value: 0 },
    uCore: { value: 0.13 },
    uGlow: { value: 0.5 },
    uSpikes: { value: 0.85 },
  };
  const points = new THREE.Points(
    starGeometry,
    new THREE.ShaderMaterial({
      vertexShader: pointsVertex,
      fragmentShader: pointsFragment,
      uniforms: starUniforms,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  points.frustumCulled = false;
  group.add(points);

  const threadPositions: number[] = [];
  const threadProgress: number[] = [];
  const threadWeight: number[] = [];
  const threadKeys: number[] = [];
  const curves: THREE.QuadraticBezierCurve3[] = [];
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const keyA = new THREE.Vector2();
  const keyB = new THREE.Vector2();

  function addThread(
    from: THREE.Vector3,
    to: THREE.Vector3,
    bow: number,
    progress: [number, number],
    key: [THREE.Vector2, THREE.Vector2],
    weight: (t: number) => number,
  ) {
    const middle = from.clone().lerp(to, 0.5);
    const normal = new THREE.Vector3(to.y - from.y, from.x - to.x, 0)
      .normalize()
      .multiplyScalar(from.distanceTo(to) * bow);
    const curve = new THREE.QuadraticBezierCurve3(from, middle.add(normal), to);
    curves.push(curve);
    for (let step = 0; step < THREAD_STEPS; step++) {
      const t0 = step / THREAD_STEPS;
      const t1 = (step + 1) / THREAD_STEPS;
      curve.getPoint(t0, a);
      curve.getPoint(t1, b);
      keyA.lerpVectors(key[0], key[1], t0);
      keyB.lerpVectors(key[0], key[1], t1);
      threadPositions.push(a.x, a.y, a.z, b.x, b.y, b.z);
      threadProgress.push(
        THREE.MathUtils.lerp(progress[0], progress[1], t0),
        THREE.MathUtils.lerp(progress[0], progress[1], t1),
      );
      threadWeight.push(weight(t0), weight(t1));
      threadKeys.push(keyA.x, keyA.y, keyB.x, keyB.y);
    }
  }

  path.forEach((thread, index) => {
    const start = index / path.length;
    const end = (index + 1) / path.length;
    addThread(
      local(thread.from),
      local(thread.to),
      index % 2 === 0 ? 0.09 : -0.09,
      [start, end],
      [keys.get(thread.from)!, keys.get(thread.to)!],
      (t) => 0.5 + 0.5 * THREE.MathUtils.lerp(start, end, t),
    );
  });
  branches.forEach((thread, index) => {
    addThread(
      local(thread.from),
      local(thread.to),
      index % 2 === 0 ? -0.1 : 0.1,
      [0.06, 0.3],
      [keys.get(thread.from)!, keys.get(thread.to)!],
      () => 0.4,
    );
  });
  const present = stars[last].id;
  addThread(
    local(present),
    new THREE.Vector3(...CONSTELLATION_HORIZON),
    0.07,
    [1, 1.2],
    [keys.get(present)!, new THREE.Vector2(1.5, 0)],
    (t) => 0.7 * (1 - t) ** 1.5,
  );

  const threadGeometry = new THREE.BufferGeometry();
  threadGeometry.setAttribute(
    'position',
    new THREE.Float32BufferAttribute(threadPositions, 3),
  );
  threadGeometry.setAttribute(
    'aProgress',
    new THREE.Float32BufferAttribute(threadProgress, 1),
  );
  threadGeometry.setAttribute(
    'aWeight',
    new THREE.Float32BufferAttribute(threadWeight, 1),
  );
  threadGeometry.setAttribute(
    'aKey',
    new THREE.Float32BufferAttribute(threadKeys, 2),
  );
  const threadUniforms = {
    uDraw: { value: 0 },
    uOpacity: { value: 0 },
    uFocus: { value: new THREE.Vector2(1, 0) },
    uColor: { value: new THREE.Color('#a583f2') },
    uAccent: { value: new THREE.Color('#f1e6ff') },
  };
  const threads = new THREE.LineSegments(
    threadGeometry,
    new THREE.ShaderMaterial({
      vertexShader: threadVertex,
      fragmentShader: threadFragment,
      uniforms: threadUniforms,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  threads.frustumCulled = false;
  group.add(threads);

  const dustCount = 190;
  const dustPositions = new Float32Array(dustCount * 3);
  const dustSizes = new Float32Array(dustCount);
  const dustColors = new Float32Array(dustCount * 3);
  const dustPhases = new Float32Array(dustCount);
  const random = seededRandom(31415);
  const gaussian = () => (random() + random() + random() - 1.5) / 1.5;
  const pale = new THREE.Color('#eeedf5');
  const tint = new THREE.Color('#a583f2');
  const mixed = new THREE.Color();
  for (let i = 0; i < dustCount; i++) {
    curves[Math.floor(random() * curves.length)].getPoint(random(), a);
    a.x += gaussian() * 0.3;
    a.y += gaussian() * 0.26;
    a.z += gaussian() * 0.9;
    a.toArray(dustPositions, i * 3);
    dustSizes[i] = 1.1 + random() * 1.6;
    mixed
      .copy(pale)
      .lerp(tint, random() * 0.6)
      .toArray(dustColors, i * 3);
    dustPhases[i] = 0.14 + random() ** 2 * 0.5;
  }
  const dustGeometry = new THREE.BufferGeometry();
  dustGeometry.setAttribute(
    'position',
    new THREE.BufferAttribute(dustPositions, 3),
  );
  dustGeometry.setAttribute('aSize', new THREE.BufferAttribute(dustSizes, 1));
  dustGeometry.setAttribute('aColor', new THREE.BufferAttribute(dustColors, 3));
  dustGeometry.setAttribute('aPhase', new THREE.BufferAttribute(dustPhases, 1));
  const dustUniforms = {
    uPixelRatio: shared.uPixelRatio,
    uFocalPx: shared.uFocalPx,
    uTime: shared.uTime,
    uAttenuate: { value: 0 },
    uOpacity: { value: 0 },
    uCore: { value: 0.9 },
    uGlow: { value: 0 },
    uSpikes: { value: 0 },
  };
  const dust = new THREE.Points(
    dustGeometry,
    new THREE.ShaderMaterial({
      vertexShader: pointsVertex,
      fragmentShader: pointsFragment,
      uniforms: dustUniforms,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  dust.frustumCulled = false;
  group.add(dust);

  const selection = new Float32Array(stars.length);
  return {
    group,
    center: group.position,
    starPositions: world,
    fit(worldScale: number) {
      if (group.scale.x === worldScale) return;
      group.scale.setScalar(worldScale);
      group.updateMatrixWorld(true);
      world.forEach((position, id) =>
        position.copy(local(id)).applyMatrix4(group.matrixWorld),
      );
      const pxPerUnit =
        (worldScale * shared.uFocalPx.value) / CONSTELLATION_DISTANCE;
      const density = THREE.MathUtils.clamp(pxPerUnit / 190, 0.5, 1.1);
      baseSizes.forEach((size, index) => (sizes[index] = size * density));
      sizeAttribute.needsUpdate = true;
    },
    update(
      damp: (rate: number) => number,
      visibility: number,
      selectedId: string,
    ) {
      group.visible = visibility > 0.002;
      starUniforms.uOpacity.value = visibility;
      dustUniforms.uOpacity.value = visibility;
      threadUniforms.uOpacity.value = visibility * 0.6;
      threadUniforms.uDraw.value = visibility * 1.26;
      const focusKey = keys.get(selectedId);
      if (focusKey) threadUniforms.uFocus.value.lerp(focusKey, damp(5));
      stars.forEach((stage, index) => {
        const target = stage.id === selectedId ? 1 : 0;
        selection[index] += (target - selection[index]) * damp(7);
        const rest = stage.rank === 'minor' ? 0.42 : 0.6;
        brightness[index] = rest + (1 - rest) * selection[index];
      });
      brightnessAttribute.needsUpdate = true;
    },
  };
}
