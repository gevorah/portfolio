import * as THREE from 'three';

import { seededRandom, type SharedUniforms } from './bodies';
import { COMET_AXIS, COMET_POSITION, COMET_VIEW } from './comet';
import {
  nebulaFragment,
  nebulaVertex,
  pointsFragment,
  pointsVertex,
} from './shaders';

export const NEBULA_VIEW = COMET_VIEW;
export const NEBULA_POSITION = COMET_POSITION.clone()
  .addScaledVector(COMET_AXIS, 90)
  .addScaledVector(NEBULA_VIEW, -60);
export const NEBULA_EXTENT = 46;

const BAND = new THREE.Vector2(0.85, -0.53);
const FIELD_STARS = 900;
const SOURCES = [
  new THREE.Vector3(0.32, -0.16, 1),
  new THREE.Vector3(-0.22, 0.12, 0.55),
  new THREE.Vector3(0.66, -0.4, 0.45),
];

interface CloudLayer {
  depth: number;
  scale: number;
  opacity: number;
  seed: number;
}

const CLOUDS: CloudLayer[] = [
  { depth: -45, scale: 2.05, opacity: 0.35, seed: 2.4 },
  { depth: 0, scale: 1.15, opacity: 0.55, seed: 7.7 },
  { depth: 32, scale: 1.75, opacity: 0.7, seed: 13.2 },
];

function stars(count: number, seed: number, bright: boolean) {
  const random = seededRandom(seed);
  const positions = new Float32Array(count * 3);
  const sizes = new Float32Array(count);
  const colors = new Float32Array(count * 3);
  const phases = new Float32Array(count);
  const palette = ['#f3eafd', '#d3c2ff', '#aab9f4', '#f0cfd8'].map(
    (hex) => new THREE.Color(hex),
  );
  const gaussian = () => (random() + random() + random() + random() - 2) * 0.6;
  for (let index = 0; index < count; index++) {
    let x: number;
    let y: number;
    const source = SOURCES[Math.floor(random() * SOURCES.length)];
    if (!bright && random() < 0.08) {
      x = source.x + gaussian() * 0.16;
      y = source.y + gaussian() * 0.16;
    } else if (bright || random() < 0.35) {
      const along = gaussian() * 1.2 + 0.2;
      const across = gaussian() * 0.42;
      x = BAND.x * along - BAND.y * across;
      y = BAND.y * along + BAND.x * across;
    } else {
      x = random() * 2.4 - 1.2;
      y = random() * 2.4 - 1.2;
    }
    positions.set(
      [
        x * NEBULA_EXTENT,
        y * NEBULA_EXTENT,
        (random() - 0.5) * (bright ? 30 : 70),
      ],
      index * 3,
    );
    sizes[index] = bright ? 1.1 + random() * 1.1 : 0.22 + random() * 0.4;
    palette[random() < 0.55 ? 0 : 1 + Math.floor(random() * 3)].toArray(
      colors,
      index * 3,
    );
    phases[index] = bright ? 0.6 + random() * 0.25 : 0.2 + random() * 0.55;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute('aSize', new THREE.BufferAttribute(sizes, 1));
  geometry.setAttribute('aColor', new THREE.BufferAttribute(colors, 3));
  geometry.setAttribute('aPhase', new THREE.BufferAttribute(phases, 1));
  return geometry;
}

const color = (hex: string) => ({ value: new THREE.Color(hex) });

export function createNebula(shared: SharedUniforms) {
  const group = new THREE.Group();
  group.position.copy(NEBULA_POSITION);
  group.lookAt(NEBULA_POSITION.clone().add(NEBULA_VIEW));
  group.visible = false;

  const plane = new THREE.PlaneGeometry(2, 2);
  const cloudMaterials = CLOUDS.map((layer, index) => {
    const material = new THREE.ShaderMaterial({
      vertexShader: nebulaVertex,
      fragmentShader: nebulaFragment,
      defines: { LAYER: index },
      uniforms: {
        uOpacity: { value: 0 },
        uSeed: { value: layer.seed },
        uScale: { value: layer.scale },
        uSources: { value: SOURCES },
        uIndigo: color('#191a4a'),
        uViolet: color('#4a3b9c'),
        uBlue: color('#3646a6'),
        uMagenta: color('#8c4c97'),
        uLavender: color('#c3b2f3'),
        uPink: color('#f0cfe6'),
        uWhite: color('#fbf3ff'),
        uSoot: color('#0b0910'),
      },
      transparent: true,
      blending:
        index === CLOUDS.length - 1
          ? THREE.NormalBlending
          : THREE.AdditiveBlending,
      depthWrite: false,
    });
    const mesh = new THREE.Mesh(plane, material);
    mesh.position.z = layer.depth;
    mesh.scale.setScalar(NEBULA_EXTENT * layer.scale);
    mesh.frustumCulled = false;
    group.add(mesh);
    return material;
  });

  const starMaterial = (spikes: number, glow: number) =>
    new THREE.ShaderMaterial({
      vertexShader: pointsVertex,
      fragmentShader: pointsFragment,
      uniforms: {
        uPixelRatio: shared.uPixelRatio,
        uFocalPx: shared.uFocalPx,
        uTime: shared.uTime,
        uAttenuate: { value: 1 },
        uOpacity: { value: 0 },
        uCore: { value: spikes > 0 ? 0.16 : 0.55 },
        uGlow: { value: glow },
        uSpikes: { value: spikes },
      },
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
  const field = new THREE.Points(
    stars(FIELD_STARS, 964811, false),
    starMaterial(0, 0.35),
  );
  const beacons = new THREE.Points(
    stars(4, 5531, true),
    starMaterial(0.35, 0.45),
  );
  [field, beacons].forEach((points) => {
    points.frustumCulled = false;
    group.add(points);
  });
  const starMaterials = [field.material, beacons.material];

  return {
    group,
    update(visibility: number) {
      group.visible = visibility > 0.002;
      if (!group.visible) return;
      cloudMaterials.forEach(
        (material, index) =>
          (material.uniforms.uOpacity.value =
            CLOUDS[index].opacity * visibility),
      );
      starMaterials.forEach(
        (material) => (material.uniforms.uOpacity.value = visibility),
      );
    },
  };
}
