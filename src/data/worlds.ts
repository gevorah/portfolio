export type WorldStage = 'world' | 'signal';

export interface WorldAction {
  label: string;
  href?: string;
}

export interface World {
  id: string;
  name: string;
  tagline: string;
  kind: string;
  status: string;
  context?: string;
  description: string;
  role?: string;
  technologies: string[];
  actions: WorldAction[];
  note: string;
  stage: WorldStage;
}

export const worlds: World[] = [
  {
    id: 'umbral',
    name: 'Umbral',
    tagline: 'Un mundo que cambia con las mareas.',
    kind: 'Experimento creativo',
    status: 'En desarrollo',
    context: 'Small Worlds',
    description:
      'Un mundo oceánico con mareas extraordinarias: la misma costa es otro lugar en pleamar y en bajamar. Es el primer mundo de Small Worlds, mi laboratorio de creative development.',
    role: 'Dirección de arte, diseño de interacción y desarrollo',
    technologies: ['Three.js', 'GLSL', 'Blender', 'Python'],
    actions: [{ label: 'Explorar experiencia' }, { label: 'Caso de estudio' }],
    note: 'La vista orbital usa los mapas del propio experimento. La experiencia interactiva todavía no está publicada.',
    stage: 'world',
  },
  {
    id: 'viajes',
    name: 'Plataforma de viajes',
    tagline: 'Historias de aventura, contadas por quienes las viven.',
    kind: 'Trabajo profesional',
    status: 'Febrero – julio de 2024',
    context: 'Aspis Consulting',
    description:
      'Una plataforma de viajes para aficionados a la aventura, desarrollada con React. Diseñé e implementé un sistema de blogging interactivo para que los usuarios compartan sus experiencias de viaje.',
    role: 'Full Stack Developer',
    technologies: ['React'],
    actions: [{ label: 'Caso de estudio' }],
    note: 'Este planeta es una representación conceptual provisional, no una imagen del producto.',
    stage: 'world',
  },
  {
    id: 'finanzas',
    name: 'Finanzas personales',
    tagline: 'Un proyecto propio que apenas toma forma.',
    kind: 'Proyecto personal',
    status: 'En desarrollo',
    description:
      'Un proyecto personal en desarrollo. Todavía no hay funcionalidades ni decisiones técnicas documentadas; este mundo crecerá cuando existan.',
    role: 'Diseño y desarrollo',
    technologies: [],
    actions: [{ label: 'Caso de estudio' }],
    note: 'Planeta conceptual provisional. Aún no hay un caso de estudio.',
    stage: 'world',
  },
  {
    id: 'duelos',
    name: 'Card battler táctico',
    tagline: 'Duelos decididos por sus personajes.',
    kind: 'Exploración futura',
    status: 'Planeado',
    description:
      'Un juego de cartas táctico centrado en duelos e impulsado por sus personajes. Es una idea en el horizonte, no un producto.',
    technologies: [],
    actions: [],
    note: 'Todavía es una señal: tendrá un planeta cuando exista algo que mostrar.',
    stage: 'signal',
  },
  {
    id: 'asistente',
    name: 'Asistente de código',
    tagline: 'Un asistente que reacciona a eventos.',
    kind: 'Exploración futura',
    status: 'Planeado',
    description:
      'Un asistente de código con arquitectura orientada a eventos. Por ahora es una señal lejana, sin implementación.',
    technologies: [],
    actions: [],
    note: 'Todavía es una señal: tendrá un planeta cuando exista algo que mostrar.',
    stage: 'signal',
  },
];

export const worldIds = worlds.map((world) => world.id);
