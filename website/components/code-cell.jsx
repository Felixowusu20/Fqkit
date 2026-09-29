'use client'

import { useEffect, useRef } from 'react'
import { autocompletion, closeBrackets, closeBracketsKeymap, completionKeymap } from '@codemirror/autocomplete'
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands'
import { python, pythonLanguage } from '@codemirror/lang-python'
import { bracketMatching, defaultHighlightStyle, indentOnInput, syntaxHighlighting } from '@codemirror/language'
import { EditorState } from '@codemirror/state'
import { EditorView, keymap, lineNumbers } from '@codemirror/view'

const GLOBAL = [
  ['QuantumCircuit', 'class', 'QuantumCircuit(n) makes an n-qubit circuit'],
  ['Hadamard', 'function', 'Hadamard gate. Hadamard()'],
  ['RX', 'function', 'X rotation. RX(angle)'],
  ['RY', 'function', 'Y rotation. RY(angle)'],
  ['RZ', 'function', 'Z rotation. RZ(angle)'],
  ['CNOT', 'function', 'Controlled NOT. CNOT()'],
  ['CZ', 'function', 'Controlled Z. CZ()'],
  ['SWAP', 'function', 'Swap two qubits. SWAP()'],
  ['Toffoli', 'function', 'Controlled-controlled NOT. Toffoli()'],
  ['run', 'function', 'run(qc) returns the state vector'],
  ['measure_all', 'function', 'measure_all(state, shots=1024)'],
  ['show', 'function', 'show(qc) draws the circuit'],
  ['plot', 'function', 'plot(state) draws probability bars'],
  ['bind_parameters', 'function', 'bind_parameters(qc, {"name": value})'],
  ['Parameter', 'class', 'Parameter("theta") is a symbolic angle'],
  ['Gate', 'class', 'Build a gate from a unitary matrix'],
  ['Qubit', 'class', 'Qubit(index)'],
  ['np', 'namespace', 'NumPy, already used as np'],
  ['math', 'namespace', 'Python math. math.pi is a half turn times two']
].map(([label, type, info]) => ({ label, type, info, detail: 'fqkit' }))

const AFTER_DOT = {
  qc: [
    ['add_gate', 'method', 'qc.add_gate(gate, [qubits])'],
    ['to_qasm', 'method', 'qc.to_qasm() exports OpenQASM'],
    ['num_qubits', 'property', 'How many qubits the circuit has'],
    ['operations', 'property', 'The gates in order'],
    ['qubits', 'property', 'The qubit objects']
  ],
  np: [
    ['abs', 'function', 'np.abs(state)'],
    ['round', 'function', 'np.round(values, 4)'],
    ['array', 'function', 'np.array([...])'],
    ['set_printoptions', 'function', 'np.set_printoptions(precision=4, suppress=True)'],
    ['sqrt', 'function', 'np.sqrt(x)'],
    ['pi', 'constant', 'np.pi']
  ],
  math: [
    ['pi', 'constant', 'math.pi'],
    ['sqrt', 'function', 'math.sqrt(x)'],
    ['sin', 'function', 'math.sin(x)'],
    ['cos', 'function', 'math.cos(x)']
  ]
}

function asOptions(rows) {
  return rows.map(([label, type, info]) => ({ label, type, info }))
}

const DOT_OPTIONS = Object.fromEntries(
  Object.entries(AFTER_DOT).map(([key, rows]) => [key, asOptions(rows)])
)

function fqkitComplete(context) {
  const dotted = context.matchBefore(/\w+\.\w*/)
  if (dotted) {
    const match = /(\w+)\.(\w*)$/.exec(dotted.text)
    const head = match[1]
    const partial = match[2]
    const pool = DOT_OPTIONS[head] || DOT_OPTIONS.qc
    const options = pool.filter(option => option.label.toLowerCase().startsWith(partial.toLowerCase()))
    if (!options.length && !context.explicit) return null
    return { from: dotted.to - partial.length, options, validFor: /^\w*$/ }
  }

  const word = context.matchBefore(/\w*/)
  if (!word || (word.from === word.to && !context.explicit)) return null
  const options = GLOBAL.filter(option => option.label.toLowerCase().startsWith(word.text.toLowerCase()))
  if (!options.length && !context.explicit) return null
  return { from: word.from, options, validFor: /^\w*$/ }
}

const fqkitSource = pythonLanguage.data.of({ autocomplete: fqkitComplete })

function extensions(onChangeRef, onRunRef) {
  return [
    lineNumbers(),
    history(),
    indentOnInput(),
    bracketMatching(),
    closeBrackets(),
    python(),
    fqkitSource,
    syntaxHighlighting(defaultHighlightStyle, { fallback: true }),
    autocompletion({ activateOnTyping: true, maxRenderedOptions: 12 }),
    keymap.of([
      ...closeBracketsKeymap,
      ...completionKeymap,
      { key: 'Shift-Enter', run: () => { onRunRef.current(); return true } },
      { key: 'Mod-Enter', run: () => { onRunRef.current(); return true } },
      indentWithTab,
      ...defaultKeymap,
      ...historyKeymap
    ]),
    EditorView.lineWrapping,
    EditorView.updateListener.of(update => {
      if (update.docChanged) onChangeRef.current(update.state.doc.toString())
    }),
    EditorView.theme({
      '&': { background: 'transparent', color: 'var(--colab-ink)' },
      '.cm-content': {
        fontFamily: '"Roboto Mono", ui-monospace, SFMono-Regular, Menlo, monospace',
        fontSize: '13.5px',
        padding: '10px 0 12px',
        caretColor: 'var(--colab-ink)'
      },
      '.cm-gutters': {
        background: 'transparent',
        color: 'var(--colab-muted)',
        border: 'none'
      },
      '.cm-activeLine': { background: 'transparent' },
      '.cm-activeLineGutter': { background: 'transparent' },
      '&.cm-focused': { outline: 'none' },
      '.cm-scroller': { overflow: 'auto' }
    })
  ]
}

export function CodeCell({ cellId, value, onChange, onRun, label }) {
  const hostRef = useRef(null)
  const onChangeRef = useRef(onChange)
  const onRunRef = useRef(onRun)
  onChangeRef.current = onChange
  onRunRef.current = onRun

  useEffect(() => {
    const view = new EditorView({
      parent: hostRef.current,
      state: EditorState.create({
        doc: value,
        extensions: extensions(onChangeRef, onRunRef)
      })
    })
    return () => view.destroy()
    // A new cell id gets a fresh editor. Typing updates the parent without rebuilding it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cellId])

  return <div ref={hostRef} className="colab-cm" aria-label={label} />
}
