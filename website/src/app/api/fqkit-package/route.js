import { access, readdir, readFile } from 'fs/promises'
import path from 'path'

export const dynamic = 'force-dynamic'

async function findPackageRoot() {
  const candidates = [
    path.resolve(process.cwd(), '..', 'fqkit'),
    path.resolve(process.cwd(), 'fqkit')
  ]
  for (const dir of candidates) {
    try {
      await access(path.join(dir, '__init__.py'))
      return dir
    } catch {
      // try the next location
    }
  }
  throw new Error('Could not find the fqkit package next to the website.')
}

async function walk(dir, rel, out) {
  const entries = await readdir(dir, { withFileTypes: true })
  for (const entry of entries) {
    if (entry.name === '__pycache__' || entry.name.startsWith('.')) continue
    const full = path.join(dir, entry.name)
    const next = `${rel}/${entry.name}`
    if (entry.isDirectory()) await walk(full, next, out)
    else if (entry.name.endsWith('.py')) out[next] = await readFile(full, 'utf8')
  }
}

export async function GET() {
  const root = await findPackageRoot()
  const files = {}
  await walk(root, 'fqkit', files)
  return Response.json(files)
}
