import Link from 'next/link'
import { getNotebooks } from '../../../lib/notebooks'

export const dynamic = 'force-dynamic'

export const metadata = {
  title: 'Lessons',
  description: 'Practice lessons that run as Python notebooks in the browser.'
}

export default async function NotebooksPage() {
  const notebooks = await getNotebooks()
  const first = notebooks[0]

  return (
    <main className="lesson-start">
      <p className="notebook-kicker">Practice</p>
      <h1>Lessons</h1>
      <p className="notebook-lead">
        Open a lesson, run the Python, and change the cells.
      </p>
      {first ? (
        <Link className="lesson-start-card" href={`/notebooks/${first.slug}`}>
          <span>
            <small>Start here</small>
            <strong>{first.title}</strong>
            {first.description ? <em>{first.description}</em> : null}
          </span>
          <span className="lesson-go">Open</span>
        </Link>
      ) : (
        <p className="notebook-hint">No lessons yet.</p>
      )}
    </main>
  )
}
