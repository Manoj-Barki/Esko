"""
RAG (Retrieval-Augmented Generation) service for packaging standards knowledge base.
Provides semantic search and AI-powered Q&A about packaging preflight rules.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI


class RAGService:
    """Manages vector database and RAG operations for packaging standards."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize RAG service with vector database.

        Args:
            storage_path: Path to store ChromaDB data. Defaults to temp directory.
        """
        self.storage_path = storage_path or Path(os.getenv("PRINTGUARD_STORAGE", Path.home() / ".printguard")) / "chromadb"
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize embeddings model (runs locally, no API key needed)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.storage_path),
            settings=Settings(anonymized_telemetry=False)
        )

        # Initialize vector store
        self.collection_name = "packaging_standards"
        self.vector_store = None
        self.llm = None

        # Check if OpenAI API key is available
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.3,
                api_key=self.openai_api_key
            )

        # Initialize if collection exists
        self._init_vector_store()

    def _init_vector_store(self):
        """Initialize vector store from existing collection."""
        try:
            # Check if collection exists
            collections = self.chroma_client.list_collections()
            if any(c.name == self.collection_name for c in collections):
                self.vector_store = Chroma(
                    client=self.chroma_client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings
                )
        except Exception as e:
            print(f"[RAG] Warning: Could not initialize vector store: {e}")

    def add_documents(self, documents: List[Dict[str, str]]):
        """
        Add documents to the knowledge base.

        Args:
            documents: List of dicts with 'content' and 'metadata' keys
        """
        if not documents:
            return

        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

        texts = []
        metadatas = []

        for doc in documents:
            chunks = text_splitter.split_text(doc['content'])
            for chunk in chunks:
                texts.append(chunk)
                metadatas.append(doc.get('metadata', {}))

        # Create or update vector store
        if self.vector_store is None:
            self.vector_store = Chroma.from_texts(
                texts=texts,
                embedding=self.embeddings,
                metadatas=metadatas,
                client=self.chroma_client,
                collection_name=self.collection_name
            )
        else:
            self.vector_store.add_texts(texts=texts, metadatas=metadatas)

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search in the knowledge base.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of search results with content and metadata
        """
        if not self.vector_store:
            return []

        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score)
                }
                for doc, score in results
            ]
        except Exception as e:
            print(f"[RAG] Search error: {e}")
            return []

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question using RAG (requires OpenAI API key).

        Args:
            question: User's question

        Returns:
            Dict with 'answer' and 'sources'
        """
        if not self.llm:
            return {
                "answer": "AI assistant is not available. Please configure OPENAI_API_KEY environment variable.",
                "sources": [],
                "error": "missing_api_key"
            }

        if not self.vector_store:
            return {
                "answer": "Knowledge base is empty. Please add documents first.",
                "sources": [],
                "error": "empty_knowledge_base"
            }

        try:
            # Get relevant documents
            docs = self.vector_store.similarity_search(question, k=4)

            # Build context from retrieved documents
            context = "\n\n".join([doc.page_content for doc in docs])

            # Create prompt
            prompt = f"""You are a packaging preflight expert assistant for PrintGuard AI.
Use the following context from packaging standards and documentation to answer the question.
If you don't know the answer based on the context, say so - don't make up information.

Context: {context}

Question: {question}

Provide a clear, concise answer with specific details when relevant (like DPI values, measurements, etc.).
If applicable, reference the standard or rule that supports your answer.

Answer:"""

            # Get LLM response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)

            # Prepare sources
            sources = []
            for doc in docs:
                sources.append({
                    "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                    "metadata": doc.metadata
                })

            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "error": str(e)
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        if not self.vector_store:
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "status": "empty"
            }

        try:
            collection = self.chroma_client.get_collection(self.collection_name)
            count = collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "status": "ready",
                "openai_configured": bool(self.openai_api_key)
            }
        except Exception as e:
            return {
                "total_documents": 0,
                "collection_name": self.collection_name,
                "status": "error",
                "error": str(e)
            }


# Global RAG service instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the global RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def initialize_knowledge_base():
    """Initialize the knowledge base with default packaging standards documents."""
    rag = get_rag_service()

    # Check if already initialized
    stats = rag.get_stats()
    if stats["total_documents"] > 0:
        print(f"[RAG] Knowledge base already initialized with {stats['total_documents']} documents")
        return

    print("[RAG] Initializing knowledge base with default documents...")

    # Default packaging standards documents
    documents = [
        {
            "content": """
