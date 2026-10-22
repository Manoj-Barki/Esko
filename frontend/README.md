# PrintGuard frontend

React + Vite UI for the PrintGuard backend.

## Run

```bash
# 1. backend (in Esko-main/backend)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 2. frontend (in this folder)
npm install
npm run dev        # http://localhost:3000
```

Port 3000 matters: the backend's CORS only allows `http://localhost:3000`.
In dev, `/api` is proxied to `127.0.0.1:8000`. For a separate deployment,
set `VITE_API_BASE` and add that origin to the backend's CORS list.

## Screens

- **Inspect**: drop a PDF/PNG/JPEG, optionally override rules (DPI, clearance, safe margin, printed width, dieline colours), optionally link to a batch. Results show a page preview with finding overlays, severity filters, evidence, mark resolved / false positive, check status (including checks that could not run) and the HTML report download.
- **Batches**: create (shelf life or expiry date), list, delete, purge expired, and open linked inspections.
