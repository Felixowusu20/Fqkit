'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState } from 'react'

export function LessonFrame({ lessons, children }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className={collapsed ? 'lesson-shell is-collapsed' : 'lesson-shell'}>
      <LessonSidebar
        lessons={lessons}
        collapsed={collapsed}
        onToggle={() => setCollapsed(value => !value)}
      />
      <div className="lesson-main">{children}</div>
    </div>
  )
}

function LessonSidebar({ lessons, collapsed, onToggle }) {
  const pathname = usePathname()

  return (
    <aside className="lesson-sidebar">
      <div className="lesson-sidebar-head">
        <p className="lesson-sidebar-label">Lessons</p>
        <button
          type="button"
          className="lesson-collapse"
          aria-expanded={!collapsed}
          aria-label={collapsed ? 'Show lessons' : 'Hide lessons'}
          onClick={onToggle}
        >
          <span className="lesson-collapse-mark" aria-hidden="true">
            {collapsed ? '›' : '‹'}
          </span>
          {collapsed ? null : <span>Hide</span>}
        </button>
      </div>
      {lessons.length === 0 ? (
        <p className="lesson-sidebar-empty">No lessons yet.</p>
      ) : (
        <nav id="lesson-nav" aria-label="Lessons">
          <ol>
            {lessons.map((lesson, index) => {
              const href = `/notebooks/${lesson.slug}`
              const current = pathname === href
              return (
                <li key={lesson.slug}>
                  <Link href={href} aria-current={current ? 'page' : undefined} title={lesson.title}>
                    <span className="lesson-num">{index + 1}</span>
                    <strong>{lesson.title}</strong>
                  </Link>
                </li>
              )
            })}
          </ol>
        </nav>
      )}
    </aside>
  )
}
