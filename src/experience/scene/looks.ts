export type SurfaceKind = 'umbral' | 'giant';

export interface OrbitLook {
  radius: number;
  angle: number;
  period: number;
  inclination: number;
}

export interface PlanetLook {
  type: 'planet';
  surface: SurfaceKind;
  radius: number;
  orbit: OrbitLook;
  spinPeriod: number;
  tilt: number;
  atmosphere: string;
  atmosphereStrength: number;
  halo?: { color: string; extent: number; strength: number };
  palette?: [string, string, string, string];
  ring?: {
    inner: number;
    outer: number;
    colors: [string, string];
    opacity: number;
  };
  moon?: { radius: number; distance: number; period: number; color: string };
  feature?: [number, number, number];
  frameRadius: number;
  viewLift?: number;
}

export interface SignalLook {
  type: 'signal';
  radius: number;
  orbit: OrbitLook;
  color: string;
  frameRadius: number;
  viewLift?: number;
}

export type WorldLook = PlanetLook | SignalLook;

export const SUN_RADIUS = 1.55;
export const SIGNAL_ORBIT = 16.9;

export const looks: Record<string, WorldLook> = {
  umbral: {
    type: 'planet',
    surface: 'umbral',
    radius: 1.3,
    orbit: { radius: 6.6, angle: 158, period: 190, inclination: 0.02 },
    spinPeriod: 150,
    tilt: 0.2,
    atmosphere: '#6f93ff',
    atmosphereStrength: 0.85,
    halo: { color: '#5d82f5', extent: 1.075, strength: 0.6 },
    moon: { radius: 0.2, distance: 1.5, period: 46, color: '#b3aebb' },
    feature: [0.92, 0.3, -0.24],
    frameRadius: 1.12,
  },
  finance: {
    type: 'planet',
    surface: 'giant',
    radius: 1.22,
    orbit: { radius: 12.2, angle: -24, period: 430, inclination: -0.03 },
    spinPeriod: 90,
    tilt: 0.42,
    atmosphere: '#9fb0ff',
    atmosphereStrength: 0.6,
    palette: ['#27305a', '#5c6db5', '#b9c1ee', '#e9d9b8'],
    ring: {
      inner: 1.34,
      outer: 1.7,
      colors: ['#8f96d8', '#e6d3ae'],
      opacity: 0.6,
    },
    frameRadius: 1.6,
    viewLift: 0.62,
  },
  'card-battler': {
    type: 'signal',
    radius: 0.55,
    orbit: { radius: SIGNAL_ORBIT, angle: 222, period: 900, inclination: 0.06 },
    color: '#a583f2',
    frameRadius: 1.9,
  },
  'code-assistant': {
    type: 'signal',
    radius: 0.5,
    orbit: { radius: SIGNAL_ORBIT, angle: 62, period: 900, inclination: 0.06 },
    color: '#7394fe',
    frameRadius: 1.9,
  },
};

export const SYSTEM_RADIUS = { hero: 14.6, atlas: 18.1 };

export const SYSTEM_VIEWS = {
  hero: { elevation: 19, azimuth: 16, roll: -11, aspect: 0.62 },
  atlas: { elevation: 48, azimuth: -20, roll: 0, aspect: 0.8 },
};

export interface ConstellationStar {
  position: [number, number, number];
  label?: 'below';
}

export const constellation: Record<string, ConstellationStar> = {
  icesi: { position: [-1.7, -0.32, 0.3] },
  appsco: { position: [-1.38, -1.04, -0.5] },
  soytusalud: { position: [-0.72, -0.8, 0.55], label: 'below' },
  encora: { position: [-0.38, 0.34, -0.45] },
  aspis: { position: [0.42, -0.06, 0.4], label: 'below' },
  zelity: { position: [1.22, 0.7, -0.15] },
};

export const constellationThreads: Array<{
  from: string;
  to: string;
  kind: 'path' | 'branch';
}> = [
  { from: 'icesi', to: 'encora', kind: 'path' },
  { from: 'encora', to: 'aspis', kind: 'path' },
  { from: 'aspis', to: 'zelity', kind: 'path' },
  { from: 'icesi', to: 'appsco', kind: 'branch' },
  { from: 'icesi', to: 'soytusalud', kind: 'branch' },
];

export const CONSTELLATION_HORIZON: [number, number, number] = [
  2.05, 1.02, -0.6,
];

export const CONSTELLATION_EXTENT: [number, number] = [2.15, 1.3];
