import nextra from 'nextra'

const withNextra = nextra({
  search: {
    codeblocks: false
  },
  latex: { renderer: 'katex', options: {} },
  contentDirBasePath: '/docs'
})
 

export default withNextra({
  reactStrictMode: true,
  allowedDevOrigins: ['127.0.0.1', '172.20.10.3', '10.30.23.21'],
  env: {
    NEXT_PUBLIC_KEYSTATIC_STORAGE: process.env.VERCEL ? 'github' : ''
  }
})