# Image Resolution Standards for Packaging

**Minimum DPI Requirements:**
- **300 DPI**: Industry standard for high-quality offset printing on coated stock
- **150 DPI**: Acceptable warning threshold for some applications
- **72 DPI**: Critical threshold - images below this will show visible pixelation

**Substrate-Specific Requirements:**
- Flexible packaging: 300 DPI minimum for photographic images
- Corrugated cartons: 200 DPI minimum acceptable
- Labels: 300-600 DPI depending on viewing distance
- Large format (posters, displays): 150 DPI may be acceptable

**Effective DPI Calculation:**
The effective DPI is calculated based on the image's pixel dimensions and the physical print size.
Formula: Effective DPI = Image Width (pixels) / Print Width (inches)

**ISO 12647-2 Standards:**
According to ISO 12647-2 for offset lithographic printing, images should maintain a minimum resolution of 300 DPI at final output size to ensure optimal quality.
            """,
            "metadata": {"source": "resolution_standards", "category": "image_quality"}
        },
        {
            "content": """
# Dieline and Geometry Standards

**Minimum Text Clearance:**
- **3mm (0.118 inches)**: Minimum distance from text to cut/fold lines
- **5mm (0.197 inches)**: Recommended for flexible packaging due to registration tolerances

**Safe Area Margins:**
- **3mm minimum**: Inset from page edge for critical content
- **5mm recommended**: For important text and branding elements

**Dieline Detection:**
- Dielines are typically defined using specific stroke colors (e.g., magenta, cyan for cut/fold)
- Layer naming conventions: "dieline", "cut", "fold", "crease"
- Dashed lines often indicate fold lines vs. solid lines for cuts

**Common Issues:**
- Text crossing dielines can lead to cut-off content
- Insufficient clearance may result in text appearing too close to edges after trimming
- Die-cutting tolerances can vary by ±0.5mm, requiring adequate safety margins
            """,
            "metadata": {"source": "dieline_standards", "category": "geometry"}
        },
        {
            "content": """
# PrintGuard AI Rules Explained

**RES-001: Effective Image Resolution**
- **Purpose**: Flags raster imagery below configured DPI thresholds
- **Warning Threshold**: Default 150 DPI
- **Critical Threshold**: Default 72 DPI
- **How to Fix**: Replace with higher resolution images or reduce print size

**GEOM-001: Text Near Cut/Fold Geometry**
- **Purpose**: Detects text crossing or too close to dieline geometry
- **Min Clearance**: Default 3.0mm
- **How to Fix**: Move text away from cut/fold lines, adjust layout

**SAFE-001: Safe-Area Boundary**
- **Purpose**: Flags text outside the configured safe area near page edge
- **Safe Margin**: Default 3.0mm from edge
- **How to Fix**: Move content inward from page edges

**BLEED-001: Bleed Validation**
- **Purpose**: Validates adequate bleed areas for production printing
- **Industry Standard**: 3mm (0.118 inches) on all sides
- **Critical Threshold**: < 1.5mm bleed triggers critical error
- **How to Fix**: Extend artwork 3mm beyond trim lines on all sides

**TRIM-001: Trim Mark Detection**
- **Purpose**: Detects presence of trim/crop marks for production cutting
- **Expected**: Minimum 4 trim marks (corners)
- **How to Fix**: Add trim marks using design software's crop mark feature, standard placement 6mm from trim edge

**FONT-001: Font Embedding**
- **Purpose**: Ensures all fonts are embedded or subsetted in PDF
- **Severity**: Critical - prevents RIP failures
- **How to Fix**: Re-export PDF with 'Embed All Fonts' or 'Subset Fonts' enabled

