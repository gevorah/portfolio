export type StageCategory = 'employment' | 'collaboration';

export const categoryLabels: Record<StageCategory, string> = {
  employment: 'Employment',
  collaboration: 'Collaboration',
};

export interface CareerStage {
  id: string;
  company: string;
  shortName?: string;
  category: StageCategory;
  role: string;
  period: string;
  start: string;
  end: string | null;
  summary: string;
  technologies: string[];
  rank: 'major' | 'minor';
}

export const careerStages: CareerStage[] = [
  {
    id: 'icesi',
    company: 'Icesi University',
    shortName: 'Icesi',
    category: 'employment',
    role: 'Software Developer',
    period: 'Apr 2022 - Jun 2023',
    start: '2022-04',
    end: '2023-06',
    summary:
      'I built a platform to manage meal distribution for scholarship students, contributing to both its frontend and backend.',
    technologies: ['Java', 'React'],
    rank: 'major',
  },
  {
    id: 'appsco',
    company: 'Apps.co',
    category: 'collaboration',
    role: 'Frontend Developer',
    period: 'Dec 2022',
    start: '2022-12',
    end: '2022-12',
    summary:
      'I developed and maintained frontend features across multiple projects, improving usability and interface performance.',
    technologies: ['React', 'Next.js'],
    rank: 'minor',
  },
  {
    id: 'soytusalud',
    company: 'Fundación Soy Tu Salud',
    shortName: 'Soy Tu Salud',
    category: 'collaboration',
    role: 'Frontend Developer',
    period: 'Jan - Jun 2023',
    start: '2023-01',
    end: '2023-06',
    summary:
      'I developed a website providing information and support resources for single mothers.',
    technologies: ['React', 'Next.js'],
    rank: 'minor',
  },
  {
    id: 'encora',
    company: 'Encora',
    category: 'employment',
    role: 'Software Developer',
    period: 'Jul 2023 - Jan 2024',
    start: '2023-07',
    end: '2024-01',
    summary:
      'I built a blogging platform and researched robotic process automation tools to support process optimization initiatives.',
    technologies: ['React', 'Node.js'],
    rank: 'major',
  },
  {
    id: 'aspis',
    company: 'Aspis Consulting',
    shortName: 'Aspis',
    category: 'employment',
    role: 'Full Stack Developer',
    period: 'Feb - Jul 2024',
    start: '2024-02',
    end: '2024-07',
    summary:
      'I developed a travel platform for a consulting client, including an interactive blogging experience for sharing travel stories.',
    technologies: ['React', 'Next.js'],
    rank: 'major',
  },
  {
    id: 'zelity',
    company: 'Zelity',
    category: 'employment',
    role: 'Technical Lead',
    period: 'Aug 2024 - Present',
    start: '2024-08',
    end: null,
    summary:
      'I lead the development team and coordinate delivery with the client. I also build and maintain web platforms, design application and database architectures from the ground up, and improve delivery through CI/CD.',
    technologies: [
      'React',
      'Next.js',
      'Java',
      '.NET',
      'SQL Server',
      'AWS',
      'Azure',
    ],
    rank: 'major',
  },
];

export const stageIds = careerStages.map((stage) => stage.id);
export const defaultStageId = 'zelity';
