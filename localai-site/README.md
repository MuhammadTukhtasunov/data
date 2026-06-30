# [COMPANY NAME] — Local AI Consulting Website

A static, dependency-free marketing site for a solo consulting firm that builds
fully local, private AI systems. Semantic HTML + modern CSS + ~60 lines of
vanilla JS. No framework, no build step, no external requests of any kind —
fonts, images, and scripts are all served from this directory.

## Run locally

Any static file server works:

```sh
cd localai-site
python3 -m http.server 8000
# → http://localhost:8000
```

## Deploy

The whole site is this directory. Upload it anywhere that serves static files.

**Cloudflare Pages** — create a project, connect the repo (or use
`wrangler pages deploy localai-site`), set the build output directory to
`localai-site`, no build command.

**Netlify** — drag the `localai-site` folder onto app.netlify.com/drop, or
connect the repo with publish directory `localai-site` and no build command.

**GitHub Pages (one-time enable required).** A deploy workflow is included at
`.github/workflows/deploy-pages.yml`, but a workflow cannot turn Pages on for
the first time — that is a manual switch only a repo admin can flip:

1. Go to **Settings → Pages** (`https://github.com/<owner>/<repo>/settings/pages`).
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Run the workflow: **Actions → "Deploy site to GitHub Pages" → Run workflow**
   (it is manual-only so it never fails on routine pushes before Pages exists).

The site then publishes at `https://<owner>.github.io/<repo>/`. Until step 1 is
done, the workflow fails with `Create Pages site failed: Resource not accessible
by integration` — that error means only "Pages isn't enabled yet," nothing else.

**Fastest with no settings — Netlify Drop.** Drag the `localai-site` folder onto
`https://app.netlify.com/drop` for an instant public URL, no account config.

## Placeholders to fill in before launch

Search the files for `[` to find them all. Complete list:

| Placeholder | Where | Replace with |
|---|---|---|
| `[COMPANY NAME]` | `index.html` (title, OG tags, JSON-LD, nav, about, footer), `assets/og.png` | Your company name |
| `[YOUR NAME]` | `index.html` (about section, JSON-LD, headshot alt/caption) | Your name |
| `[FIELD — e.g., electrical engineering]` | `index.html` about section | Your research field |
| `[UNIVERSITY]` | `index.html` about section | Your university (or "a major university") |
| `[HEADSHOT PLACEHOLDER]` | `assets/headshot.svg` | A real photo — add `assets/headshot.jpg` and update the `<img>` in the About section |
| `[FORMSPREE_ID]` | `index.html` contact form `action` | Your Formspree form ID (or change the form to `action="mailto:you@email"` — Formspree is nicer). Until replaced, JS blocks submission and shows a notice. |
| `[CALENDLY LINK]` | `index.html` contact section | Your Calendly URL (or delete that button) |
| `[YOUR@EMAIL]` | `index.html` (contact, footer, JSON-LD) | Your email address |
| `[CITY, STATE]` / `[CITY]` / `[STATE]` | `index.html` (footer, JSON-LD) | Your location |
| `https://www.example.com` | `index.html` (canonical, OG, JSON-LD), `sitemap.xml`, `robots.txt` | Your real domain |
| `2026-06-12` | `sitemap.xml` `<lastmod>` | Launch date |
| `assets/og.png` | — | Regenerate with your real company name (it currently renders the literal placeholder) |

## Design notes

- **Identity:** "engineering datasheet" — numbered sections, monospace spec
  labels, ruled comparison tables, hazard-amber indicator accents on gunmetal.
- **Palette:** Bolt Black `#0E1116`, Gunmetal `#161C24`, Hairline `#2A323D`,
  Paper `#E8EAED`, Steel `#97A1AD`, Signal Amber `#FFB000`.
- **Type:** Archivo (variable, display + body) and IBM Plex Mono (labels,
  tables, buttons). Self-hosted woff2 in `assets/fonts/` — no Google Fonts
  request at runtime.
- **Signature element:** the hero "data perimeter" schematic (animated SVG of
  data flowing inside a building outline, with a severed route to the cloud)
  plus the live footer badge that counts this page's external requests in the
  visitor's browser. Keep that count at zero: if you add any third-party embed,
  the badge will say so honestly.
- **Accessibility:** semantic landmarks, skip link, visible focus states,
  `prefers-reduced-motion` honored, contrast ≥ WCAG AA on all text.
