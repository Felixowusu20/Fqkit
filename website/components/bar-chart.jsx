export function BarChart({ rows, title = 'Probabilities' }) {
  const values = rows.map(row => row.value)
  const peak = Math.max(...values, 0.001)

  return (
    <figure className="bar-chart">
      <figcaption>{title}</figcaption>
      <div className="bar-chart-plot">
        {rows.map(row => (
          <div className="bar-chart-col" key={row.label}>
            <span className="bar-chart-pct">{row.value >= 0.995 ? '1' : row.value.toFixed(2)}</span>
            <div className="bar-chart-track">
              <div
                className="bar-chart-fill"
                style={{ height: `${Math.max(2, (row.value / peak) * 100)}%` }}
              />
            </div>
            <span className="bar-chart-label">{row.label}</span>
          </div>
        ))}
      </div>
    </figure>
  )
}
