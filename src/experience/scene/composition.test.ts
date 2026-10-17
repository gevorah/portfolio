import * as THREE from 'three';
import { describe, expect, it } from 'vitest';

import {
  chooseView,
  scoreView,
  viewCandidates,
  viewDirection,
  type ViewProblem,
} from './composition';

const problem = (overrides: Partial<ViewProblem> = {}): ViewProblem => ({
  subject: new THREE.Vector3(-6, 0, 3),
  subjectRadius: 1.5,
  distance: 8,
  shiftX: -0.45,
  shiftY: 0,
  width: 1440,
  height: 900,
  fov: 36,
  protect: { left: 900, top: 120, right: 1380, bottom: 780 },
  obstacles: [],
  ...overrides,
});

describe('focus view composition', () => {
  it('keeps the default view when nothing competes with the text', () => {
    const candidates = viewCandidates(0.3);
    expect(chooseView(problem(), candidates)).toBe(candidates[0]);
  });

  it('scores a view higher when a body sits behind the protected text', () => {
    const candidates = viewCandidates(0.3);
    const clear = scoreView(problem(), candidates[0]);
    const sun = { position: new THREE.Vector3(), radius: 3.4, weight: 2 };
    const scores = candidates.map((candidate) =>
      scoreView(problem({ obstacles: [sun] }), candidate),
    );
    expect(clear).toBe(0);
    expect(Math.max(...scores)).toBeGreaterThan(0);
  });

  it('picks the candidate with the least intrusion', () => {
    const candidates = viewCandidates(0.3);
    const obstacles = [
      { position: new THREE.Vector3(), radius: 3.4, weight: 2 },
      { position: new THREE.Vector3(9, 0, -7), radius: 2.6, weight: 1 },
      { position: new THREE.Vector3(-3, 0, -12), radius: 1, weight: 0.3 },
    ];
    const scenario = problem({ obstacles });
    const chosen = chooseView(scenario, candidates);
    const chosenScore = scoreView(scenario, chosen);
    candidates.forEach((candidate) =>
      expect(chosenScore).toBeLessThanOrEqual(
        scoreView(scenario, candidate) + candidates.indexOf(candidate) * 0.5,
      ),
    );
  });

  it('ignores bodies behind the camera', () => {
    const candidates = viewCandidates(0.3);
    const scenario = problem();
    candidates.forEach((candidate) => {
      const behind = viewDirection(
        scenario.subject,
        candidate,
        new THREE.Vector3(),
      )
        .multiplyScalar(scenario.distance * 2)
        .add(scenario.subject);
      const obstacles = [{ position: behind, radius: 4, weight: 2 }];
      expect(scoreView({ ...scenario, obstacles }, candidate)).toBe(0);
    });
  });
});
