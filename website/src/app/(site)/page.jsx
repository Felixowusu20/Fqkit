import { CircuitDiagram } from '../../../components/circuit-diagram'

export const metadata = {
  title: { absolute: 'FQkit' },
  description: 'A small Python toolkit for learning quantum circuits.'
}

const routes = [
  {
    href: '/docs/tutorials',
    title: 'Lessons',
    text: 'Superposition, interference, and entanglement.',
    spec: 'H 0',
    caption: 'One Hadamard'
  },
  {
    href: '/docs/algorithms',
    title: 'Algorithms',
    text: 'Deutsch, Bernstein-Vazirani, Grover, and variational methods.',
    spec: 'H 0; H 1; CZ 0 1',
    caption: 'Mark a state'
  },
  {
    href: '/docs/applications',
    title: 'Applications',
    text: 'Chemistry, telecommunications, physics, and cryptography.',
    spec: 'H 0; CNOT 0 1; RZ pi 0',
    caption: 'A shared pair'
  },
  {
    href: '/notebooks',
    title: 'Notebooks',
    text: 'Write Python, run the cell, and read the result.',
    spec: 'H 0; CNOT 0 1',
    caption: 'A Bell state'
  },
  {
    href: '/docs/gates',
    title: 'Gates',
    text: 'Every gate FQkit can draw and apply.',
    spec: 'H 0; CNOT 0 1; SWAP 1 2',
    caption: 'Hadamard, CNOT, SWAP'
  }
]

export default function HomePage() {
  return (
    <main className="home">
      <p className="home-kicker">Quantum circuits in Python</p>
      <h1>FQkit</h1>
      <p className="home-lead">
        A small toolkit for learning quantum circuits. Pick a circuit to open
        that part of the site.
      </p>
      <nav className="home-circuits" aria-label="Sections">
        {routes.map(route => (
          <a key={route.href} href={route.href} className="home-circuit">
            <CircuitDiagram spec={route.spec} caption={route.caption} />
            <strong>{route.title}</strong>
            <span>{route.text}</span>
          </a>
        ))}
      </nav>
    </main>
  )
}
