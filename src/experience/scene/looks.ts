export type SurfaceKind = 'umbral' | 'terra' | 'giant';

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
    tilt: number;
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

export const looks: Record<string, WorldLook> = {
  umbral: {
    type: 'planet',
    surface: 'umbral',
    radius: 1.3,
    orbit: { radius: 6.6, angle: 152, period: 190, inclination: 0.02 },
    spinPeriod: 150,
    tilt: 0.2,
    atmosphere: '#6f93ff',
    atmosphereStrength: 0.85,
    halo: { color: '#5d82f5', extent: 1.075, strength: 0.6 },
    moon: { radius: 0.2, distance: 2.5, period: 46, color: '#b3aebb' },
    feature: [0.92, 0.3, -0.24],
    frameRadius: 1.12,
  },
  travel: {
    type: 'planet',
    surface: 'terra',
    radius: 1.08,
    orbit: { radius: 10.6, angle: -38, period: 320, inclination: -0.035 },
    spinPeriod: 120,
    tilt: -0.32,
    atmosphere: '#ffb48a',
    atmosphereStrength: 0.7,
    halo: { color: '#f29a78', extent: 1.07, strength: 0.6 },
    palette: ['#141d38', '#2c7c84', '#d7ae82', '#7d4640'],
    frameRadius: 1.12,
  },
  finance: {
    type: 'planet',
    surface: 'giant',
    radius: 1.22,
    orbit: { radius: 14.6, angle: 34, period: 520, inclination: 0.03 },
    spinPeriod: 90,
    tilt: 0.42,
    atmosphere: '#9fb0ff',
    atmosphereStrength: 0.6,
    palette: ['#27305a', '#5c6db5', '#b9c1ee', '#e9d9b8'],
    ring: {
      inner: 1.45,
      outer: 2.25,
      colors: ['#8f96d8', '#e6d3ae'],
      tilt: 0.42,
    },
    frameRadius: 2.0,
    viewLift: 0.62,
  },
  'card-battler': {
    type: 'signal',
    radius: 0.55,
    orbit: { radius: 18.6, angle: 218, period: 900, inclination: 0.06 },
    color: '#a583f2',
    frameRadius: 1.9,
  },
  'code-assistant': {
    type: 'signal',
    radius: 0.5,
    orbit: { radius: 18.6, angle: -82, period: 900, inclination: 0.06 },
    color: '#7394fe',
    frameRadius: 1.9,
  },
};

export const SYSTEM_RADIUS = { hero: 16.4, atlas: 19.6 };

export const SYSTEM_VIEWS = {
  hero: { elevation: 21, azimuth: 10, roll: 0, aspect: 0.55 },
  atlas: { elevation: 50, azimuth: -22, roll: 0, aspect: 0.82 },
};

export interface ConstellationStar {
  position: [number, number, number];
  label?: 'below';
}

export const constellation: Record<string, ConstellationStar> = {
  icesi: { position: [-1.62, -0.28, 0.2] },
  appsco: { position: [-1.78, -1.0, -0.25] },
  soytusalud: { position: [-0.86, -0.98, 0.35], label: 'below' },
  encora: { position: [-0.46, 0.5, -0.3] },
  aspis: { position: [0.56, -0.12, 0.25], label: 'below' },
  zelity: { position: [1.58, 0.82, -0.1] },
};

export const constellationThreads: Array<{
  from: string;
  to: string;
  weight: number;
}> = [
  { from: 'icesi', to: 'encora', weight: 1 },
  { from: 'encora', to: 'aspis', weight: 1 },
  { from: 'aspis', to: 'zelity', weight: 1 },
  { from: 'icesi', to: 'appsco', weight: 0.42 },
  { from: 'icesi', to: 'soytusalud', weight: 0.42 },
];

export const CONSTELLATION_EXTENT: [number, number] = [2.0, 1.25];
