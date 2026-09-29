import { useMDXComponents as getDocsMDXComponents } from 'nextra-theme-docs'
import { Callout } from './components/callout'
import { CircuitDiagram as Circuit } from './components/circuit-diagram'
import { Equation, Math } from './components/equation'

const docsComponents = getDocsMDXComponents({ Callout, Equation, Math, Circuit })

export const useMDXComponents = components => ({
  ...docsComponents,
  ...components
})
