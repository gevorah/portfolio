import * as THREE from 'three';

export interface ViewCandidate {
  side: number;
  sunMix: number;
  lift: number;
}

export interface Obstacle {
  position: THREE.Vector3;
  radius: number;
  weight: number;
}

export interface ScreenRect {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

export interface ViewProblem {
  subject: THREE.Vector3;
  subjectRadius: number;
  distance: number;
  shiftX: number;
  shiftY: number;
  width: number;
  height: number;
  fov: number;
  protect: ScreenRect | null;
  obstacles: Obstacle[];
}

const UP = new THREE.Vector3(0, 1, 0);
const sunDirection = new THREE.Vector3();
const side = new THREE.Vector3();
const view = new THREE.Vector3();
const projected = new THREE.Vector3();
const inView = new THREE.Vector3();
const scratch = new THREE.PerspectiveCamera();

export function viewCandidates(lift: number): ViewCandidate[] {
  return [
    { side: 1, sunMix: 0.3, lift },
    { side: 1, sunMix: 0.3, lift: lift + 0.3 },
    { side: 1, sunMix: 0.55, lift: lift + 0.12 },
    { side: 1, sunMix: 0.05, lift },
    { side: -1, sunMix: 0.3, lift },
    { side: -1, sunMix: 0.3, lift: lift + 0.3 },
  ];
}

export function viewDirection(
  subject: THREE.Vector3,
  candidate: ViewCandidate,
  out: THREE.Vector3,
) {
  sunDirection.copy(subject).negate().normalize();
  side.crossVectors(UP, sunDirection).normalize();
  return out
    .copy(sunDirection)
    .multiplyScalar(candidate.sunMix)
    .addScaledVector(side, candidate.side * 0.9)
    .addScaledVector(UP, candidate.lift)
    .normalize();
}

const distanceToRect = (x: number, y: number, rect: ScreenRect) =>
  Math.hypot(
    x - Math.max(rect.left, Math.min(x, rect.right)),
    y - Math.max(rect.top, Math.min(y, rect.bottom)),
  );

export function scoreView(problem: ViewProblem, candidate: ViewCandidate) {
  const { width, height } = problem;
  viewDirection(problem.subject, candidate, view);
  scratch.fov = problem.fov;
  scratch.aspect = width / height;
  scratch.near = 0.1;
  scratch.far = 2400;
  scratch.position
    .copy(problem.subject)
    .addScaledVector(view, problem.distance);
  scratch.up.copy(UP);
  scratch.lookAt(problem.subject);
  scratch.updateProjectionMatrix();
  scratch.projectionMatrix.elements[8] = -problem.shiftX;
  scratch.projectionMatrix.elements[9] = -problem.shiftY;
  scratch.updateMatrixWorld();
  scratch.matrixWorldInverse.copy(scratch.matrixWorld).invert();

  const focal =
    height / 2 / Math.tan(THREE.MathUtils.degToRad(problem.fov / 2));
  const subjectX = (problem.shiftX * 0.5 + 0.5) * width;
  const subjectY = (1 - (problem.shiftY * 0.5 + 0.5)) * height;
  const subjectPx = (problem.subjectRadius * focal) / problem.distance;

  let score = 0;
  for (const obstacle of problem.obstacles) {
    inView.copy(obstacle.position).applyMatrix4(scratch.matrixWorldInverse);
    if (inView.z > -0.1) continue;
    projected.copy(obstacle.position).project(scratch);
    const x = (projected.x * 0.5 + 0.5) * width;
    const y = (1 - (projected.y * 0.5 + 0.5)) * height;
    const radius = (obstacle.radius * focal) / -inView.z;
    if (x < -radius || x > width + radius || y < -radius || y > height + radius)
      continue;

    if (problem.protect) {
      const intrusion = radius - distanceToRect(x, y, problem.protect);
      if (intrusion > 0)
        score += obstacle.weight * Math.min(intrusion, radius * 2);
    }
    const crowding =
      subjectPx + radius - Math.hypot(x - subjectX, y - subjectY);
    if (crowding > 0)
      score += obstacle.weight * 0.5 * Math.min(crowding, radius * 2);
  }
  return score;
}

export function chooseView(problem: ViewProblem, candidates: ViewCandidate[]) {
  let best = candidates[0];
  let bestScore = Infinity;
  candidates.forEach((candidate, index) => {
    const score = scoreView(problem, candidate) + index * 0.5;
    if (score < bestScore) {
      best = candidate;
      bestScore = score;
    }
  });
  return best;
}
