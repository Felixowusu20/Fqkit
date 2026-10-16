import Link from 'next/link'
import { notFound } from 'next/navigation'
import { CodingNotebook } from '../../../../../components/coding-notebook'
import { getNotebook, getNotebooks } from '../../../../lib/notebooks'

export const dynamic = 'force-dynamic'

export async function generateMetadata({ params }) {
  const { slug } = await params
  const notebook = await getNotebook(slug)
  if (!notebook) return { title: 'Notebook' }
  return { title: notebook.title, description: notebook.description }
}

export default async function NotebookPage({ params }) {
  const { slug } = await params
  const notebook = await getNotebook(slug)
  if (!notebook) notFound()
  const notebooks = await getNotebooks()
  const index = notebooks.findIndex(item => item.slug === slug)
  const next = index >= 0 ? notebooks[index + 1] : null

  return (
    <article className="notebook">
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap"
      />
      <header className="lesson-head">
        <p className="notebook-kicker">
          <Link href="/notebooks">Lessons</Link>
          {index >= 0 ? <span>{index + 1} / {notebooks.length}</span> : null}
        </p>
        <h1>{notebook.title}</h1>
        {notebook.description ? <p className="notebook-lead">{notebook.description}</p> : null}
      </header>
      <CodingNotebook slug={notebook.slug} cells={notebook.cells} />
      {next ? (
        <Link className="lesson-next" href={`/notebooks/${next.slug}`}>
          <span>
            <small>Next lesson</small>
            <strong>{next.title}</strong>
          </span>
          <span className="lesson-go">Next</span>
        </Link>
      ) : (
        <p className="lesson-done">That is the last lesson.</p>
      )}
    </article>
  )
}
