const C = (re, im = 0) => ({ re, im })
const add = (a, b) => C(a.re + b.re, a.im + b.im)
const mul = (a, b) => C(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re)
const abs2 = a => a.re * a.re + a.im * a.im

const ONE_QUBIT = { H: 1, RX: 1, RY: 1, RZ: 1 }
const MULTI = { CNOT: 2, CZ: 2, SWAP: 2, TOFFOLI: 3, CCNOT: 3 }
const KNOWN = { ...ONE_QUBIT, ...MULTI }

const S2 = 1 / Math.sqrt(2)

function parseAngle(token) {
  const t = token.toLowerCase().replace('π', 'pi')
  const named = {
    pi: Math.PI,
    '-pi': -Math.PI,
    'pi/2': Math.PI / 2,
    '-pi/2': -Math.PI / 2,
    'pi/4': Math.PI / 4,
    '-pi/4': -Math.PI / 4
  }
  if (t in named) return named[t]
  const n = Number(t)
  return Number.isFinite(n) ? n : null
}

export function formatAngle(angle) {
  const near = (value) => Math.abs(angle - value) < 1e-6
  if (near(Math.PI)) return 'π'
  if (near(-Math.PI)) return '-π'
  if (near(Math.PI / 2)) return 'π/2'
  if (near(-Math.PI / 2)) return '-π/2'
  if (near(Math.PI / 4)) return 'π/4'
  if (near(-Math.PI / 4)) return '-π/4'
  if (near(0)) return '0'
  return String(Math.round(angle * 1000) / 1000)
}

export function gateLabel(op) {
  if (op.angle == null) return op.name === 'CCNOT' ? 'Toffoli' : op.name
  const name = op.name
  return `${name}(${formatAngle(op.angle)})`
}

export function parseCircuit(spec) {
  const lines = String(spec || '')
    .split(/[\n;]+/)
    .map(line => line.trim())
    .filter(line => line && !line.startsWith('#'))

  if (!lines.length) {
    return { error: 'Add a gate to draw the circuit.', ops: [], qubits: 0 }
  }

  const ops = []
  for (const line of lines) {
    const parts = line.split(/\s+/)
    const rawName = parts[0]
    const name = rawName.toUpperCase()
    if (!KNOWN[name]) {
      return { error: `Unknown gate "${rawName}". Use H, RX, RY, RZ, CNOT, CZ, SWAP, or Toffoli.`, ops: [], qubits: 0 }
    }

    let angle = null
    let qubitTokens = parts.slice(1)
    if (ONE_QUBIT[name] && name !== 'H') {
      if (qubitTokens.length < 2) {
        return { error: `${name} needs an angle and a qubit. Example: ${name} pi/2 0`, ops: [], qubits: 0 }
      }
      angle = parseAngle(qubitTokens[0])
      if (angle == null) {
        return { error: `Could not read the angle "${qubitTokens[0]}". Try pi, pi/2, or a number.`, ops: [], qubits: 0 }
      }
      qubitTokens = qubitTokens.slice(1)
    }

    const qubits = qubitTokens.map(token => Number(token))
    const needed = KNOWN[name]
    if (qubits.length !== needed || qubits.some(q => !Number.isInteger(q) || q < 0)) {
      return {
        error: `${name === 'CCNOT' ? 'Toffoli' : name} needs ${needed} qubit ${needed === 1 ? 'index' : 'indices'}.`,
        ops: [],
        qubits: 0
      }
    }
    if (new Set(qubits).size !== qubits.length) {
      return { error: `${name} cannot use the same qubit twice.`, ops: [], qubits: 0 }
    }
    ops.push({ name: name === 'CCNOT' ? 'TOFFOLI' : name, angle, qubits })
  }

  const qubits = ops.reduce((max, op) => Math.max(max, ...op.qubits), -1) + 1
  if (qubits > 8) {
    return { error: 'Notebooks draw and run up to 8 qubits.', ops: [], qubits: 0 }
  }
  return { error: null, ops, qubits }
}

