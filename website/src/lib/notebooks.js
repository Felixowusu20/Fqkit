import { createReader } from '@keystatic/core/reader'
import keystaticConfig from '../../keystatic.config.mjs'

const reader = createReader(process.cwd(), keystaticConfig)

function shape(slug, entry) {
  return {
    slug,
    title: entry.title,
    description: entry.description || '',
    cells: (entry.cells || []).map(cell => ({
      kind: cell.kind === 'markdown' ? 'markdown' : 'code',
      source: cell.source || ''
    })),
    order: entry.order ?? 0
  }
}

export async function getNotebooks() {
  const all = await reader.collections.notebooks.all()
  return all
    .map(({ slug, entry }) => shape(slug, entry))
    .sort((a, b) => a.order - b.order || a.title.localeCompare(b.title))
}

export async function getNotebook(slug) {
  const entry = await reader.collections.notebooks.read(slug)
  if (!entry) return null
  return shape(slug, entry)
}
