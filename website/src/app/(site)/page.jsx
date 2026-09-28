const btnBase = {
  display: 'inline-block',
  padding: '11px 22px',
  borderRadius: 10,
  fontSize: 15,
  fontWeight: 600,
  textDecoration: 'none'
}

export default function HomePage() {
  return (
    <div
      style={{
        maxWidth: 780,
        margin: '0 auto',
        padding: '15vh 24px 10vh',
        textAlign: 'center'
      }}
    >
      <div style={{ fontSize: 60, lineHeight: 1, marginBottom: 16 }}>⚛</div>
      <h1
        style={{
          fontSize: 60,
          fontWeight: 800,
          letterSpacing: '-0.03em',
          margin: '0 0 14px'
        }}
      >
        FQkit
      </h1>
      <p
        style={{
          fontSize: 20,
          opacity: 0.72,
          margin: '0 auto 34px',
          lineHeight: 1.55,
          maxWidth: 620
        }}
      >
        A lightweight quantum circuit framework for learning and simulation —
        built for Africa and the world.
      </p>
      <div
        style={{
          display: 'flex',
          gap: 12,
          justifyContent: 'center',
          flexWrap: 'wrap'
        }}
      >
        <a href="/docs" style={{ ...btnBase, background: '#2f6feb', color: '#fff' }}>
          Get started →
        </a>
        <a
          href="https://github.com/Felixowusu20/Fqkit"
          style={{
            ...btnBase,
            border: '1px solid rgba(125,125,125,0.4)',
            color: 'inherit'
          }}
        >
          GitHub
        </a>
      </div>
      <p style={{ marginTop: 48, opacity: 0.5, fontSize: 14 }}>
        Free &amp; open source · Pure Python + NumPy · Exports to OpenQASM
      </p>
    </div>
  )
}