**OVERPRINT-001: White Overprint Detection**
- **Purpose**: Detects white elements set to overprint (causes disappearing elements)
- **Severity**: Warning (detection has limitations)
- **How to Fix**: Ensure overprint is OFF for white fills/strokes, use 'Overprint Preview' in Acrobat

**TEXT-001: Small Text Legibility**
- **Purpose**: Validates minimum text sizes for readability
- **Standards**: 6pt general (coated), 7pt reversed, 8pt uncoated
- **Critical Threshold**: < 5pt text
- **How to Fix**: Increase text size to meet legibility standards for substrate type

**Configurable Settings:**
All thresholds can be overridden per inspection or set as defaults in rules configuration.
            """,
            "metadata": {"source": "printguard_rules", "category": "application_specific"}
        },
        {
            "content": """
# Common Packaging Defects and Solutions

**Low Resolution Images:**
- **Symptom**: Pixelated or blurry images
- **Cause**: Image DPI below 300 for print size
- **Solution**: Use higher resolution source files, reduce print dimensions, or vectorize simple graphics
- **Rule**: RES-001

**Text Too Close to Cut Lines:**
- **Symptom**: Text appears cut off or too close to edges
- **Cause**: Insufficient clearance from dieline
- **Solution**: Reposition text 3-5mm away from cut/fold lines
- **Rule**: GEOM-001

**Insufficient Bleed:**
- **Symptom**: White edges after trimming, artwork doesn't extend to edge
- **Cause**: Bleed area less than 3mm industry standard
- **Solution**: Extend artwork 3mm beyond trim lines on all sides
- **Rule**: BLEED-001

**Missing Trim Marks:**
- **Symptom**: No visual guides for cutting
- **Cause**: Crop marks not added to PDF
- **Solution**: Add trim marks 6mm from trim edge using design software
- **Rule**: TRIM-001

**Font Embedding Issues:**
- **Symptom**: Text displays incorrectly or missing
- **Cause**: Fonts not embedded in PDF
- **Solution**: Re-export with 'Embed All Fonts' or 'Subset Fonts' enabled
- **Rule**: FONT-001

**White Overprint Issues:**
- **Symptom**: White elements disappear in print
- **Cause**: White set to overprint instead of knockout
- **Solution**: Set overprint OFF for white, verify in Overprint Preview
- **Rule**: OVERPRINT-001

**Illegible Small Text:**
- **Symptom**: Text too small to read when printed
- **Cause**: Font size below minimum standards (6pt general, 7pt reversed)
- **Solution**: Increase text size to meet legibility thresholds
- **Rule**: TEXT-001

**Color Registration Issues:**
- **Symptom**: Misaligned colors, white gaps
- **Cause**: Poor trapping, tight registration on flexible materials
- **Solution**: Increase clearances on flexible packaging, use trapping

**Barcode Readability:**
- **Symptom**: Scanners cannot read barcodes
- **Cause**: Insufficient contrast, bars too thin, quiet zones violated
- **Solution**: Maintain minimum bar widths, ensure adequate contrast ratio, preserve quiet zones
            """,
            "metadata": {"source": "common_defects", "category": "troubleshooting"}
        },
        {
            "content": """
# Substrate-Specific Guidelines

**Flexible Packaging (Films, Pouches):**
- Higher registration tolerances: use 5mm clearances
- Account for material stretch during filling
- Higher resolution requirements for photographic quality

**Corrugated Cartons:**
- Lower resolution acceptable (200 DPI minimum)
- Larger safety margins due to board flex
- Consider flute direction for fine details

**Labels (Paper/Film):**
- 300-600 DPI depending on label size
- Small labels need higher DPI for readability
- Consider adhesive bleed when designing

**Folding Cartons (Paperboard):**
- 300 DPI standard
- 3mm safety margins typical
- Score lines require adequate clearance for clean folds

**Large Format (Displays, Posters):**
- Viewing distance affects DPI requirements
- 150 DPI may be acceptable for distant viewing
- Larger safety margins for rough cutting methods
            """,
            "metadata": {"source": "substrate_guidelines", "category": "materials"}
        }
    ]

    rag.add_documents(documents)
    print(f"[RAG] Knowledge base initialized with {len(documents)} documents")
