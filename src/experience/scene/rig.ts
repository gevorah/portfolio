import * as THREE from 'three';

import type { ExperienceState } from '../store';
import type { WorldBody } from './bodies';
import {
  CONSTELLATION_DIRECTION,
  CONSTELLATION_DISTANCE,
} from './constellation';
import { CONSTELLATION_EXTENT, SYSTEM_RADIUS } from './looks';

export const FOV = 36;

export interface Frame {
  cx: number;
  cy: number;
  width: number;
  height: number;
  fit: number;
}

export type FrameName = 'hero' | 'atlas' | 'focus' | 'career';
export type Frames = Record<FrameName, Frame>;

interface Pose {
  subject: THREE.Vector3;
  view: THREE.Vector3;
  distance: number;
  shiftX: number;
  shiftY: number;
}

const createPose = (): Pose => ({
  subject: new THREE.Vector3(),
  view: new THREE.Vector3(0, 0, 1),
  distance: 1,
  shiftX: 0,
  shiftY: 0,
});

const UP = new THREE.Vector3(0, 1, 0);

function direction(elevation: number, azimuth: number) {
  const e = THREE.MathUtils.degToRad(elevation);
  const a = THREE.MathUtils.degToRad(azimuth);
  return new THREE.Vector3(
    Math.sin(a) * Math.cos(e),
    Math.sin(e),
    Math.cos(a) * Math.cos(e),
  );
}

const HERO_VIEW = direction(21, 10);
const ATLAS_VIEW = direction(50, -22);

function mixPose(a: Pose, b: Pose, t: number, out: Pose) {
  out.subject.lerpVectors(a.subject, b.subject, t);
  out.view.lerpVectors(a.view, b.view, t).normalize();
  out.distance = Math.exp(
    THREE.MathUtils.lerp(Math.log(a.distance), Math.log(b.distance), t),
  );
  out.shiftX = THREE.MathUtils.lerp(a.shiftX, b.shiftX, t);
  out.shiftY = THREE.MathUtils.lerp(a.shiftY, b.shiftY, t);
  return out;
}

export function createRig(camera: THREE.PerspectiveCamera) {
  const hero = createPose();
  const atlas = createPose();
  const focus = createPose();
  const career = createPose();
  const work = createPose();
  const system = createPose();
  const final = createPose();

  const anchor = new THREE.Vector3();
  let anchorRadius = 1;
  const sunDirection = new THREE.Vector3();
  const side = new THREE.Vector3();
  const pointer = new THREE.Vector2();
  const faceDirection = new THREE.Vector3(0, 0, 1);
  const careerSubject = new THREE.Vector3();

  let width = 1;
  let height = 1;
  let focalPx = 1;

  function place(pose: Pose, frame: Frame, radius: number, aspectY: number) {
    const pxPerUnit =
      Math.min(
        frame.width / (2 * radius),
        frame.height / (2 * radius * aspectY),
      ) * frame.fit;
    pose.distance = focalPx / Math.max(pxPerUnit, 0.0001);
    pose.shiftX = (frame.cx - width / 2) / (width / 2);
    pose.shiftY = -(frame.cy - height / 2) / (height / 2);
    return pxPerUnit;
  }

  return {
    faceDirection,
    get focalPx() {
      return focalPx;
    },
    resize(nextWidth: number, nextHeight: number) {
      width = nextWidth;
      height = nextHeight;
      camera.aspect = width / height;
      focalPx = height / 2 / Math.tan(THREE.MathUtils.degToRad(FOV / 2));
    },
    displayScale(frames: Frames, state: ExperienceState) {
      const heroPx = place(hero, frames.hero, SYSTEM_RADIUS.hero, 0.55);
      const atlasPx = place(atlas, frames.atlas, SYSTEM_RADIUS.atlas, 0.82);
      const blend = state.weights.work + state.weights.career;
      const systemPx = THREE.MathUtils.lerp(heroPx, atlasPx, blend);
      return THREE.MathUtils.clamp(35 / systemPx, 1, 1.75);
    },
    constellationScale(frames: Frames) {
      const frame = frames.career;
      const pxPerUnit =
        Math.min(
          frame.width / (2 * CONSTELLATION_EXTENT[0]),
          frame.height / (2 * CONSTELLATION_EXTENT[1]),
        ) * frame.fit;
      return (pxPerUnit * CONSTELLATION_DISTANCE) / focalPx;
    },
    update(
      dt: number,
      frames: Frames,
      state: ExperienceState,
      focused: WorldBody | undefined,
      constellationCenter: THREE.Vector3,
      selectedStar: THREE.Vector3 | undefined,
      pointerTarget: THREE.Vector2,
    ) {
      hero.subject.set(0, 0, 0);
      hero.view.copy(HERO_VIEW);
      atlas.subject.set(0, 0, 0);
      atlas.view.copy(ATLAS_VIEW);

      if (focused) {
        if (state.focus < 0.02) {
          anchor.copy(focused.position);
          anchorRadius = focused.frameRadius;
        } else {
          const glide = 1 - Math.exp(-dt * 4);
          anchor.lerp(focused.position, glide);
          anchorRadius += (focused.frameRadius - anchorRadius) * glide;
        }

        sunDirection.copy(anchor).negate().normalize();
        side.crossVectors(UP, sunDirection).normalize();
        focus.view
          .copy(sunDirection)
          .multiplyScalar(0.3)
          .addScaledVector(side, 0.9)
          .addScaledVector(UP, focused.viewLift)
          .normalize();
        focus.subject.copy(anchor);
        place(focus, frames.focus, anchorRadius, 1);
        faceDirection
          .copy(focus.view)
          .addScaledVector(sunDirection, 0.45)
          .normalize();
      }

      careerSubject.copy(constellationCenter);
      if (selectedStar) careerSubject.lerp(selectedStar, 0.14);
      const follow = 1 - Math.exp(-dt * 3);
      career.subject.lerp(
        careerSubject,
        career.subject.lengthSq() === 0 ? 1 : follow,
      );
      career.view.copy(CONSTELLATION_DIRECTION).negate();
      place(career, frames.career, 1, 1);
      career.distance = CONSTELLATION_DISTANCE;

      if (focused && state.focus > 0) {
        mixPose(atlas, focus, state.focus, work);
        work.shiftX = THREE.MathUtils.lerp(
          atlas.shiftX,
          focus.shiftX,
          state.focusShift,
        );
        work.shiftY = THREE.MathUtils.lerp(
          atlas.shiftY,
          focus.shiftY,
          state.focusShift,
        );
      } else {
        mixPose(atlas, atlas, 0, work);
      }
      const toWork =
        state.weights.work /
        Math.max(state.weights.work + state.weights.hero, 0.0001);
      mixPose(hero, work, state.weights.career >= 1 ? 1 : toWork, system);
      mixPose(system, career, state.weights.career, final);

      const ease = state.reducedMotion ? 1 : 1 - Math.exp(-dt * 5);
      pointer.lerp(pointerTarget, ease);
      const parallax = state.reducedMotion
        ? 0
        : 0.014 * (1 - state.focus * 0.5);

      camera.position
        .copy(final.subject)
        .addScaledVector(final.view, final.distance);
      camera.up.copy(UP);
      camera.lookAt(final.subject);
      camera.updateProjectionMatrix();
      camera.projectionMatrix.elements[8] = -(
        final.shiftX +
        pointer.x * parallax
      );
      camera.projectionMatrix.elements[9] = -(
        final.shiftY +
        pointer.y * parallax
      );
      camera.projectionMatrixInverse.copy(camera.projectionMatrix).invert();
      camera.updateMatrixWorld();
    },
  };
}
