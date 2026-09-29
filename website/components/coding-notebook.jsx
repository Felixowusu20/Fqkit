'use client'

import { useEffect, useRef, useState } from 'react'
import { BarChart } from './bar-chart'
import { CircuitDiagram } from './circuit-diagram'
import { CodeCell } from './code-cell'

const INDEX_URL = 'https://cdn.jsdelivr.net/pyodide/v0.28.2/full/'

const BOOTSTRAP = `
import math

def show(circuit):
    lines = []
    for op in circuit.operations:
        qubits = " ".join(str(int(q)) for q in op.qubits)
        params = list(op.gate.params or [])
        if params:
            lines.append(op.gate.name + " " + str(float(params[0])) + " " + qubits)
        else:
            lines.append(op.gate.name + " " + qubits)
    print("@@CIRCUIT@@")
    print("\\n".join(lines))
    print("@@END@@")

def plot(state):
    import numpy as np
    probs = np.abs(np.asarray(state, dtype=complex)) ** 2
    n = int(round(np.log2(len(probs)))) if len(probs) else 0
    print("@@BARS@@")
    for i, value in enumerate(probs):
        value = float(value)
        if n > 3 and value < 1e-4:
            continue
        label = format(i, "0" + str(max(n, 1)) + "b")
        print(label + " " + format(value, ".6f"))
    print("@@END@@")
`

let runtimePromise = null

function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (window.loadPyodide) {
      resolve()
      return
    }
    const existing = document.querySelector(`script[src="${src}"]`)
    if (existing) {
      existing.addEventListener('load', () => resolve())
      existing.addEventListener('error', () => reject(new Error('Could not download Python.')))
      return
    }
    const script = document.createElement('script')
    script.src = src
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Could not download Python.'))
    document.head.appendChild(script)
  })
}

function ensureDir(fs, dir) {
  const parts = dir.split('/').filter(Boolean)
  let current = ''
  for (const part of parts) {
    current += `/${part}`
    try {
      fs.mkdir(current)
    } catch {
      // The directory already exists.
    }
  }
}

async function getRuntime(onStatus) {
  if (!runtimePromise) {
    runtimePromise = (async () => {
      onStatus('Downloading Python. The first run takes a moment.')
      await loadScript(`${INDEX_URL}pyodide.js`)
      const chunks = []
      const pyodide = await window.loadPyodide({
        indexURL: INDEX_URL,
        stdout: text => chunks.push(text),
        stderr: text => chunks.push(text)
      })
      pyodide._fqChunks = chunks
      onStatus('Loading NumPy and FQkit.')
      await pyodide.loadPackage('numpy')
      const response = await fetch('/api/fqkit-package')
      if (!response.ok) throw new Error('Could not load the FQkit package.')
      const files = await response.json()
      for (const [filePath, source] of Object.entries(files)) {
        ensureDir(pyodide.FS, `/${filePath.split('/').slice(0, -1).join('/')}`)
        pyodide.FS.writeFile(`/${filePath}`, source)
      }
      await pyodide.runPythonAsync('import sys\nsys.path.insert(0, "/")\n')
      return pyodide
    })()
    runtimePromise.catch(() => {
      runtimePromise = null
    })
  }
  return runtimePromise
}

async function resetNamespace(pyodide) {
  pyodide.globals.set('_bootstrap', BOOTSTRAP)
  await pyodide.runPythonAsync(`
_ns = {"__name__": "__main__"}
exec(compile(_bootstrap, "<bootstrap>", "exec"), _ns)
del _bootstrap
`)
}

function joinChunks(chunks) {
  return chunks
    .map(chunk => (chunk.endsWith('\n') ? chunk : `${chunk}\n`))
    .join('')
    .replace(/\n+$/, '')
}

function MarkdownView({ source }) {
  const blocks = String(source || '').trim().split(/\n\s*\n/).filter(Boolean)
  return blocks.map((block, index) => {
    const lines = block.split('\n')
    if (lines[0].startsWith('### ')) return <h3 key={index}>{lines[0].slice(4)}</h3>
    if (lines[0].startsWith('## ')) return <h2 key={index}>{lines[0].slice(3)}</h2>
    if (lines.every(line => line.trim().startsWith('- '))) {
      return (
        <ul key={index}>
          {lines.map(line => (
            <li key={line}>{line.trim().slice(2)}</li>
          ))}
        </ul>
      )
    }
    const html = block
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
    return <p key={index} dangerouslySetInnerHTML={{ __html: html }} />
  })
}

