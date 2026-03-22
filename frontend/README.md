# Frontend

Frontend for TestReport Storage built with Vue 3, TypeScript, Vite and Nginx.

This UI is designed to work with [allure-framework/allure3](https://github.com/allure-framework/allure3).
It is part of an independent product and is not affiliated with or endorsed by the upstream project.
The upstream reference is included here to preserve attribution required by the Apache-2.0 license.

## Pages
- `/dashboard` - QA analytics dashboard based on `history.jsonl`
- `/reports` - list of uploaded reports and built-in report viewer
- `/reports/:reportId` - direct link to a specific report

## Dashboard Capabilities
- History-based KPIs: runs, unique tests, pass rate, p95 duration
- Stability analytics: flaky tests, always failed, always passed, incidents
- Recent run trends
- Most unstable tests
- Failure signatures
- Tag health
- Test details panel opened from Stability popup

## Filters
Dashboard supports filters by:
- `tag` (multi-select)
- `suite`
- `environment`
- `failure signature`

Filters are synced to the page URL, so the dashboard state can be shared with a direct link.

## Development
```bash
cd /Users/zaharpirozenko/Documents/allure3_folder/frontend
npm ci
npm run dev
```

Dev server: `http://localhost:5173`

## Production Build
```bash
cd /Users/zaharpirozenko/Documents/allure3_folder/frontend
npm run build
```
