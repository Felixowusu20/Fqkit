import katex from 'katex'

function renderTex(tex, displayMode) {
  return katex.renderToString(tex || '', {
    displayMode,
    throwOnError: false
  })
}

export function Equation({ tex }) {
  return <div dangerouslySetInnerHTML={{ __html: renderTex(tex, true) }} />
}

export function Math({ tex }) {
  return <span dangerouslySetInnerHTML={{ __html: renderTex(tex, false) }} />
}
