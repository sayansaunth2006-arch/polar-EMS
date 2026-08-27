# POLAR-EMS — Frontend

Next.js 16 (App Router) + TypeScript + Tailwind CSS v4 dashboard for the POLAR-EMS backend.

See the [repo root README](../README.md) for the full project overview, setup instructions, and demo script. Quick start from this directory:

```bash
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_BASE_URL — defaults to http://localhost:8000
npm run dev
```

Requires the backend (`../backend`) running first — see its section in the root README.

- `npx tsc --noEmit` — type-check
- `npx eslint src` — lint
- `npx playwright test` — end-to-end tests (needs both dev servers running)
