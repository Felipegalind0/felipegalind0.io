# fg.io — bento grid personal dashboard

A minimal, zero-JavaScript personal dashboard built with [Astro](https://astro.build). Pure CSS, system-theme-aware (light/dark), deployed as a static site to GitHub Pages.

**Live:** [felipegalind0.io](https://felipegalind0.io)

---

## Layout

```
┌──────────────────┬────────────┬────────────┐
│                  │ INPUT      │ CORRUPT    │
│  STATUS (bio)    │ _STREAM    │ _DATA      │
│  [A]             │ [B]        │ [D]        │
│                  ├────────────┴────────────┤
│                  │ GITHUB_STATS            │
│                  │ [C]                     │
├──────────────────┴─────────────────────────┤
│ RECENT_COMMITS [E]                         │
└────────────────────────────────────────────┘
```

On mobile, cells stack vertically in source order: A → C → B → D → E.

---

## Project Structure

```
fg-io/
├── public/
│   └── CNAME                    # Custom domain for GitHub Pages
├── scripts/
│   └── inject-size.mjs          # Post-build: logs page size in KB
├── src/
│   ├── components/
│   │   ├── StatusCard.astro     # Widget [A]: bio, avatar, accomplishments
│   │   └── GithubStats.astro    # Widget [C]: GitHub stats SVG image
│   ├── layouts/
│   │   └── Layout.astro         # HTML shell, global reset, scanline overlay
│   ├── pages/
│   │   └── index.astro          # Bento grid layout with 5 cells
│   ├── styles/
│   │   └── tokens.css           # CSS custom properties (design tokens)
│   └── config.ts                # VERSION constant
├── astro.config.mjs             # Astro config (site URL)
├── package.json
└── tsconfig.json
```

---

## Architecture

### Design Tokens (`src/styles/tokens.css`)

All theming is driven by CSS custom properties. Dark mode is the default; light mode activates via `@media (prefers-color-scheme: light)`.

| Token          | Dark             | Light           | Purpose                      |
|:---------------|:-----------------|:----------------|:-----------------------------|
| `--bg`         | `#050505`        | `#f5f5f5`       | Page background              |
| `--fg`         | `#e0e0e0`        | `#111`          | Primary text                 |
| `--fg-dim`     | `#333`           | `#ccc`          | Cell borders, muted elements |
| `--alert`      | `#FF003C`        | `#FF003C`       | Accent / alert color         |
| `--cell-min`   | `280px`          | `280px`         | Min cell width on mobile     |
| `--gap`        | `6px`            | `6px`           | Grid gap                     |
| `--radius`     | `2px`            | `2px`           | Border radius                |
| `--font-mono`  | `"Anonymous Pro"` | same           | Monospace font (slashed 0)   |

### Layout (`src/layouts/Layout.astro`)

- Loads **Anonymous Pro** from Google Fonts (slashed zeros on all devices)
- Global box-sizing reset
- `font-feature-settings: "zero"` as fallback for slashed zeros
- Scanline overlay via `body::after` (subtle CRT effect, disabled on touch devices)
- On desktop (768px+): viewport-locked (`overflow: hidden; height: 100dvh`)

### Grid (`src/pages/index.astro`)

The bento grid uses CSS Grid with `auto-fit` + `minmax()` on mobile, switching to an explicit 4-column layout at 768px+.

**Desktop grid mapping:**
- **Cell A** (StatusCard): columns 1–3, rows 1–3
- **Cell B** (INPUT_STREAM): column 3–4, row 1–2
- **Cell C** (GithubStats): columns 3–5, rows 2–3
- **Cell D** (CORRUPT_DATA): column 4–5, row 1–2
- **Cell E** (RECENT_COMMITS): columns 1–5, row 3–4

### Components

#### StatusCard (`src/components/StatusCard.astro`)
- GitHub avatar image (circular, responsive via `clamp()`)
- Name, tagline, list of accomplishments
- Version display from `src/config.ts`
- All pure CSS, zero JS

#### GithubStats (`src/components/GithubStats.astro`)
- Uses [github-readme-stats](https://github.com/anuraghazra/github-readme-stats) via a self-hosted Vercel app
- `<picture>` element with `<source>` for automatic light/dark theme switching
- Transparent background, theme-matched text colors
- Stats API URL pattern: `https://github-readme-stats-sigma-five.vercel.app/api?username=USERNAME&show_icons=true&bg_color=00000000&text_color=COLOR&icon_color=COLOR&title_color=COLOR&hide_border=true`
- Links to GitHub profile on click

### Post-Build Script (`scripts/inject-size.mjs`)
Replaces the `__SIZE__` placeholder in the built HTML with the actual file size in KB. Currently the template uses a hardcoded `~4KB` string, so the script just logs the real size without replacing anything.

---

## Quick Start

```bash
# Clone
git clone https://github.com/Felipegalind0/felipegalind0.io.git
cd felipegalind0.io

# Install
npm install

# Dev server (localhost:4321)
npm run dev

# Build (outputs to dist/)
npm run build

# Preview built site
npm run preview
```

---

## Customization Guide

### Use as a template for your own site

1. **Fork or clone** this repo
2. **Update `public/CNAME`** with your domain (or delete it for `username.github.io`)
3. **Update `astro.config.mjs`** — change `site` to your URL
4. **Edit `src/components/StatusCard.astro`:**
   - Replace the avatar URL: `https://github.com/YOUR_USERNAME.png?size=80`
   - Change the name, tagline, and accomplishment lines
5. **Edit `src/components/GithubStats.astro`:**
   - Replace `Felipegalind0` with your GitHub username in both image URLs
6. **Edit `src/config.ts`:**
   - Update the `VERSION` string
7. **Customize tokens** in `src/styles/tokens.css`:
   - Change colors, gap, radius to your liking
8. **Change the font** in `src/layouts/Layout.astro`:
   - Swap the Google Fonts `<link>` tag and update `--font-mono` in tokens.css

### Adding a new widget

1. Create `src/components/MyWidget.astro`:
   ```astro
   <div class="my-widget">
     <!-- your content -->
   </div>

   <style>
     .my-widget {
       /* scoped styles */
     }
   </style>
   ```

2. Import and place it in `src/pages/index.astro`:
   ```astro
   ---
   import MyWidget from "../components/MyWidget.astro";
   ---
   ```
   ```html
   <section class="cell cell-b"><MyWidget /></section>
   ```

3. Adjust grid placement in the `<style>` block of `index.astro` if needed.

### Placeholder widgets (not yet implemented)

| Cell | Name            | Suggested purpose                   |
|:-----|:----------------|:------------------------------------|
| B    | INPUT_STREAM    | Blog feed, social links, interests  |
| D    | CORRUPT_DATA    | Random/glitch art, fun data         |
| E    | RECENT_COMMITS  | Latest GitHub activity feed         |

---

## Deployment

### GitHub Pages (current setup)

The site deploys to the `gh-pages` branch using the `gh-pages` npm package:

```bash
# Build + deploy in one command
npm run build && npx gh-pages -d dist
```

This pushes the `dist/` folder to the `gh-pages` branch. GitHub Pages serves from that branch.

**Important:** GitHub Actions deploy was attempted but disabled due to billing restrictions. The manual `gh-pages` approach works without Actions.

### Custom Domain

1. Set DNS A records (DNS-only, no proxy) pointing to GitHub Pages IPs:
   ```
   185.199.108.153
   185.199.109.153
   185.199.110.153
   185.199.111.153
   ```
2. Add a CNAME record for `www` → `username.github.io`
3. Keep `public/CNAME` with your domain — it gets copied to `dist/` on build
4. In repo Settings → Pages, verify the custom domain

### Other hosts

Since this is a static site (`dist/` is plain HTML/CSS), it works anywhere:
- **Netlify / Vercel / Cloudflare Pages:** Connect repo, build command `npm run build`, output dir `dist`
- **Any web server:** Just serve the `dist/` folder

---

## Commands

| Command                    | Action                                    |
|:---------------------------|:------------------------------------------|
| `npm install`              | Install dependencies                      |
| `npm run dev`              | Start dev server at `localhost:4321`       |
| `npm run build`            | Build to `./dist/` + log page size        |
| `npm run preview`          | Preview built site locally                |
| `npx gh-pages -d dist`    | Deploy `dist/` to `gh-pages` branch       |

---

## Design Principles

- **Zero JavaScript** — the entire page is static HTML + CSS, no client-side JS
- **System theme** — respects `prefers-color-scheme`, no manual toggle
- **Tiny** — the entire page is ~6KB of HTML/CSS (excluding external font)
- **Monospace** — Anonymous Pro with slashed zeros everywhere
- **Bento grid** — responsive CSS Grid, no layout frameworks
- **Scanline overlay** — subtle CRT texture on desktop, disabled on mobile

---

## Tech Stack

- [Astro](https://astro.build) v5 — static site generator (zero JS output)
- [Anonymous Pro](https://fonts.google.com/specimen/Anonymous+Pro) — monospace font with slashed zeros
- [github-readme-stats](https://github.com/anuraghazra/github-readme-stats) — live GitHub stats SVG
- CSS Grid + custom properties — no frameworks, no preprocessors
- GitHub Pages — hosting

---

## For LLMs

If you're an AI assistant working on this codebase, here's a quick reference:

- **Build:** `npm run build` → static output in `dist/`
- **Deploy:** `npm run build && npx gh-pages -d dist`
- **Styles are scoped** per `.astro` component, except globals in `Layout.astro`
- **Theme colors** → `src/styles/tokens.css` (CSS custom properties)
- **Font** → Google Fonts `<link>` in `src/layouts/Layout.astro` `<head>`, font-family in tokens.css
- **Grid placements** → `<style>` block in `src/pages/index.astro`
- **Components** are `.astro` files: frontmatter in `---` fences, then HTML template, then `<style>` block
- **No client-side JS** — everything renders at build time
- **GitHub stats** use an external Vercel-hosted SVG, not build-time API calls
- **`<picture>` element** in `GithubStats.astro` handles light/dark via `<source media="(prefers-color-scheme: ...)">`
- **`public/CNAME`** must exist for custom domain deploys (auto-copied to dist)
- **Version string** lives in `src/config.ts`, rendered in `StatusCard.astro`
- **Repo:** `Felipegalind0/felipegalind0.io` on GitHub

---

## Version History

| Version | Date       | Changes                                                        |
|:--------|:-----------|:---------------------------------------------------------------|
| v.2.0   | 2026-02-11 | Source link in footer, versioning, flattened repo structure     |
| v.1.0   | 2026-02-11 | Anonymous Pro font (slashed zeros), comprehensive README       |
| b.0.1   | 2026-02-10 | Initial build: bento grid, StatusCard, GithubStats, deployment |

Version is defined in `src/config.ts` and rendered in the StatusCard footer alongside a link to the source repo.

---

## License

MIT