# PrintGuard AI

### AI-powered packaging artwork preflight with RAG assistant and production validation

[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?logo=react&logoColor=white)](https://react.dev/) [![Vite](https://img.shields.io/badge/Build-Vite-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/) [![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/) [![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/) [![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC)](https://pytest.org/) [![AI](https://img.shields.io/badge/AI-RAG%20Powered-FF6B6B)](https://github.com/Manoj-Barki/Esko)

**PrintGuard AI is an AI-powered packaging preflight assistant that helps teams catch production risks before files reach the press.** Upload PDFs, PNGs, or JPEGs for automated validation with 8 industry-standard checks, get AI-powered explanations via RAG system, chat with the AI assistant about packaging standards, and receive comprehensive reports. Supports multi-file batch uploads and production-ready validation for packaging workflows.

> **Important:** PrintGuard is a screening aid, not a print-readiness certification. Always validate artwork against the printer's and packaging line's specifications.

---

## The problem

Packaging artwork can look correct on screen and still carry production risks: low-resolution imagery, text placed too close to cut/fold lines, or content positioned outside a safe area. Manual checks are time-consuming and easy to apply inconsistently, especially when multiple products or batches are involved.

## The solution

PrintGuard combines deterministic preflight checks with visual evidence and explicit uncertainty handling. Findings include a severity, measured evidence, an explanation, a recommended action, and a normalized location that the UI can overlay on a page preview. If a check cannot be evaluated from the uploaded file, it is marked **unavailable** rather than silently treated as a pass.

### What it checks today

| Rule ID | Check | Purpose |
|---|---|---|
| `RES-001` | Effective image resolution | Flags raster imagery below configured DPI warning/critical thresholds. |
| `GEOM-001` | Text near cut/fold geometry | Flags text crossing or too close to detected dieline geometry. |
| `SAFE-001` | Safe-area boundary | Flags text outside the configured safe area near the page edge. |
| `BLEED-001` | **Bleed validation** | **Validates 3mm bleed areas on all sides (packaging industry standard).** |
| `TRIM-001` | **Trim mark detection** | **Detects presence of trim/crop marks for production cutting (expects 4+ marks).** |
| `FONT-001` | **Font embedding** | **Ensures all fonts are embedded or subsetted in PDF (critical for RIP).** |
| `OVERPRINT-001` | **White overprint detection** | **Detects white elements set to overprint (prevents disappearing elements).** |
| `TEXT-001` | **Text legibility** | **Validates minimum text sizes: 6pt general, 7pt reversed, 8pt uncoated.** |

The checks are configurable. Dieline identification can use configured stroke colours and layer names; dashed lines can be treated as probable folds and may require review.

### 🤖 AI Features

- **RAG-Powered Assistant:** Chat interface with AI assistant trained on packaging standards and PrintGuard rules
- **AI Explanations:** Get context-aware explanations for any finding using the RAG knowledge base
- **Vector Database:** Local ChromaDB storage with sentence-transformers embeddings (runs offline)
- **Optional OpenAI:** Connect OpenAI API for enhanced natural language responses
- **Pre-loaded Knowledge:** Industry standards for DPI, bleed, dielines, substrates, and common defects

## Product workflow

```mermaid
flowchart TD
    A[Open PrintGuard] --> B{Choose workflow}
    B --> C[Inspect artwork]
    B --> D[Manage batches]
    B --> E[AI Assistant]
    C --> F[Drag & drop multiple files]
    F --> G[Optionally choose a batch and override rules]
    G --> H[Backend validates type and size]
    H --> I[Run 8 production checks]
    I --> J[Generate findings and page previews]
    J --> K[Review severity, evidence and locations]
    K --> L[Get AI explanation for findings]
    K --> M[Mark a finding reviewed / false positive]
    K --> N[Download HTML report]
    D --> O[Create, view or delete batches]
    O --> P[Link inspections to batch]
    P --> Q[Expiry-based cleanup]
    E --> R[Chat with AI about packaging standards]
    E --> S[Ask about DPI, bleed, fonts, etc.]
```

## Architecture

```mermaid
flowchart LR
    U[User] --> UI[React UI<br/>Vite :3000]
    UI -->|/api requests| VP[Vite development proxy]
    VP --> API[FastAPI application<br/>:8000]
    API --> CFG[Rule configuration]
    API --> PDF[PDF inspector]
    API --> IMG[PNG / JPEG inspector]
    PDF --> GEO[Geometry checks]
    PDF --> RES[Resolution checks]
    PDF --> PROD[Production checks]
    IMG --> RES
    GEO --> FIND[Structured findings]
    RES --> FIND
    PROD --> FIND
    FIND --> STORE[Inspection JSON + page previews]
    FIND --> REPORT[HTML report generator]
    API --> DB[SQLite batch database]
    API --> RAG[RAG Service]
    RAG --> VDB[ChromaDB vector store]
    RAG --> EMB[HuggingFace embeddings]
    RAG --> LLM[OpenAI GPT-3.5 optional]
    DB --> PURGE[Expiry purge loop]
    STORE --> API
    REPORT --> API
    RAG --> API
    API --> UI
```

### Design principles

- **Evidence over a black box:** each finding exposes what was measured and where it was found.
- **Unavailable is not passed:** unsupported or insufficient source data is surfaced honestly.
- **Configurable to production rules:** thresholds and dieline hints can be overridden per inspection.
- **Human review stays in the loop:** findings can be marked as reviewed/false positive; the app does not certify print readiness.
- **Small, local-first prototype:** uploaded artifacts and results are stored locally by default, and batch metadata uses SQLite.

---

## Application features

### Inspect

- **Multi-file upload:** Drag & drop multiple PDFs, PNGs, or JPEGs at once (25 MB per file default)
- **Batch processing:** Sequential inspection with progress indicators for each file
- **8 production checks:** Resolution, geometry, safe-area, bleed, trim marks, fonts, overprint, text size
- **AI explanations:** Click "Get AI explanation" on any finding for context-aware help from RAG system
- **Visual overlays:** Page previews with finding boxes mapped to exact locations
- **Status management:** Mark findings as reviewed/false positive
- **HTML reports:** Download comprehensive standalone reports
- **Batch association:** Link inspections to manufacturing batches
- **Live status:** Backend connectivity indicator in header

### AI Assistant

- **RAG-powered chat:** Ask questions about packaging standards, DPI requirements, bleed specs, etc.
- **Pre-loaded knowledge:** Industry standards for resolution, dielines, substrates, common defects
- **Source citations:** AI responses include source references from the knowledge base
- **Offline capable:** Local embeddings work without API keys (OpenAI optional for enhanced responses)
- **Finding explanations:** Get detailed explanations for any inspection finding

### Batches

- Create a batch with a batch number, optional product name, manufacturing date, and either expiry date or shelf-life days.
- List batches, open inspections associated with a batch, and delete a batch.
- Trigger an expiry cleanup manually.
- Automatically purge expired batches and linked inspection artifacts at server startup and on a configurable interval. A batch is retained through its expiry date and removed the day after.

### Rule configuration

Default values are loaded from `backend/rules/default_rules.json` and validated in `backend/config.py`.

| Setting | Default / meaning |
|---|---|
| `min_dpi_warning` | `150` DPI warning threshold |
| `min_dpi_critical` | `72` DPI critical threshold |
| `min_clearance_mm` | `3.0` mm text-to-dieline clearance |
| `safe_margin_mm` | `3.0` mm safe-area inset |
| `safe_area_norm` | Optional explicit normalized safe area `[x, y, width, height]`; overrides margin-based area |
| `dieline_colors` | RGB stroke colours (components from `0` to `1`) considered cut/fold lines |
| `color_tolerance` | Colour matching tolerance |
| `dieline_layer_names` | Layer-name hints such as `dieline`, `cut`, `fold`, and `crease` |
| `detect_dashed_as_fold` | Whether dashed lines can be treated as probable folds |
| `image_target_width_mm` | Optional assumed printed width for raster uploads so effective DPI can be estimated |
| `preview_zoom` | Preview rendering scale |
| `max_pages` | Maximum PDF pages to process |

Tune these values to the printer, substrate, finishing process, and packaging specification. Defaults are starting points, not universal print standards.

---

## Technology stack

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React 18, Vite, JavaScript, CSS | Multi-file upload, findings UI, AI chat, overlays, batches, API status |
| API | FastAPI, Uvicorn, Pydantic | HTTP endpoints, input validation, orchestration, structured response models |
| PDF processing | PyMuPDF | PDF page inspection, production checks, preview generation |
| Raster processing | Pillow | PNG/JPEG loading and image inspection |
| AI/RAG | LangChain, ChromaDB, HuggingFace, OpenAI | Vector database, embeddings, semantic search, AI Q&A |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Local semantic embeddings (runs offline) |
| LLM | OpenAI GPT-3.5-turbo (optional) | Natural language responses for chat and explanations |
| Persistence | JSON files + SQLite + ChromaDB | Inspection results, batch records, vector knowledge base |
| Reporting | Generated HTML | Portable report download |
| Testing | pytest, HTTPX | API and rule behaviour tests |

---

## Repository structure

```text
Esko/
├── README.md                         # Project overview, setup, architecture and API
├── CHANGELOG.md                      # Comprehensive feature documentation
├── .gitignore                        # Ignores node_modules, Python cache and virtualenv
├── backend/
│   ├── main.py                       # FastAPI app, endpoints, RAG endpoints, cleanup lifecycle
│   ├── config.py                     # Defaults + per-inspection rule validation
│   ├── schemas.py                    # Finding, status and inspection result models
│   ├── db.py                         # SQLite batches, inspection links and expiry purge
│   ├── requirements.txt              # Python dependencies (includes AI/RAG packages)
│   ├── rules/
│   │   └── default_rules.json        # Default preflight thresholds and dieline hints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document.py               # Shared document-related helpers
│   │   ├── pdf_inspector.py          # PDF text/geometry inspection and page previews
│   │   ├── image_inspector.py        # PNG/JPEG inspection and previews
│   │   ├── resolution_checks.py      # RES-001 effective-resolution check
│   │   ├── geometry_checks.py        # GEOM-001 and SAFE-001 checks
│   │   ├── production_checks.py      # BLEED/TRIM/FONT/OVERPRINT/TEXT production checks
│   │   ├── rag_service.py            # RAG system with ChromaDB and embeddings
│   │   ├── report_generator.py       # Downloadable HTML report generation
│   │   └── summary.py                # Finding IDs and result summary helpers
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py               # Test fixtures
│       ├── test_api.py               # API behaviour
│       ├── test_batches.py            # Batch lifecycle and expiry
│       ├── test_geometry.py          # Geometry/safe-area checks
│       └── test_resolution.py        # Resolution checks
└── frontend/
    ├── index.html                    # Vite entry document; mounts React at #root
    ├── package.json                  # Frontend scripts and dependencies
    ├── package-lock.json             # Locked npm dependency tree
    ├── vite.config.js                # Dev server on :3000 and /api proxy to :8000
    └── src/
        ├── main.jsx                  # React bootstrap and stylesheet import
        ├── App.jsx                   # Header, navigation, AI Assistant tab, view routing
        ├── api.js                    # API wrapper with RAG endpoints
        ├── styles.css                # Application styling (includes chat UI)
        └── components/
            ├── UploadView.jsx        # Multi-file drag & drop upload with progress
            ├── ResultView.jsx        # Findings, AI explanations, overlays, report link
            ├── AssistantView.jsx     # AI chat interface for packaging standards Q&A
            └── BatchesView.jsx       # Batch create/list/delete and linked inspections
```

> The tree above describes the current prototype layout. If a file is renamed or added, update this section to keep it in sync with the repository.

---

## Run locally

### Prerequisites

- Python 3.10 or newer
- Node.js and npm
- Git (optional, for cloning)

### 1. Get the code

```bash
git clone https://github.com/Manoj-Barki/Esko.git
cd Esko
```

### 2. Start the backend

Open a terminal in the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
```

```bash
# Git Bash / macOS / Linux
source .venv/Scripts/activate  # Windows Git Bash
# On macOS/Linux use: source .venv/bin/activate
```

Install dependencies and start FastAPI:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend URLs:

- API health: <http://127.0.0.1:8000/api/health>
- Interactive API docs: <http://127.0.0.1:8000/docs>

### 3. Start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>.

The Vite development server proxies `/api` requests to `http://127.0.0.1:8000`. The backend's current CORS configuration allows `http://localhost:3000`, so use that exact frontend origin during local development.

### 4. Run tests

With the backend virtual environment activated:

```bash
cd backend
pytest -q
```

---

## API reference

The backend exposes the following endpoints. Request and response schemas can also be explored at `http://127.0.0.1:8000/docs` while the backend is running.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Health check used by the frontend connection indicator |
| `POST` | `/api/inspect` | Upload and inspect PDF/PNG/JPEG; accepts multipart `file`, optional JSON-string `config`, optional `batch_id` |
| `GET` | `/api/inspections/{id}` | Retrieve a saved inspection result |
| `GET` | `/api/inspections/{id}/pages/{n}` | Retrieve a rendered page preview (`n` is 1-based) |
| `PATCH` | `/api/inspections/{id}/findings/{finding_id}` | Update finding status, e.g. `{"status":"false_positive"}` |
| `GET` | `/api/inspections/{id}/report` | Download generated HTML report |
| `POST` | `/api/batches` | Create a batch |
| `GET` | `/api/batches` | List batches |
| `GET` | `/api/batches/{batch_id}` | Get a batch by ID |
| `DELETE` | `/api/batches/{batch_id}` | Delete a batch and associated stored inspection data |
| `POST` | `/api/batches/purge-expired` | Manually trigger expiry cleanup |
| **`POST`** | **`/api/rag/chat`** | **AI chat: send question, get answer with sources from knowledge base** |
| **`GET`** | **`/api/rag/search`** | **Semantic search in knowledge base (query param `query`, optional `k`)** |
| **`POST`** | **`/api/rag/explain/{finding_id}`** | **Get AI explanation for specific finding (requires `inspection_id` param)** |
| **`GET`** | **`/api/rag/stats`** | **Get RAG system statistics (document count, status, OpenAI configured)** |

### Inspection request flow

```mermaid
sequenceDiagram
    actor User
    participant UI as React UI
    participant API as FastAPI
    participant Inspect as Inspection services
    participant Store as Local storage

    User->>UI: Select artwork and options
    UI->>API: POST /api/inspect (multipart)
    API->>API: Validate batch, config, size and file signature
    API->>Inspect: Inspect PDF or raster image
    Inspect-->>API: Findings, checks and previews
    API->>Store: Save upload, previews and result.json
    API-->>UI: Structured inspection result
    UI-->>User: Findings and overlays
    User->>UI: Download report
    UI->>API: GET /api/inspections/{id}/report
    API-->>UI: HTML report
```

Finding coordinates use normalized `[x, y, width, height]` values relative to the page, with origin at the top-left. This lets the frontend render overlays at different zoom levels. Page numbering starts at 1.

### Example: create a batch

```http
POST /api/batches
Content-Type: application/json
```

```json
{
  "batch_number": "B-101",
  "product_name": "Example carton",
  "mfg_date": "2026-10-01",
  "shelf_life_days": 180
}
```

Provide either `expiry_date` or `shelf_life_days`. The expiry date must be after the manufacturing date, and batch numbers must be unique.

---

## Storage, privacy and configuration

By default, the backend stores data under a `printguard` directory inside the operating system's temporary folder. This includes uploaded files, inspection result JSON, page previews, and the SQLite database. Temporary storage is convenient for demos, but the OS may clean it up. For persistent local storage, set `PRINTGUARD_STORAGE` before starting the backend.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `PRINTGUARD_STORAGE` | OS temp directory + `printguard` | Root directory for uploads, results, previews, SQLite DB, and ChromaDB |
| `PRINTGUARD_MAX_MB` | `25` | Maximum accepted upload size in MB |
| `PRINTGUARD_PURGE_MINUTES` | `60` | Interval between automatic expiry purges |
| **`OPENAI_API_KEY`** | **None** | **Optional OpenAI API key for enhanced AI responses (embeddings work without it)** |
| **`HF_TOKEN`** | **None** | **Optional HuggingFace token for faster model downloads and higher rate limits** |
| `VITE_API_BASE` | Empty string | Optional API base URL for a separately hosted frontend; configure backend CORS accordingly |

Example (PowerShell):

```powershell
$env:PRINTGUARD_STORAGE = "C:\printguard-data"
$env:PRINTGUARD_MAX_MB = "25"
$env:PRINTGUARD_PURGE_MINUTES = "60"
uvicorn main:app --reload --port 8000
```

**Privacy note:** treat uploads as production assets. Use only files you are authorized to process, choose a storage location appropriate for their sensitivity, and remember that expiry purge permanently deletes expired batch data and linked inspection artifacts.

---

## Limitations and honest uncertainty

- PNG/JPEG inputs provide visual previews, but vector geometry checks require a PDF with usable vector paths.
- Scanned/image-only PDFs may not contain extractable text; geometry-related checks can therefore be unavailable.
- Raster DPI cannot be reliably inferred without a physical print size. `image_target_width_mm` can supply an assumed width for an estimate.
- Safe-area checks measure from the page edge unless `safe_area_norm` is configured; they do not automatically infer every printer's trim box or bleed specification.
- Dieline colours and layer names must be configured for the source artwork. Dashed-line detection is heuristic and may need human review.
- The default thresholds are not universal standards; calibrate them to the production workflow.
- A passing result does not guarantee colour accuracy, trapping, overprint behaviour, barcode readability, substrate compatibility, or overall print readiness.
- This is a local prototype, not a hardened multi-tenant production service. Review authentication, authorization, storage isolation, deployment configuration, and operational monitoring before exposing it to untrusted networks.

## Troubleshooting

| Symptom | What to check |
|---|---|
| Frontend says “Backend not reachable” | Start the API from `backend/` using `uvicorn main:app --reload --port 8000`; check `/api/health`. |
| Browser page is blank | Confirm `frontend/index.html` exists, includes `<div id="root"></div>`, and loads `/src/main.jsx`; check browser console and Vite terminal. |
| Upload returns `415` | Only PDF, PNG, and JPEG files are supported. |
| Upload returns `413` | File exceeds `PRINTGUARD_MAX_MB` (25 MB by default). |
| Upload returns `422` | The file may be unreadable/corrupt or the optional config JSON may be invalid. |
| Batch creation returns `409` | The batch number already exists. Choose a unique number. |
| Page/report returns `404` | Verify the inspection ID and page number; stored data may have been removed by expiry cleanup. |
| Frontend API requests fail in development | Keep frontend at `http://localhost:3000`; Vite proxies `/api` to port `8000`. |

## Roadmap ideas

Potential next steps for a hackathon demo or future iteration:

- Add representative sample artwork and clearly labelled defect fixtures.
- Add a “before/after” guided demo and a one-click sample inspection.
- Add configurable per-printer profiles and versioned rule sets.
- Add a batch-level summary of inspection outcomes and recurring defect patterns.
- Add export options such as JSON/CSV alongside HTML.
- Add stronger persistence controls, authentication, audit events, and deployment documentation before production use.

These are ideas, not features currently claimed by the prototype.

## Contributing

1. Create a focused branch.
2. Make a small, testable change.
3. Add or update tests for rule/API behaviour.
4. Run `pytest -q` from `backend/` and verify the frontend manually.
5. Update this README when endpoints, rules, storage behaviour, or project structure changes.

## License

No license is specified in this repository yet. Add a `LICENSE` file before redistributing the project or accepting external contributions under explicit terms.

---

**Built for safer packaging preflight workflows.** Catch likely issues earlier, show the evidence, and keep the final production decision with the people and specifications that matter.