function realMatrix(rows) {
  return rows.map(row => row.map(value => C(value)))
}

function matrixFor(op) {
  const { name, angle } = op
  if (name === 'H') {
    return realMatrix([
      [S2, S2],
      [S2, -S2]
    ])
  }
  if (name === 'RX') {
    const c = Math.cos(angle / 2)
    const s = Math.sin(angle / 2)
    return [
      [C(c), C(0, -s)],
      [C(0, -s), C(c)]
    ]
  }
  if (name === 'RY') {
    const c = Math.cos(angle / 2)
    const s = Math.sin(angle / 2)
    return realMatrix([
      [c, -s],
      [s, c]
    ])
  }
  if (name === 'RZ') {
    return [
      [C(Math.cos(-angle / 2), Math.sin(-angle / 2)), C(0)],
      [C(0), C(Math.cos(angle / 2), Math.sin(angle / 2))]
    ]
  }
  if (name === 'CNOT') {
    return realMatrix([
      [1, 0, 0, 0],
      [0, 1, 0, 0],
      [0, 0, 0, 1],
      [0, 0, 1, 0]
    ])
  }
  if (name === 'CZ') {
    return realMatrix([
      [1, 0, 0, 0],
      [0, 1, 0, 0],
      [0, 0, 1, 0],
      [0, 0, 0, -1]
    ])
  }
  if (name === 'SWAP') {
    return realMatrix([
      [1, 0, 0, 0],
      [0, 0, 1, 0],
      [0, 1, 0, 0],
      [0, 0, 0, 1]
    ])
  }
  const toffoli = Array.from({ length: 8 }, (_, row) =>
    Array.from({ length: 8 }, (_, col) => (row === col ? 1 : 0))
  )
  toffoli[6][6] = 0
  toffoli[7][7] = 0
  toffoli[6][7] = 1
  toffoli[7][6] = 1
  return realMatrix(toffoli)
}

function applyGate(state, matrix, n, targets) {
  const k = targets.length
  const dim = 1 << n
  const gdim = 1 << k
  const out = Array.from({ length: dim }, () => C(0))
  for (let i = 0; i < dim; i++) {
    if (abs2(state[i]) < 1e-18) continue
    let col = 0
    for (let t = 0; t < k; t++) {
      const bit = (i >> (n - 1 - targets[t])) & 1
      col = (col << 1) | bit
    }
    for (let row = 0; row < gdim; row++) {
      const amp = mul(matrix[row][col], state[i])
      if (abs2(amp) < 1e-18) continue
      let j = i
      for (let t = 0; t < k; t++) {
        const bit = (row >> (k - 1 - t)) & 1
        const shift = n - 1 - targets[t]
        j = (j & ~(1 << shift)) | (bit << shift)
      }
      out[j] = add(out[j], amp)
    }
  }
  return out
}

export function runCircuit(parsed) {
  const n = parsed.qubits
  let state = Array.from({ length: 1 << n }, () => C(0))
  state[0] = C(1)
  for (const op of parsed.ops) {
    state = applyGate(state, matrixFor(op), n, op.qubits)
  }
  const probabilities = state.map(abs2)
  return { probabilities, qubits: n }
}

export function sampleCounts(probabilities, shots, seed) {
  let x = seed >>> 0 || 1
  const next = () => {
    x = (1664525 * x + 1013904223) >>> 0
    return x / 4294967296
  }
  const counts = new Map()
  const n = Math.round(Math.log2(probabilities.length))
  for (let s = 0; s < shots; s++) {
    const roll = next()
    let cursor = 0
    let index = probabilities.length - 1
    for (let i = 0; i < probabilities.length; i++) {
      cursor += probabilities[i]
      if (roll <= cursor) {
        index = i
        break
      }
    }
    const label = index.toString(2).padStart(n, '0')
    counts.set(label, (counts.get(label) || 0) + 1)
  }
  return Object.fromEntries([...counts.entries()].sort(([a], [b]) => a.localeCompare(b)))
}
