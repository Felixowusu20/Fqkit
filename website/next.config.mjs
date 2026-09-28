import nextra from 'nextra'

const withNextra = nextra({
  search: {
    codeblocks: false
  },
  latex: { renderer: 'katex', options: {} },
  contentDirBasePath: '/docs'
})

export default withNextra({
  reactStrictMode: true
})
