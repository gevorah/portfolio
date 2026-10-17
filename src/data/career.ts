export interface CareerStage {
  id: string;
  company: string;
  shortName?: string;
  role: string;
  period: string;
  highlights: string[];
  rank: 'major' | 'minor';
}

export const careerStages: CareerStage[] = [
  {
    id: 'icesi',
    company: 'Universidad Icesi',
    shortName: 'Icesi',
    role: 'Software Developer',
    period: 'Abril de 2022 – junio de 2023',
    highlights: [
      'Construí una plataforma con Java y React para gestionar la distribución de alimentación a estudiantes becados.',
    ],
    rank: 'major',
  },
  {
    id: 'appsco',
    company: 'Apps.co',
    role: 'Frontend Developer',
    period: 'Diciembre de 2022',
    highlights: [
      'Desarrollé y actualicé proyectos en React, mejorando la experiencia de usuario y el rendimiento de la interfaz.',
    ],
    rank: 'minor',
  },
  {
    id: 'soytusalud',
    company: 'Fundación Soy Tu Salud',
    shortName: 'Soy Tu Salud',
    role: 'Frontend Developer',
    period: 'Enero – junio de 2023',
    highlights: [
      'Desarrollé un sitio web con React y Next.js para ofrecer apoyo y recursos a madres solteras.',
    ],
    rank: 'minor',
  },
  {
    id: 'encora',
    company: 'Encora',
    role: 'Software Developer',
    period: 'Julio de 2023 – enero de 2024',
    highlights: [
      'Construí una plataforma de blogging con React y Node.js.',
      'Investigué y documenté tecnologías de RPA para la optimización de procesos.',
    ],
    rank: 'major',
  },
  {
    id: 'aspis',
    company: 'Aspis Consulting',
    shortName: 'Aspis',
    role: 'Full Stack Developer',
    period: 'Febrero – julio de 2024',
    highlights: [
      'Desarrollé una plataforma de viajes con React para aficionados a la aventura.',
      'Diseñé e implementé un sistema de blogging interactivo para compartir experiencias de viaje.',
    ],
    rank: 'major',
  },
  {
    id: 'zelity',
    company: 'Zelity',
    role: 'Technical Lead',
    period: 'Agosto de 2024 – actualidad',
    highlights: [
      'Coordino al equipo de desarrollo y mantengo la comunicación directa con el cliente.',
      'Implementé prácticas de CI/CD que redujeron los errores y los tiempos de entrega en un 70 %.',
      'Desarrollo y mantengo plataformas web con React, Next.js y Angular, e integro soluciones de AWS.',
      'Diseñé la arquitectura limpia de un proyecto Java EE y la estructura de su base de datos.',
    ],
    rank: 'major',
  },
];

export const defaultStageId = 'zelity';
