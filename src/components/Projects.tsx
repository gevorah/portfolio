import { useState } from 'react';
import {
  motion,
  AnimatePresence,
  useTransform,
  useMotionValue
} from 'framer-motion';

const projects = [
  {
    id: 0,
    title: 'Welcome',
    description: "Here's some of my projects that I have worked on."
  },
  {
    id: 1,
    title: 'Portfolio',
    description:
      'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean quis libero ullamcorper, congue sapien sed, vehicula risus. Mauris fringilla, odio vel vehicula consectetur, mauris sem imperdiet leo, ac elementum ipsum elit eget leo. Cras ut viverra eros. ',
    links: ['']
  },
  {
    id: 2,
    title: 'Nintendo',
    description:
      'Aenean quis libero ullamcorper, congue sapien sed, vehicula risus. Mauris fringilla, odio vel vehicula consectetur, mauris sem imperdiet leo, ac elementum ipsum elit eget leo. Cras ut viverra eros. Proin porttitorenim nec metus accumsan condimentum.',
    links: ['']
  },
  {
    id: 3,
    title: 'Assistant',
    description:
      'Mauris fringilla, odio vel vehicula consectetur, mauris sem imperdiet leo, ac elementum ipsum elit eget leo. Cras ut viverra eros. Proin porttitorenim nec metus accumsan condimentum. Curabitur id ultricies odio. Vivamus in dolor facilisis, finibus purus finibus, ultricies erat.',
    links: ['']
  },
  {
    id: 4,
    title: 'Fund',
    description:
      'Vivamus in dolor facilisis, finibus purus finibus, ultricies erat.',
    links: ['']
  },
  {
    id: 5,
    title: 'Assistant',
    description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit.',
    links: ['']
  }
];

export default function Projects() {
  const [selected, setSelected] = useState<number>(0);

  const handleSelect = (id: number) => {
    setSelected(id);
  };

  return (
    <section
      id="home"
      data-section="home"
      className="relative flex flex-col items-center justify-center w-full px-6 md:px-16 mt-32"
    >
      <div className="relative max-w-5xl w-full p-9">
        <div className="absolute top-0 left-0 bg-[linear-gradient(to_right,purple,orange)] h-60 w-60 [clip-path:polygon(0%_0%,0%_100%,10%_80%,10%_10%,80%_10%,100%_0%);]"></div>
        <div className="my-32 flex flex-col md:flex-row w-full gap-6 items-center border-secondary p-9">
          <AnimatePresence initial={false} mode="popLayout">
            <Project {...projects.find(project => project.id === selected)} />
          </AnimatePresence>
          <div className="w-1/4">
            <h2 className="text-3xl font-normal">Projects</h2>
            <ul className="relative p-6 mt-6 rounded-xl flex flex-col gap-3 bg-primary-hard before:absolute before:-m-[2px] before:w-1/2 before:h-1/2 before:inset-0 before:bg-[linear-gradient(to_right,purple,orange)] before:-z-10 before:rounded-xl">
              {projects.map(
                project =>
                  project.id != 0 && (
                    <li key={project.id} className="h-6">
                      <button
                        onClick={() => handleSelect(project.id)}
                        className="text-secondary-3 hover:text-secondary-1 hover:tracking-wide relative pb-1 before:absolute before:bottom-0 before:left-0 before:w-full before:h-[2px] before:bg-[linear-gradient(to_right,purple,orange)]"
                      >
                        {project.title}
                      </button>
                    </li>
                  )
              )}
            </ul>
          </div>
        </div>
        <div className="absolute bottom-0 right-0 -rotate-180 bg-[linear-gradient(to_right,purple,orange)] h-60 w-60 [clip-path:polygon(0%_0%,0%_100%,10%_80%,10%_10%,80%_10%,100%_0%);]"></div>
      </div>
    </section>
  );
}

function Project({ title, description, links }: any) {
  return (
    <motion.article
      key={title}
      className="w-3/4 min-h-60"
      initial={{ x: '50%' }}
      animate={{ x: 0 }}
      exit={{ x: 0 }}
      transition={{ type: 'spring', duration: 1.5 }}
    >
      <h1 className="text-3xl font-normal">{title}</h1>
      <div className="relative mt-6 pl-6 before:absolute before:inset-0 before:w-[2px] before:h-full before:bg-[linear-gradient(to_bottom,purple,orange)]">
        <p>{description}</p>
        {links && links.length != 0 && (
          <div className="flex gap-6 mt-5">
            <a
              href=""
              className="text-secondary-3 hover:text-secondary-1 hover:tracking-wide relative pb-1 before:absolute before:bottom-0 before:left-0 before:w-full before:h-[2px] before:bg-[linear-gradient(to_right,purple,orange)]"
            >
              View Site
            </a>
            <a
              href=""
              className="text-secondary-3 hover:text-secondary-1 hover:tracking-wide relative pb-1 before:absolute before:bottom-0 before:left-0 before:w-full before:h-[2px] before:bg-[linear-gradient(to_right,purple,orange)]"
            >
              Github
            </a>
            <a
              href=""
              className="text-secondary-3 hover:text-secondary-1 hover:tracking-wide relative pb-1 before:absolute before:bottom-0 before:left-0 before:w-full before:h-[2px] before:bg-[linear-gradient(to_right,purple,orange)]"
            >
              NPM
            </a>
          </div>
        )}
      </div>
    </motion.article>
  );
}

