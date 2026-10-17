import * as THREE from 'three';

import { careerStages } from '@/data/career';

import type { SharedUniforms } from './bodies';
import { constellation, constellationThreads } from './looks';
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

const THREAD_STEPS = 24;

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

  const positions = new Float32Array(stars.length * 3);
  const sizes = new Float32Array(stars.length);
  const colors = new Float32Array(stars.length * 3);
  const brightness = new Float32Array(stars.length);
  const last = stars.length - 1;
  stars.forEach((stage, index) => {
    local(stage.id).toArray(positions, index * 3);
    sizes[index] = stage.rank === 'minor' ? 22 : index === last ? 52 : 36;
    new THREE.Color(
      index === last
        ? '#fff1dc'
        : stage.rank === 'minor'
          ? '#b4b1c1'
          : '#e4d8ff',
    ).toArray(colors, index * 3);
  });
  const starGeometry = new THREE.BufferGeometry();
  starGeometry.setAttribute(
    'position',
    new THREE.BufferAttribute(positions, 3),
  );
  starGeometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
  starGeometry.setAttribute('aColor', new THREE.BufferAttribute(colors, 3));
  const brightnessAttribute = new THREE.BufferAttribute(brightness, 1);
  starGeometry.setAttribute('aPhase', brightnessAttribute);
  const starUniforms = {
    uPixelRatio: shared.uPixelRatio,
    uFocalPx: shared.uFocalPx,
    uTime: shared.uTime,
    uAttenuate: { value: 0 },
    uOpacity: { value: 0 },
    uCore: { value: 0.26 },
    uGlow: { value: 0.75 },
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

  const mainThreads = constellationThreads.filter(
    (thread) => thread.weight === 1,
  );
  const threadPositions: number[] = [];
  const threadProgress: number[] = [];
  const threadWeight: number[] = [];
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  constellationThreads.forEach((thread) => {
    const mainIndex = mainThreads.indexOf(thread);
    const start = mainIndex >= 0 ? mainIndex / mainThreads.length : 0.08;
    const span = mainIndex >= 0 ? 1 / mainThreads.length : 0.22;
    const from = local(thread.from);
    const to = local(thread.to);
    for (let step = 0; step < THREAD_STEPS; step++) {
      const t0 = step / THREAD_STEPS;
      const t1 = (step + 1) / THREAD_STEPS;
      a.lerpVectors(from, to, t0);
      b.lerpVectors(from, to, t1);
      threadPositions.push(a.x, a.y, a.z, b.x, b.y, b.z);
      threadProgress.push(start + span * t0, start + span * t1);
      threadWeight.push(thread.weight, thread.weight);
    }
  });
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
  const threadUniforms = {
    uDraw: { value: 0 },
    uOpacity: { value: 0 },
    uColor: { value: new THREE.Color('#a583f2') },
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
    },
    update(dt: number, visibility: number, selectedId: string) {
      group.visible = visibility > 0.002;
      starUniforms.uOpacity.value = visibility;
      threadUniforms.uOpacity.value = visibility * 0.62;
      threadUniforms.uDraw.value = visibility * 1.06;
      stars.forEach((stage, index) => {
        const target = stage.id === selectedId ? 1 : 0;
        selection[index] +=
          (target - selection[index]) * (1 - Math.exp(-dt * 7));
        brightness[index] =
          (stage.rank === 'minor' ? 0.5 : 0.7) + 0.3 * selection[index];
      });
      brightnessAttribute.needsUpdate = true;
    },
  };
}
