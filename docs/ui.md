# UI

## Overview
The UI is a React + Vite + TypeScript app in `ui/` with light/dark themes and a dashboard for usage, requests, and API keys.

## Routes
- `/login`
- `/register`
- `/` (Overview)
- `/usage`
- `/requests`
- `/projects`
- `/members`
- `/keys`
- `/settings` (API keys and rate limits)

## Theme
- CSS variables drive light/dark mode.
- Theme state persists in `localStorage`.

## Data Sources
The UI reads from:
- `/auth/*`
- `/keys/*`
- `/orgs/*`
- `/projects/*`
- `/usage/*`
- `/requests`
- `/dashboard/providers`

## Dev

```bash
cd ui
npm install
npm run dev
```
