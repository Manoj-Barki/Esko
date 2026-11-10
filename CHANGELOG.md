# PrintGuard AI - Changelog

## [Unreleased] - 2026-11-10

### 🎉 Major Features Added

#### 🤖 AI Assistant & RAG System
- **NEW: Dedicated AI Assistant Tab** - Full chat interface for asking questions about packaging standards
- **RAG (Retrieval-Augmented Generation)** - Implemented using ChromaDB vector database and HuggingFace embeddings
- **Knowledge Base** - Pre-loaded with 5 comprehensive documents:
  - Image Resolution Standards (ISO 12647-2, DPI requirements)
  - Dieline and Geometry Standards (clearances, safe areas)
  - PrintGuard Rules Explained (RES-001, GEOM-001, SAFE-001)
  - Common Packaging Defects and Solutions
  - Substrate-Specific Guidelines
- **Contextual Help** - "Get AI explanation" button on every finding
- **Semantic Search** - Find relevant standards using natural language (works without API key)
- **Source Citations** - Every AI answer shows which knowledge base documents were used
- **Optional OpenAI Integration** - Set OPENAI_API_KEY for AI-generated answers

#### 📤 Multi-File Upload System
- **Drag-and-Drop Interface** - Upload multiple files simultaneously
- **Batch Upload Support** - Process multiple files in sequence
- **Client-Side Validation** - Validate file types (PDF/PNG/JPEG) and sizes before upload
- **Real-Time Progress Tracking** - Individual status for each file (uploading/completed/error)
- **File Management** - Add/remove files before uploading
- **Error Handling** - Clear error messages for invalid files

### 🔧 Technical Improvements

#### Backend
- Added 4 new RAG API endpoints:
  - `POST /api/rag/chat` - Ask questions using RAG
  - `GET /api/rag/search` - Semantic search in knowledge base
  - `POST /api/rag/explain/{finding_id}` - Get AI explanations for findings
  - `GET /api/rag/stats` - Knowledge base statistics
- Implemented `RAGService` class with vector database management
- Auto-initialization of knowledge base on startup
- Added support for HuggingFace embeddings (local, no API key needed)
- Integrated LangChain for RAG orchestration

#### Frontend
- Created `AssistantView.jsx` - Full-featured AI chat interface
- Enhanced `UploadView.jsx` - Multi-file support with progress indicators
- Updated `ResultView.jsx` - Added AI explanation feature for findings
- Extended `api.js` - Added RAG endpoint methods
- New CSS components for chat interface and AI explanations

#### Dependencies Added
- `langchain>=0.1.0`
- `langchain-community>=0.0.20`
- `langchain-openai>=0.0.5`
- `langchain-text-splitters>=0.0.1`
- `chromadb>=0.4.22`
- `sentence-transformers>=2.3.0`
- `openai>=1.12.0`
- `python-dotenv>=1.0.0`

### 📝 Documentation
- Updated architecture diagram to include RAG components
- Added AI Assistant section to features
- Documented new API endpoints
- Added environment variable for OPENAI_API_KEY
- Included troubleshooting for RAG-related issues
- Added first-time setup notes for embedding model download

### 🎨 UI/UX Enhancements
- New "AI Assistant" navigation tab
- Chat interface with typing indicators
- Message history with user/assistant differentiation
- Suggested questions for new users
- Collapsible source citations
- Color-coded upload progress (cyan=uploading, green=completed, red=error)
- File size display for selected files
- Real-time status badges

### 🔐 Security & Privacy
- All RAG processing happens locally except OpenAI API calls
- Vector embeddings stored in local ChromaDB
- No data sent to external services without explicit API key configuration
- Semantic search fully functional without any API keys

### 📊 Performance
- Embedding model downloads once (~90MB) and caches locally
- Semantic search operates on local vector database
- Sequential file upload to prevent server overload
- Efficient chunk-based document processing (1000 chars with 200 overlap)

### 🐛 Bug Fixes
- Fixed langchain import issues for newer versions
- Resolved Python cache conflicts during development
- Corrected auto-reload behavior with large imports

### ⚠️ Breaking Changes
None - All changes are additive and backward compatible

### 📦 Migration Notes
To use the new features:
1. Install updated dependencies: `pip install -r requirements.txt`
2. First backend startup will download embedding model (~90MB)
3. (Optional) Set `OPENAI_API_KEY` environment variable for AI Q&A
4. Install frontend dependencies: `npm install` (no changes, but recommended)

### 🚀 What's Working
- ✅ Multi-file drag-and-drop upload
- ✅ Client-side validation
- ✅ Sequential upload with progress tracking
- ✅ RAG knowledge base (5 documents, ~30 chunks)
- ✅ Semantic search (no API key needed)
- ✅ AI chat interface
- ✅ Contextual finding explanations
- ✅ Source citations
- ✅ Knowledge base statistics

### 💡 Known Limitations
- AI Q&A requires OpenAI API key (semantic search works without it)
- Files process sequentially (not in parallel)
- First startup downloads embedding model (one-time, ~90MB)
- RAG responses depend on knowledge base coverage
- ChromaDB requires local storage permissions

### 🎯 Next Steps
Remaining from Phase 1 plan:
- PDF report generation (alongside HTML)
- CSV export for findings
- Email report delivery
- Shareable inspection links with expiry
- Approval/rejection workflow states
- Approval history and audit trail
- User comments on findings
- Notification system

---

## How to Test New Features

### Test Multi-File Upload
1. Open http://localhost:3000
2. Go to "Inspect" tab
3. Drag multiple PDF/PNG/JPEG files onto the drop zone
4. Observe individual file validation and progress tracking
5. Files upload sequentially with status indicators

### Test AI Assistant
1. Open http://localhost:3000
2. Click "AI Assistant" tab
3. Try suggested questions or ask:
   - "What is the minimum DPI for packaging?"
   - "How much clearance from cut lines?"
   - "What causes low resolution warnings?"
4. View sources by clicking "Sources (N)"

### Test Finding Explanations
1. Upload a file with findings
2. Click on a finding to expand it
3. Click "🤖 Get AI explanation"
4. View detailed explanation with sources

### Test Without OpenAI Key
1. Don't set OPENAI_API_KEY
2. AI Assistant shows friendly message about needing API key
3. Semantic search still works
4. Finding explanations show informative message

---

**Summary**: This release adds comprehensive AI assistance to PrintGuard using RAG technology, along with multi-file upload capabilities. The system provides instant access to packaging standards knowledge while maintaining the existing preflight inspection functionality.