function parseOutput(text) {
  const parts = []
  const pattern = /@@(CIRCUIT|BARS)@@\n?([\s\S]*?)@@END@@/g
  let last = 0
  let match = pattern.exec(text)
  while (match) {
    if (match.index > last) parts.push({ type: 'text', value: text.slice(last, match.index) })
    if (match[1] === 'CIRCUIT') parts.push({ type: 'circuit', value: match[2].trim() })
    else {
      const rows = match[2]
        .trim()
        .split('\n')
        .filter(Boolean)
        .map(line => {
          const [label, raw] = line.trim().split(/\s+/)
          return { label, value: Number(raw) }
        })
        .filter(row => Number.isFinite(row.value))
      parts.push({ type: 'bars', rows })
    }
    last = match.index + match[0].length
    match = pattern.exec(text)
  }
  if (last < text.length) parts.push({ type: 'text', value: text.slice(last) })
  return parts
}

function CellOutput({ output }) {
  if (!output || (!output.text && !output.error)) return null
  const parts = parseOutput(output.text || '')
  return (
    <div className={output.error ? 'colab-output colab-output-error' : 'colab-output'}>
      {parts.map((part, index) => {
        if (part.type === 'circuit') return <CircuitDiagram key={index} spec={part.value} />
        if (part.type === 'bars') return <BarChart key={index} rows={part.rows} />
        const text = part.value.replace(/^\n+|\n+$/g, '')
        return text ? <pre key={index}>{text}</pre> : null
      })}
      {output.error ? <pre className="colab-traceback">{output.error}</pre> : null}
    </div>
  )
}

function InsertBar({ onCode, onText }) {
  return (
    <div className="colab-insert">
      <span className="colab-insert-line" />
      <span className="colab-insert-actions">
        <button type="button" onClick={onCode}>+ Code</button>
        <button type="button" onClick={onText}>+ Text</button>
      </span>
    </div>
  )
}

function ToolIcon({ children }) {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      {children}
    </svg>
  )
}

let added = 0

function newId() {
  added += 1
  return `added-${added}`
}

