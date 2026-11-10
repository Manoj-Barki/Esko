# PrintGuard AI - RAG System Setup Guide

## ✅ Current Status: RAG is WORKING!

Your RAG system is already up and running! Here's what's currently active:

- ✅ **Vector Database**: ChromaDB with 6 documents loaded
- ✅ **Embeddings**: HuggingFace sentence-transformers (running locally)
- ✅ **Knowledge Base**: Packaging standards pre-loaded
- ✅ **Semantic Search**: Working and tested
- ⚠️ **AI Chat**: Limited (OpenAI not configured)

---

## 🎯 What's Working Right Now

### 1. Semantic Search (No API Key Needed)
```bash
# Test semantic search - works offline!
curl "http://127.0.0.1:8000/api/rag/search?query=bleed&k=3"
curl "http://127.0.0.1:8000/api/rag/search?query=DPI+requirements&k=3"
curl "http://127.0.0.1:8000/api/rag/search?query=font+embedding&k=3"
```

### 2. RAG System Status
```bash
# Check RAG health
curl http://127.0.0.1:8000/api/rag/stats
```

**Current Output:**
```json
{
  "total_documents": 6,
  "collection_name": "packaging_standards",
  "status": "ready",
  "openai_configured": false
}
```

### 3. What Works WITHOUT OpenAI API Key

✅ **Embeddings** - Local HuggingFace model (sentence-transformers/all-MiniLM-L6-v2)
✅ **Semantic Search** - Find relevant documents by meaning, not keywords
✅ **Knowledge Base** - 6 pre-loaded documents about packaging standards
✅ **Vector Storage** - Persistent ChromaDB database
✅ **Finding Context** - Get relevant context for inspection findings

### 4. What Requires OpenAI API Key (Optional)

⚠️ **AI Chat Responses** - Natural language Q&A (currently returns error message)
⚠️ **AI Explanations** - Enhanced finding explanations (works with basic search fallback)

---

## 🚀 How to Enable Full AI Features (Optional)

If you want natural language chat responses, set up OpenAI:

### Step 1: Get OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create an account (requires phone verification)
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-...` or `sk-...`)

### Step 2: Set Environment Variable

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY = "sk-proj-your-key-here"
```

**Windows CMD:**
```cmd
set OPENAI_API_KEY=sk-proj-your-key-here
```

**Git Bash / Linux / macOS:**
```bash
export OPENAI_API_KEY="sk-proj-your-key-here"
```

### Step 3: Restart Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

You should see in the logs:
```
[RAG] Knowledge base initialized with 5 documents
INFO:     Application startup complete.
```

### Step 4: Test AI Chat

```bash
curl -X POST http://127.0.0.1:8000/api/rag/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the minimum DPI for packaging?"}'
```

---

## 📁 Where is Everything Stored?

### ChromaDB Vector Database
**Location:** `%TEMP%\printguard\chromadb\` (Windows) or `~/.printguard/chromadb/` (custom)

**Contents:**
- Embeddings for 6 packaging standards documents
- Metadata and source references
- Persistent across restarts

### Knowledge Base Documents

The RAG system includes these pre-loaded documents:

1. **Image Resolution Standards** - DPI requirements (300/150/72 thresholds)
2. **Dieline and Geometry** - Clearances, safe areas, dieline detection
3. **PrintGuard Rules** - All 8 validation rules explained (RES, GEOM, SAFE, BLEED, TRIM, FONT, OVERPRINT, TEXT)
4. **Common Defects** - Symptoms, causes, solutions for 7 defect types
5. **Substrate Guidelines** - Flexible, corrugated, labels, folding cartons, large format

### Embeddings Model
**Location:** `~/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/`

**Details:**
- Model: sentence-transformers/all-MiniLM-L6-v2
- Size: ~90MB
- Downloads on first run
- Works completely offline after download

---

## 🧪 Testing the RAG System

### Test 1: Check System Status
```bash
curl http://127.0.0.1:8000/api/rag/stats
```

**Expected:** `"status": "ready"`, `"total_documents": 6`

### Test 2: Semantic Search
```bash
# Search for bleed information
curl "http://127.0.0.1:8000/api/rag/search?query=bleed%20standard&k=2"

# Search for DPI requirements
curl "http://127.0.0.1:8000/api/rag/search?query=image%20resolution%20DPI&k=2"

# Search for font issues
curl "http://127.0.0.1:8000/api/rag/search?query=font%20embedding%20PDF&k=2"
```

**Expected:** Returns relevant document chunks with scores

### Test 3: AI Chat (Requires OpenAI)
```bash
curl -X POST http://127.0.0.1:8000/api/rag/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the minimum bleed for packaging?"}'
```

**Without OpenAI:** Returns `"error": "missing_api_key"`
**With OpenAI:** Returns AI-generated answer with sources

### Test 4: Frontend UI

1. Open http://localhost:3000
2. Click "AI Assistant" tab
3. Type a question: "What is the minimum DPI for packaging?"
4. **Without OpenAI:** Error message shown
5. **With OpenAI:** AI response with sources

---

## 🔧 Configuration Options

### Environment Variables

```bash
# Optional: Custom storage location
export PRINTGUARD_STORAGE="/path/to/storage"

# Optional: OpenAI API key for AI chat
export OPENAI_API_KEY="sk-proj-your-key"

