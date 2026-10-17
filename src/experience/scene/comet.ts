import * as THREE from 'three';

import type { SharedUniforms } from './bodies';
import { comaFragment, comaVertex, tailFragment, tailVertex } from './shaders';

export const COMET_POSITION = new THREE.Vector3(30, 26, 22);
export const COMET_AXIS = COMET_POSITION.clone().normalize();
export const COMET_TAIL = 24;
export const COMET_EXTENT = 9;

const UP = new THREE.Vector3(0, 1, 0);
export const COMET_VIEW = new THREE.Vector3()
  .crossVectors(COMET_AXIS, UP)
  .normalize()
  .addScaledVector(COMET_AXIS, -0.22)
  .addScaledVector(UP, 0.1)
  .normalize();

const SEGMENTS = 140;
const SLICES = 32;
const ARC = new THREE.Vector3(1, 0.25, 0).normalize();
const DRIFT = new THREE.Vector3(0.2, -1, 0).normalize();

interface TailLayer {
  length: number;
  width: [number, number];
  lateral: THREE.Vector3;
  bend: number;
  skew: number;
  fade: number;
  diffuse: number;
  streaks: number;
  warmth: number;
  opacity: number;
  seed: number;
  colors: [string, string, string, string];
}

const LAYERS: TailLayer[] = [
  {
    length: COMET_TAIL,
    width: [1.6, 3.4],
    lateral: ARC,
    bend: 0.3,
    skew: -0.05,
    fade: 1,
    diffuse: 0.55,
    streaks: 0.1,
    warmth: 0.35,
    opacity: 0.6,
    seed: 1.3,
    colors: ['#9b9cf0', '#b0a4e6', '#6a64c4', '#cfa0b8'],
  },
  {
    length: COMET_TAIL,
    width: [0.35, 1.1],
    lateral: DRIFT,
    bend: 0.2,
    skew: 0,
    fade: 0.7,
    diffuse: 0.3,
    streaks: 0.3,
    warmth: 0,
    opacity: 0.15,
    seed: 9.4,
    colors: ['#7488f4', '#6a82f2', '#4458da', '#7488f4'],
  },
];

function ribbonGeometry() {
  const tail = new Float32Array((SEGMENTS + 1) * (SLICES + 1) * 2);
  const indices: number[] = [];
  for (let segment = 0; segment <= SEGMENTS; segment++) {
    const u = Math.pow(segment / SEGMENTS, 1.6);
    for (let slice = 0; slice <= SLICES; slice++) {
      const index = segment * (SLICES + 1) + slice;
      tail[index * 2] = u;
      tail[index * 2 + 1] = (slice / SLICES) * 2 - 1;
      if (segment < SEGMENTS && slice < SLICES) {
        const next = index + SLICES + 1;
        indices.push(index, next, index + 1, index + 1, next, next + 1);
      }
    }
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute(
    'position',
    new THREE.BufferAttribute(new Float32Array(tail.length * 1.5), 3),
  );
  geometry.setAttribute('aTail', new THREE.BufferAttribute(tail, 2));
  geometry.setIndex(indices);
  return geometry;
}

const color = (hex: string) => ({ value: new THREE.Color(hex) });

export function createComet(shared: SharedUniforms) {
  const group = new THREE.Group();
  group.position.copy(COMET_POSITION);
  group.visible = false;

  const side = new THREE.Vector3().crossVectors(COMET_AXIS, UP).normalize();
  const lift = new THREE.Vector3().crossVectors(side, COMET_AXIS).normalize();
  const tails = new THREE.Group();
  tails.quaternion.setFromRotationMatrix(
    new THREE.Matrix4().makeBasis(side, lift, COMET_AXIS),
  );
  group.add(tails);

  const ribbon = ribbonGeometry();
  const tailMaterials = LAYERS.map((layer) => {
    const [head, mid, outer, warm] = layer.colors;
    const material = new THREE.ShaderMaterial({
      vertexShader: tailVertex,
      fragmentShader: tailFragment,
      uniforms: {
        uTime: shared.uTime,
        uOpacity: { value: 0 },
        uLength: { value: layer.length },
        uWidth: { value: new THREE.Vector2(...layer.width) },
        uBend: { value: layer.bend },
        uLateral: { value: layer.lateral },
        uSeed: { value: layer.seed },
        uSkew: { value: layer.skew },
        uFade: { value: layer.fade },
        uDiffuse: { value: layer.diffuse },
        uStreaks: { value: layer.streaks },
        uWarmth: { value: layer.warmth },
        uHead: color(head),
        uMid: color(mid),
        uOuter: color(outer),
        uWarm: color(warm),
      },
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(ribbon, material);
    mesh.position.z = -0.6;
    mesh.frustumCulled = false;
    tails.add(mesh);
    return material;
  });

  const comaUniforms = {
    uSize: { value: 10 },
    uAxis: { value: COMET_AXIS },
    uOpacity: { value: 0 },
  };
  const coma = new THREE.Mesh(
    new THREE.PlaneGeometry(2, 2),
    new THREE.ShaderMaterial({
      vertexShader: comaVertex,
      fragmentShader: comaFragment,
      uniforms: comaUniforms,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  coma.frustumCulled = false;
  group.add(coma);

  return {
    group,
    update(visibility: number) {
      group.visible = visibility > 0.002;
      if (!group.visible) return;
      tailMaterials.forEach(
        (material, index) =>
          (material.uniforms.uOpacity.value =
            LAYERS[index].opacity * visibility),
      );
      comaUniforms.uOpacity.value = visibility;
    },
  };
}
