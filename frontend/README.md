# BugDiag Frontend

React + Vite + Tailwind CSS frontend for the Bug Diagnosis Platform.

## Run

```bash
npm install
npm run dev
```

Backend:
`http://localhost:8000`

Optional frontend env:
`VITE_API_BASE_URL=http://localhost:8000`

## Structure

- `src/components/` reusable UI
- `src/pages/` application screens
- `src/services/api.js` FastAPI integration
- `src/context/ThemeContext.jsx` dark/light mode
- `src/utils/helpers.js` formatting/badge helpers
