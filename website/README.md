# FQkit Website

The documentation website for [FQkit](https://github.com/Felixowusu20/Fqkit) —
built with [Next.js](https://nextjs.org) and
[Nextra 4](https://nextra.site) (docs theme). Free and open source, and it can
be hosted for **$0** on Vercel's free (Hobby) tier.

## Local development

Requires Node.js 18.18 or newer.

```bash
cd website
npm install
npm run dev
```

Open http://localhost:3000 (or the port printed in the terminal). The site
reloads as you edit files.

> **Note:** search is powered by [Pagefind](https://pagefind.app), which indexes
> the site *after* a production build. In `npm run dev` the search box is
> present but has no index yet. To try search locally, run `npm run build` once.

## Project structure

```
website/
  next.config.mjs           # Nextra config (content dir served at /docs)
  mdx-components.js         # Registers MDX components (e.g. Callout)
  package.json
  src/
    app/
      _meta.js                # Top navigation order (shared)
      (site)/                 # Public site — Nextra chrome, statically rendered
        layout.jsx            # Root layout: navbar, banner, footer, sidebar
        page.jsx              # Landing page (hero)
        docs/
          [[...mdxPath]]/
            page.jsx          # Catch-all route that renders every docs page
      (admin)/                # Admin area — bare root layout, no docs chrome
        layout.jsx
        keystatic/
          [[...params]]/
            page.jsx          # Keystatic CMS UI (/keystatic)
            keystatic-app.jsx
      api/
        keystatic/
          [...params]/
            route.js          # Keystatic read/write API (local mode)
    content/
      _meta.js              # Sidebar order and titles
      index.mdx             # Introduction
      installation.mdx
      quick-start.mdx
      gates.mdx
      circuits.mdx
      simulation-and-measurement.mdx
      parameters.mdx
      openqasm.mdx
      api.mdx
      tutorials/            # Step-by-step lessons (math + code + output)
        _meta.js
        index.mdx
        bell-state-lesson.mdx
  keystatic.config.mjs      # Admin panel content model (git-backed, no DB)
  components/
    callout.jsx             # Server-safe Callout used inside MDX
```

Documentation lives in `src/content/*.mdx` as Markdown with JSX. Add a new page
by creating an `.mdx` file there and listing it in `src/content/_meta.js`.

## Scripts

| Script | Purpose |
| --- | --- |
| `npm run dev` | Start the dev server with hot reload |
| `npm run build` | Production build (then indexes search via `postbuild`) |
| `npm run start` | Serve the production build locally |

## Deploy for free on Vercel

Vercel's **Hobby** plan is free and is the native host for Next.js.

1. Push this repository to GitHub (already done).
2. Go to https://vercel.com and sign in with GitHub (free account).
3. Click **Add New… → Project**, then **Import** the `Fqkit` repository.
4. Set the **Root Directory** to `website` (so Vercel builds this folder).
5. Vercel auto-detects the Next.js framework — leave the build settings as-is:
   - Build command: `npm run build` (the `postbuild` Pagefind step runs
     automatically and generates the search index).
   - Output directory: `.next`.
6. Click **Deploy**. You'll get a free `*.vercel.app` URL in about a minute.

Every push to the repository triggers a new free deployment, and pull requests
get their own free preview URLs.

## Admin panel (Keystatic)

The site ships with a clean, git-backed CMS at **`/keystatic`** so you (or other
scholars) can add and edit docs and tutorials through a visual editor — code,
output, explanations, and even KaTeX math — without touching Markdown by hand.
There is **no database**: content is stored as the same `.mdx` files in the repo,
so every edit is a normal git commit. Costs **$0**.

Run the dev server and open:

```
http://localhost:3000/keystatic
```

Two collections are configured in `keystatic.config.mjs`:

- **Docs** → `src/content/*.mdx`
- **Tutorials** → `src/content/tutorials/*.mdx`

Each entry has a title, description, and an MDX body. Saving writes the file to
disk; commit and push to publish.

### Letting scholars edit from anywhere (still free)

Local mode (the default) only works on your own machine. To let scholars edit
through a public URL, switch Keystatic to **GitHub mode** and deploy — all free:

1. **Deploy the site to Vercel** (Hobby tier, free) using the steps above.
2. **Create a free GitHub OAuth app** (GitHub → Settings → Developer settings →
   OAuth Apps). Set the callback URL to
   `https://<your-site>.vercel.app/api/keystatic/github/oauth`. Note the client
   ID and generate a client secret.
3. **Set `storage: { kind: 'github', repo: 'Felixowusu20/Fqkit' }`** in
   `keystatic.config.mjs`, and add the `KEYSTATIC_GITHUB_CLIENT_ID` /
   `KEYSTATIC_GITHUB_CLIENT_SECRET` env vars in Vercel (free).
4. **Add scholars as repository collaborators** (free for public repos). They
   sign in at `/keystatic` with their GitHub account; edits become commits /
   pull requests on the repo, which Vercel redeploys automatically.

No paid services, no database, no hosting fees.

## Notes

- The app uses **two root layouts** via route groups: `(site)` carries the
  Nextra chrome and is statically rendered (so Pagefind search works), while
  `(admin)` is a bare root for the Keystatic CMS. Keep `src/app/_meta.js` at the
  app root — Nextra strips route-group segments from page paths but *not* from
  `_meta` paths, so a `_meta.js` placed inside `(site)` would fail to match its
  pages. Only list real content pages in `_meta.js`; the `(admin)` routes are
  not part of the Nextra page map and must not be referenced there.
- `zod` is pinned via the `overrides` field in `package.json` (`~4.1.12`).
  Nextra 4.6.1 declares `zod@^4.1.12`, but newer 4.x releases changed
  `z.custom()` to reject `undefined`, which breaks Nextra's layout prop
  validation. The pin keeps the site building; remove it once Nextra supports
  the newer zod.
