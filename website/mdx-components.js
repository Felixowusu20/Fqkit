import { useMDXComponents as getDocsMDXComponents } from 'nextra-theme-docs'
import { Callout } from './components/callout'

const docsComponents = getDocsMDXComponents({ Callout })

export const useMDXComponents = components => ({
  ...docsComponents,
  ...components
})
