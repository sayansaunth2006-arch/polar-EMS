# CobaltFlow — marketing landing page (showcase)

A standalone Next.js marketing site, separate from the POLAR-EMS app in this repo, built specifically to exercise the two installed Claude Code skills (`.claude/skills/ui-ux-pro-max` and `.claude/skills/motion`) on a real task end to end rather than just referencing them informally.

**CobaltFlow is a fictional product** — an invented B2B SaaS for engineering-team workflow automation, made up purely as a subject for this landing page. It is not a real company.

## How the skills drove this build

- **`ui-ux-pro-max`**: ran `--design-system` for a "B2B SaaS developer tooling" brief, which returned Glassmorphism as its top style match — its own output flagged "dark mode by default" as an anti-pattern for that style, which conflicted with the brief's dark-mode-friendly requirement. Re-queried the `style` domain directly and got **Minimalism & Swiss Style** (dark-mode supported, "Best For: SaaS platforms, professional tools"), then pulled a real color match from the `color` domain ("API Developer Portal": near-black background, dark card surfaces) and typography from the `typography` domain (Plus Jakarta Sans — appeared as the top SaaS/B2B match across multiple queries). Landing-page structure came from the `landing` domain (Hero + Testimonials + CTA / Trust & Authority patterns), and UX guidance (`ux` domain) directly shaped the animation approach below.
- **`motion`**: its React best-practices doc set the implementation rules actually followed in this code — import from `motion/react` in client components, prefer physics-based springs over duration/easing pairs for anything that could be interrupted, and (per the UX guidance pulled from ui-ux-pro-max) keep springs restrained with no overshoot for a "serious" B2B product (`bounce: 0.1–0.15`) rather than the bouncier settings appropriate for a more playful product.

## What's here

A single-page site: sticky nav (with a real mobile menu), animated hero (staggered entrance, respects `prefers-reduced-motion`), social-proof logo strip, feature grid, 3-step "how it works", testimonials, pricing (working monthly/annual toggle), an accessible FAQ accordion (native `<details>`, keyboard/screen-reader friendly with no extra JS), a closing CTA, and a footer that's honest about this being a fictional demo product.

Architecture note: only the interactive pieces (`Hero`, `MobileMenuButton`, `Pricing`, the shared `Reveal` scroll-animation wrapper) are Client Components — everything else is a Server Component, per the Next.js "push Client Components down" guidance pulled from the `ui-ux-pro-max` stack search.

## Run it

```bash
cd showcase
npm install
npm run dev
```

Open http://localhost:3000 (or whatever port you pass via `--port`).

## Verification

- `npx tsc --noEmit` and `npx eslint src` — both clean.
- `npm run build` — production build succeeds.
- Manually tested in a real browser via Playwright: hero renders and animates on load; scrolling through the full page triggers every scroll-reveal section correctly (verified via computed-opacity check, not just visually); the pricing monthly/annual toggle updates the displayed price; the FAQ accordion opens/closes; the mobile hamburger menu opens and its links work; responsive at 390px (mobile) and 1440px (desktop).
- One thing *not* a bug, in case it comes up again: a Playwright `fullPage: true` screenshot taken without scrolling shows most sections as invisible. That's specific to how Chrome DevTools Protocol captures beyond-viewport content (it renders it without ever firing real scroll/IntersectionObserver events) — real users, who always scroll, see every section animate in correctly, as confirmed by the scroll-through test above.
