import { useMDXComponents as getDocsMDXComponents } from 'nextra-theme-docs'
import { Callout } from './components/callout'
import { CircuitDiagram as Circuit } from './components/circuit-diagram'
import { Equation, Math } from './components/equation'
import { Image } from './components/media-image'
import { Video } from './components/media-video'

const docsComponents = getDocsMDXComponents({
  Callout,
  Equation,
  Math,
  Circuit,
  Image,
  Video
})

export const useMDXComponents = components => ({
  ...docsComponents,
  ...components
})
