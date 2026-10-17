export type WorldStage = 'world' | 'signal';

export type StudyImage = 'high-tide' | 'low-tide';

export interface WorldStudy {
  caption: string;
  frames: readonly { image: StudyImage; alt: string; label: string }[];
}

export interface World {
  id: string;
  name: string;
  tagline: string;
  kind: string;
  status?: string;
  context?: string;
  description: string;
  study?: WorldStudy;
  note?: string;
  stage: WorldStage;
}

const entries = [
  {
    id: 'umbral',
    name: 'Umbral',
    tagline: 'An ocean world shaped by extraordinary tides.',
    kind: 'Creative study',
    context: 'Universe',
    description:
      'Umbral explores the atmosphere of a distant ocean world, where vast horizons, unfamiliar landscapes, and a sense of mystery invite you to imagine what lies beyond.',
    study: {
      caption: 'One coastline, revealed and reclaimed by the sea.',
      frames: [
        {
          image: 'high-tide',
          alt: 'A rocky overhang and sea stacks rising from calm water at high tide.',
          label: 'High tide',
        },
        {
          image: 'low-tide',
          alt: 'The same coast at low tide, with the rock shelf, pools and a cave exposed.',
          label: 'Low tide',
        },
      ],
    },
    stage: 'world',
  },
  {
    id: 'finance',
    name: 'Personal Finance',
    tagline: 'Making everyday finances easier to understand.',
    kind: 'Personal project',
    status: 'In development',
    description:
      "I'm building a personal finance application focused on helping people better understand and manage their money.",
    stage: 'world',
  },
  {
    id: 'card-battler',
    name: 'Parallax Zero',
    tagline: 'Characters shape the duel. Your decisions decide it.',
    kind: 'Tactical card battler',
    status: 'In development',
    description:
      'A character-driven tactical card battler built around reading your opponent, committing to your moves, and facing the consequences.',
    stage: 'signal',
  },
  {
    id: 'code-assistant',
    name: 'Code assistant',
    tagline: 'An assistant that reacts to events.',
    kind: 'Future exploration',
    status: 'Planned',
    description:
      'An event-driven code assistant. For now it is a distant signal with nothing built.',
    note: 'Still a signal. It becomes a planet once there is something to show.',
    stage: 'signal',
  },
] as const satisfies readonly World[];

export type WorldId = (typeof entries)[number]['id'];

export const worlds: readonly (World & { id: WorldId })[] = entries;

export const worldIds: readonly WorldId[] = worlds.map((world) => world.id);

export const isWorldId = (value: string | null | undefined): value is WorldId =>
  worldIds.includes(value as WorldId);
