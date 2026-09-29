import { Layout, Navbar, ThemeSwitch } from 'nextra-theme-docs'
import { FqkitMark } from '../../../components/fqkit-mark'
import { SiteBanner } from '../../../components/site-banner'
import { Head } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'
import 'katex/dist/katex.min.css'
import 'nextra-theme-docs/style.css'
import './site.css'

export const metadata = {
  title: {
    template: '%s | FQkit'
  },
  description:
    'FQkit is a lightweight Python framework for learning quantum circuits.',
  applicationName: 'FQkit'
}

export default async function SiteLayout({ children }) {
  const navbar = (
    <Navbar
      key="navbar"
      logo={
        <div className="fqkit-logo">
          <FqkitMark />
          <b className="fqkit-logo-mark">FQkit</b>
        </div>
      }
    >
      <ThemeSwitch className="fqkit-theme-switch" />
    </Navbar>
  )
  const pageMap = await getPageMap()
  return (
    <html lang="en" dir="ltr" suppressHydrationWarning>
      <Head />
      <body>
        <script
          dangerouslySetInnerHTML={{
            __html:
              'try{if(localStorage.getItem("fqkit-banner"))document.documentElement.setAttribute("data-banner","off")}catch(e){}'
          }}
        />
        <Layout
          banner={
            <SiteBanner key="banner">
              New in v0.1.0  OpenQASM export: run fqkit circuits on real IBM
              hardware
            </SiteBanner>
          }
          navbar={navbar}
          footer={
            <footer key="footer" className="fqkit-footer">
              FQkit © {new Date().getFullYear()}
            </footer>
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
