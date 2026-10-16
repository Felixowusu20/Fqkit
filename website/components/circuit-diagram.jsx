import { formatAngle, gateLabel, parseCircuit } from '../src/lib/circuit.mjs'

const ROW = 64
const COL = 108
const TOP = 40
const LEFT = 72

function wireY(q) {
  return TOP + q * ROW
}

function Plus({ x, y }) {
  return (
    <g className="target-mark">
      <circle className="target" cx={x} cy={y} r={11} />
      <line x1={x - 6} y1={y} x2={x + 6} y2={y} />
      <line x1={x} y1={y - 6} x2={x} y2={y + 6} />
    </g>
  )
}

function Cross({ x, y }) {
  return (
    <g className="target-mark">
      <line x1={x - 6} y1={y - 6} x2={x + 6} y2={y + 6} />
      <line x1={x - 6} y1={y + 6} x2={x + 6} y2={y - 6} />
    </g>
  )
}

function GateSymbol({ op, x }) {
  const ys = op.qubits.map(wireY)
  const yMin = Math.min(...ys)
  const yMax = Math.max(...ys)

  if (op.name === 'CNOT' || op.name === 'TOFFOLI') {
    const target = ys[ys.length - 1]
    return (
      <g>
        <line className="wire" x1={x} y1={yMin} x2={x} y2={yMax} />
        {ys.slice(0, -1).map(y => (
          <g key={y}>
            <circle className="dot-halo" cx={x} cy={y} r={8} />
            <circle className="dot" cx={x} cy={y} r={5} />
          </g>
        ))}
        <Plus x={x} y={target} />
      </g>
    )
  }

  if (op.name === 'CZ') {
    return (
      <g>
        <line className="wire" x1={x} y1={yMin} x2={x} y2={yMax} />
        {ys.map(y => (
          <g key={y}>
            <circle className="dot-halo" cx={x} cy={y} r={8} />
            <circle className="dot" cx={x} cy={y} r={5} />
          </g>
        ))}
      </g>
    )
  }

  if (op.name === 'SWAP') {
    return (
      <g>
        <line className="wire" x1={x} y1={yMin} x2={x} y2={yMax} />
        {ys.map(y => (
          <Cross key={y} x={x} y={y} />
        ))}
      </g>
    )
  }

  const label = op.name === 'H' ? 'H' : `${op.name}(${formatAngle(op.angle)})`
  const boxW = Math.max(52, label.length * 8.4 + 16)
  const y = ys[0]
  return (
    <g>
      <rect className="box" x={x - boxW / 2} y={y - 16} width={boxW} height={32} rx={7} />
      <text className="label" x={x} y={y + 5} textAnchor="middle">
        {label}
      </text>
    </g>
  )
}

export function CircuitDiagram({ spec, caption }) {
  const parsed = parseCircuit(spec)
  if (parsed.error) {
    return <p className="circuit-error">{parsed.error}</p>
  }

  const width = LEFT + parsed.ops.length * COL + 28
  const height = TOP + (parsed.qubits - 1) * ROW + 36

  return (
    <figure className="circuit-figure">
      <svg
        className="circuit-svg"
        viewBox={`0 0 ${width} ${height}`}
        width={width}
        height={height}
        role="img"
        aria-label={caption || gateLabel(parsed.ops[0])}
      >
        <rect className="circuit-panel" x="1" y="1" width={width - 2} height={height - 2} rx="12" />
        {Array.from({ length: parsed.qubits }, (_, q) => {
          const y = wireY(q)
          return (
            <g key={q}>
              <text className="qlabel" x={16} y={y + 4}>
                q{q}
              </text>
              <line className="wire" x1={LEFT - 10} y1={y} x2={width - 22} y2={y} />
              <line className="wire-end" x1={width - 22} y1={y - 7} x2={width - 22} y2={y + 7} />
            </g>
          )
        })}
        {parsed.ops.map((op, index) => (
          <GateSymbol key={index} op={op} x={LEFT + index * COL + COL / 2} />
        ))}
      </svg>
      {caption ? <figcaption className="circuit-caption">{caption}</figcaption> : null}
    </figure>
  )
}