# Optional: HuggingFace token (faster downloads)
export HF_TOKEN="hf_your-token"
```

### Checking Current Config

**Backend logs on startup:**
```
[RAG] Knowledge base already initialized with 6 documents
INFO:     Application startup complete.
```

**RAG Stats endpoint:**
```json
{
  "total_documents": 6,
  "openai_configured": true  // ← Shows if OpenAI is set up
}
```

---

## 🐛 Troubleshooting

### Issue: "Knowledge base is empty"

**Cause:** ChromaDB collection not initialized
**Fix:**
```bash
# Delete ChromaDB and restart backend
rm -rf %TEMP%/printguard/chromadb
# Backend will re-initialize on next start
```

### Issue: "AI assistant is not available"

**Cause:** `OPENAI_API_KEY` not set
**Options:**
1. Set the environment variable (see Step 2 above)
2. Use semantic search instead (works without OpenAI)

### Issue: Embedding model download fails

**Cause:** Network issues or rate limits
**Fix:**
```bash
# Set HuggingFace token for higher rate limits
export HF_TOKEN="hf_your-token"
# Or download manually:
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Issue: LangChain deprecation warnings

**Status:** These are warnings, not errors
**Impact:** System still works perfectly
**Message:**
```
LangChainDeprecationWarning: The class `HuggingFaceEmbeddings` was deprecated
```

**Optional Fix:** Update to newer package (already in requirements.txt)

---

## 📊 API Endpoints Reference

### 1. GET /api/rag/stats
**Purpose:** Get RAG system health and configuration
**Response:**
```json
{
  "total_documents": 6,
  "collection_name": "packaging_standards",
  "status": "ready",
  "openai_configured": false
}
```

### 2. GET /api/rag/search
**Purpose:** Semantic search in knowledge base
**Query Params:**
- `query` (required): Search query
- `k` (optional): Number of results (default 5)

**Example:**
```bash
curl "http://127.0.0.1:8000/api/rag/search?query=DPI&k=3"
```

### 3. POST /api/rag/chat
**Purpose:** AI-powered Q&A (requires OpenAI)
**Body:**
```json
{
  "question": "What is the minimum DPI for packaging?"
}
```

**Response (with OpenAI):**
```json
{
  "answer": "The industry standard minimum DPI for packaging is 300 DPI...",
  "sources": [...]
}
```

**Response (without OpenAI):**
```json
{
  "answer": "AI assistant is not available. Please configure OPENAI_API_KEY.",
  "sources": [],
  "error": "missing_api_key"
}
```

### 4. POST /api/rag/explain/{finding_id}
**Purpose:** Get AI explanation for inspection finding
**Query Params:**
- `inspection_id` (required): Inspection ID

**Example:**
```bash
curl -X POST "http://127.0.0.1:8000/api/rag/explain/RES-001-P1?inspection_id=abc123"
```

---

## 💡 Usage Tips

### 1. Use Semantic Search Even Without OpenAI

The semantic search works perfectly without any API keys:

```javascript
// In frontend or via API
fetch('/api/rag/search?query=bleed+requirements&k=3')
  .then(r => r.json())
  .then(data => console.log(data.results))
```

### 2. Add Your Own Documents

```python
from services.rag_service import get_rag_service

rag = get_rag_service()
rag.add_documents([
    {
        "content": "Your custom packaging standards here...",
        "metadata": {"source": "company_spec", "category": "internal"}
    }
])
```

### 3. Monitor RAG Performance

```bash
# Check status regularly
curl http://127.0.0.1:8000/api/rag/stats

# Test search relevance
curl "http://127.0.0.1:8000/api/rag/search?query=test&k=5"
```

---

## 🎓 Understanding the RAG System

### What is RAG?

**Retrieval-Augmented Generation** combines:
1. **Semantic Search** - Find relevant documents by meaning
2. **AI Generation** - Generate natural language answers
3. **Source Citation** - Show where answers came from

### How It Works in PrintGuard

```
User Question
    ↓
Embedding Model (local) → Convert to vector
    ↓
ChromaDB → Find similar documents
    ↓
Top 4 Results → Build context
    ↓
OpenAI (optional) → Generate answer
    ↓
Response with Sources
```

### Why Two Modes?

**Mode 1: Search Only (No OpenAI)**
- ✅ Works completely offline
- ✅ No API costs
- ✅ Returns raw document chunks
- ⚠️ User must read/interpret results

**Mode 2: AI Chat (With OpenAI)**
- ✅ Natural language answers
- ✅ Synthesizes information
- ✅ Easier to understand
- ⚠️ Requires API key and costs ~$0.002 per chat

---

## 📈 Next Steps

### Current Capabilities ✅
1. Semantic search working offline
2. 6 documents in knowledge base
3. Production checks integrated
4. Finding context retrieval

### To Enable AI Chat (Optional)
1. Get OpenAI API key
2. Set `OPENAI_API_KEY` environment variable
3. Restart backend
4. Test with `/api/rag/chat`

### To Enhance RAG System
1. Add company-specific packaging standards
2. Include printer specifications
3. Add substrate datasheets
4. Document common customer issues

---

## 🆘 Support

**Test RAG is working:**
```bash
curl http://127.0.0.1:8000/api/rag/stats
```

**Expected Output:**
```json
{"total_documents": 6, "status": "ready"}
```

**If not working:**
1. Check backend is running: `curl http://127.0.0.1:8000/api/health`
2. Check logs for errors: Look for `[RAG]` messages
3. Delete ChromaDB and restart: `rm -rf %TEMP%/printguard/chromadb`

---

**🎉 Congratulations! Your RAG system is ready to use!**

Even without OpenAI, you have powerful semantic search capabilities for packaging standards.
