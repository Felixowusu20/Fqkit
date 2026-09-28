export const metadata = {
  title: 'FQkit Docs Admin',
  robots: { index: false, follow: false }
}

export default function AdminLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body style={{ margin: 0 }}>{children}</body>
    </html>
  )
}
