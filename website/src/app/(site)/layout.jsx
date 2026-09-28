import { Footer, Layout, Navbar } from 'nextra-theme-docs'
import { Banner, Head } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import 'nextra-theme-docs/style.css'
import './site.css'

export const metadata = {
  title: {
    template: '%s – FQkit'
  },
  description:
    'FQkit — a lightweight quantum circuit framework for learning and simulation, built for Africa and the world.',
  applicationName: 'FQkit'
}

export default async function SiteLayout({ children }) {
  const navbar = (
    <Navbar
      logo={
        <div className="fqkit-logo">
          <b className="fqkit-logo-mark">⚛ FQkit</b>
          <span className="fqkit-logo-tagline">
            quantum framework for Quantum Enthusiasts&amp;
          </span>
        </div>
      }
    />
  )
  const pageMap = await getPageMap()
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <Head faviconGlyph="⚛" />
      <body>
        <Layout
          banner={
            <Banner storageKey="fqkit-banner">
              New in v0.1.0  OpenQASM export: run fqkit circuits on real IBM
              hardware
            </Banner>
          }
          navbar={navbar}
          footer={
            <Footer>
              FQkit For Quantum Enthusiast. © {new Date().getFullYear()}
            </Footer>
          }
          editLink="Edit this page on GitHub"
          docsRepositoryBase="https://github.com/Felixowusu20/Fqkit/tree/main/website"
          sidebar={{ defaultMenuCollapseLevel: 1 }}
          pageMap={pageMap}
        >
          {children}
        </Layout>
      </body>
    </html>
  )
}