export function CodingNotebook({ slug, cells: initialCells }) {
  const [cells, setCells] = useState(() =>
    (initialCells || []).map(cell => ({ ...cell, id: newId() }))
  )
  const [outputs, setOutputs] = useState({})
  const [editing, setEditing] = useState({})
  const [status, setStatus] = useState('Python starts when you run a cell.')
  const [busy, setBusy] = useState(false)
  const kernel = useRef(null)
  const queue = useRef(Promise.resolve())
  const slugRef = useRef(slug)

  const incoming = JSON.stringify(initialCells || [])
  useEffect(() => {
    slugRef.current = slug
    setCells(JSON.parse(incoming).map(cell => ({ ...cell, id: newId() })))
    setOutputs({})
    setEditing({})
    kernel.current = null
  }, [slug, incoming])

  async function ensureKernel() {
    const pyodide = await getRuntime(setStatus)
    if (kernel.current !== pyodide || kernel.current._fqSlug !== slugRef.current) {
      await resetNamespace(pyodide)
      pyodide._fqSlug = slugRef.current
      kernel.current = pyodide
      setStatus('Python is ready. Cells share one session, so a later cell can use names from an earlier one.')
    }
    return pyodide
  }

  function enqueue(task) {
    const run = queue.current.then(task, task)
    queue.current = run.then(() => {}, () => {})
    return run
  }

  function runCell(index) {
    return enqueue(async () => {
      const cell = cellsRef.current[index]
      if (!cell || cell.kind !== 'code') return
      setBusy(true)
      setOutputs(current => ({ ...current, [cell.id]: { text: '', error: '', running: true } }))
      const chunks = []
      try {
        const pyodide = await ensureKernel()
        pyodide._fqChunks = chunks
        pyodide.setStdout({ batched: text => chunks.push(text) })
        pyodide.setStderr({ batched: text => chunks.push(text) })
        pyodide.globals.set('_cell', cell.source)
        await pyodide.runPythonAsync('exec(compile(_cell, "<cell>", "exec"), _ns)')
        setOutputs(current => ({
          ...current,
          [cell.id]: { text: joinChunks(chunks), error: '', running: false }
        }))
      } catch (error) {
        const message = String(error?.message || error)
        setOutputs(current => ({
          ...current,
          [cell.id]: { text: joinChunks(chunks), error: message, running: false }
        }))
        setStatus('That cell raised an error. Fix it and run it again.')
      } finally {
        setBusy(false)
      }
    })
  }

  const cellsRef = useRef(cells)
  cellsRef.current = cells

  function updateSource(id, source) {
    setCells(current => current.map(cell => (cell.id === id ? { ...cell, source } : cell)))
  }

  function insertAt(index, kind) {
    const cell = {
      id: newId(),
      kind,
      source: kind === 'code' ? '' : ''
    }
    setCells(current => [...current.slice(0, index), cell, ...current.slice(index)])
    if (kind === 'markdown') setEditing(current => ({ ...current, [cell.id]: true }))
  }

  function moveCell(index, direction) {
    setCells(current => {
      const target = index + direction
      if (target < 0 || target >= current.length) return current
      const next = current.slice()
      const [item] = next.splice(index, 1)
      next.splice(target, 0, item)
      return next
    })
  }

  function removeCell(id) {
    setCells(current => current.filter(cell => cell.id !== id))
  }

  async function runAll() {
    for (let index = 0; index < cellsRef.current.length; index += 1) {
      if (cellsRef.current[index].kind === 'code') await runCell(index)
    }
  }

  let codeCount = 0

  return (
    <div className="colab-sheet">
      <div className="colab-bar">
        <button type="button" className="colab-runall" onClick={runAll} disabled={busy}>
          Run all
        </button>
        <p>{status}</p>
      </div>
      <InsertBar onCode={() => insertAt(0, 'code')} onText={() => insertAt(0, 'markdown')} />
      {cells.map((cell, index) => {
        const isCode = cell.kind === 'code'
        if (isCode) codeCount += 1
        const running = outputs[cell.id]?.running
        const ran = outputs[cell.id] && !running
        const prompt = running ? '*' : ran ? codeCount : ' '
        return (
          <div key={cell.id}>
            <section className={isCode ? 'colab-row colab-row-code' : 'colab-row'}>
              <div className="colab-gutter">
                {isCode ? (
                  <button
                    type="button"
                    className="colab-play"
                    aria-label={`Run cell ${codeCount}`}
                    disabled={busy}
                    onClick={() => runCell(index)}
                  >
                    {running ? '…' : '▶'}
                  </button>
                ) : null}
                {isCode ? <span className="colab-prompt">[{prompt}]</span> : null}
              </div>
              <div className="colab-card">
                <div className="colab-tools">
                  <button type="button" aria-label="Move cell up" title="Move cell up" disabled={index === 0} onClick={() => moveCell(index, -1)}>
                    <ToolIcon><path d="M6 14l6-6 6 6" fill="none" stroke="currentColor" strokeWidth="2" /></ToolIcon>
                  </button>
                  <button type="button" aria-label="Move cell down" title="Move cell down" disabled={index === cells.length - 1} onClick={() => moveCell(index, 1)}>
                    <ToolIcon><path d="M6 10l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="2" /></ToolIcon>
                  </button>
                  <button type="button" aria-label="Add code cell above" title="Add code cell above" onClick={() => insertAt(index, 'code')}>
                    + Code
                  </button>
                  <button type="button" aria-label="Add text cell above" title="Add text cell above" onClick={() => insertAt(index, 'markdown')}>
                    + Text
                  </button>
                  {!isCode ? (
                    <button type="button" onClick={() => setEditing(current => ({ ...current, [cell.id]: !current[cell.id] }))}>
                      {editing[cell.id] ? 'Done' : 'Edit'}
                    </button>
                  ) : null}
                  <button type="button" aria-label="Delete cell" title="Delete cell" onClick={() => removeCell(cell.id)}>
                    <ToolIcon><path d="M8 7h8M9 7V5h6v2M7 9h10l-1 11H8L7 9z" fill="none" stroke="currentColor" strokeWidth="1.7" /></ToolIcon>
                  </button>
                </div>
                {isCode ? (
                  <CodeCell
                    cellId={cell.id}
                    value={cell.source}
                    label={`Python cell ${codeCount}`}
                    onChange={source => updateSource(cell.id, source)}
                    onRun={() => runCell(index)}
                  />
                ) : editing[cell.id] ? (
                  <textarea
                    className="colab-text-editor"
                    value={cell.source}
                    aria-label="Text cell"
                    onChange={event => updateSource(cell.id, event.target.value)}
                  />
                ) : (
                  <div className="colab-markdown" onDoubleClick={() => setEditing(current => ({ ...current, [cell.id]: true }))}>
                    <MarkdownView source={cell.source} />
                  </div>
                )}
                {isCode ? <CellOutput output={outputs[cell.id]} /> : null}
              </div>
            </section>
            <InsertBar onCode={() => insertAt(index + 1, 'code')} onText={() => insertAt(index + 1, 'markdown')} />
          </div>
        )
      })}
    </div>
  )
}
