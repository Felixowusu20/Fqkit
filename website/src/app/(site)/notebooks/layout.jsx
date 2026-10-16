import { LessonFrame } from '../../../../components/lesson-sidebar'
import { getNotebooks } from '../../../lib/notebooks'

export const dynamic = 'force-dynamic'

export default async function NotebooksLayout({ children }) {
  const lessons = await getNotebooks()

  return <LessonFrame lessons={lessons}>{children}</LessonFrame>
}
