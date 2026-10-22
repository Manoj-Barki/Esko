# PrintGuard AI: Backend

Hi! This is the backend for PrintGuard AI, a packaging preflight assistant. You upload a dieline or artwork (PDF, PNG or JPEG), and it checks for a few common production risks, shows you where each one is, and gives you a report you can download.

I built it to be small and reliable rather than clever. It does a handful of checks well, tells you honestly when it can't check something, and never claims your artwork is "print-ready". It's a helper, not a certification.

## What it checks

| Check | What it looks for |
|---|---|
| `RES-001` | Images whose effective resolution (pixels vs. printed size) is too low |
| `GEOM-001` | Text that crosses, or sits too close to, a cut or fold line |
| `SAFE-001` | Text that sits outside the safe area near the page edge |

Every finding comes with a severity, the measured evidence, an explanation, a recommended action and a location on the page.

If a check can't run (for example, a PNG has no physical size, so DPI can't be measured), it is reported as **unavailable**. It is never silently counted as a pass.

## Getting started

You'll need Python 3.10 or newer.

```powershell
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Then open http://127.0.0.1:8000/docs. That page lets you try every endpoint from your browser.

Note that the server speaks plain `http`, not `https`.

To run the tests:

```powershell
pytest -q
```

## Using it

**Inspect a file**

`POST /api/inspect` with a `file` field (PDF, PNG or JPEG, up to 25 MB). You get back the findings, the check results and a summary.

Two optional fields:
- `config`: a JSON string that overrides the default rules for this one inspection
- `batch_id`: links the inspection to a batch (see below)

**Get results back**

- `GET /api/inspections/{id}` returns the full result
- `GET /api/inspections/{id}/pages/{n}` returns the page preview image
- `GET /api/inspections/{id}/report` downloads the HTML report
- `PATCH /api/inspections/{id}/findings/{finding_id}` with `{"status": "false_positive"}` lets you mark a finding as reviewed

**Coordinates**

Every finding has a `bbox` of `[x, y, width, height]`. Each value is between 0 and 1, relative to the page, with the origin at the top-left. This means you can draw overlays at any zoom level. Pages are numbered from 1.

## Tuning the rules

Defaults live in `rules/default_rules.json`. Please change them to match your printer's spec, because the right values depend on your production process.

| Setting | Meaning |
|---|---|
| `min_dpi_warning` / `min_dpi_critical` | Resolution thresholds |
| `min_clearance_mm` | Minimum distance between text and a cut/fold line |
| `safe_margin_mm` | Safe-area inset from the page edge |
| `safe_area_norm` | An explicit safe area `[x, y, w, h]`, which overrides the margin |
| `dieline_colors` | RGB stroke colours (0 to 1) that are definitely cut/fold lines |
| `dieline_layer_names` | Layer names that mark dielines |
| `image_target_width_mm` | Print width for raster uploads, so their DPI can be checked |

One thing worth knowing: I don't assume which lines are cuts or folds. If you tell me the dieline colour or layer, findings are more confident. Otherwise I fall back to treating dashed lines as probable folds, and those findings are marked "needs review".

## Batches and automatic expiry

If you track products by batch, there's a small SQLite database for that. Nothing to install or set up, as the file is created on first use.

Create a batch:

```json
POST /api/batches
{"batch_number": "B-101", "mfg_date": "2026-10-01", "expiry_date": "2027-04-01"}
```

You can send `shelf_life_days` instead of `expiry_date`, and I'll work out the expiry for you.

Other endpoints: `GET /api/batches`, `GET /api/batches/{id}`, `DELETE /api/batches/{id}`.

**Expired data is deleted automatically.** Once a batch's expiry date has passed, the batch and any inspections linked to it (uploaded file, previews and results) are removed. This happens when the server starts and then once an hour. A batch is kept through its expiry date and deleted the day after.

To trigger it right now, send `POST /api/batches/purge-expired`.

Deletion is permanent, so please don't point this at data you want to keep.

## Where your data lives

Files and the database are stored in your system's temp folder by default. That's fine for a demo, but your OS may clean it up. To keep data somewhere permanent, set this before starting the server:

```powershell
$env:PRINTGUARD_STORAGE="C:\printguard-data"
```

Other settings:
- `PRINTGUARD_MAX_MB`: upload size limit (default 25)
- `PRINTGUARD_PURGE_MINUTES`: how often expired data is purged (default 60)

## Project layout

```
backend/
├── main.py                  API routes
├── schemas.py               Finding and result models
├── config.py                Rule settings loader
├── db.py                    SQLite batches and expiry purge
├── rules/default_rules.json Default thresholds
├── services/
│   ├── pdf_inspector.py         PDF extraction and previews
│   ├── image_inspector.py       PNG/JPEG handling
│   ├── resolution_checks.py     RES-001
│   ├── geometry_checks.py       GEOM-001, SAFE-001
│   ├── report_generator.py      HTML report
│   └── summary.py               Finding IDs and summary counts
└── tests/                   Tests with controlled-defect fixtures
```

## Troubleshooting

**"Attribute not found in module main"**: check the command is `main:app` (not `main:appp`).

**SSL or "WRONG_VERSION_NUMBER" errors**: use `http://`, not `https://`.

**`No module named ...`**: run `pip install -r requirements.txt` in the environment you start the server from.

**415 error on upload**: only PDF, PNG and JPEG files are accepted.

**422 error on upload**: the file is corrupt, password-protected or unreadable. The server stays up and tells you safely.

## Known limitations

- Raster images (PNG/JPEG) get a visual preview only. Geometry checks need a PDF with real vector paths.
- Image-only (scanned) PDFs have no text to analyse, so geometry checks report as unavailable.
- Safe-area checks measure from the page edge, not from a trim box, unless you provide `safe_area_norm`.
- Results are a screening aid. Always confirm against your printer's specification.

Happy printing!
