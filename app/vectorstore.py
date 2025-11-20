from app.helpers import build_vectorstore, build_combined_vectorstore
from app.pdf_processor import process_pdf_directory, chunk_pdf_documents
from app.enhanced_helpers import EnhancedVectorstoreBuilder
from app.ingest_reporter import IngestReporter
from app.graph_store import get_graph_store
from config import (
    CHROMA_DB_PATH, INITIALIZE_VECTORSTORE,
    ENABLE_WEB_SOURCE, ENABLE_PDF_SOURCE, ENABLE_EXCEL_SOURCE, ENABLE_DOC_SOURCE, ENABLE_SHAREPOINT_SOURCE, ENABLE_OUTLOOK_SOURCE,
    WEB_SOURCE_URL, PDF_SOURCE_DIR, EXCEL_SOURCE_DIR, DOC_SOURCE_DIR, BLOG_START_PAGE,
    SHAREPOINT_SITE_URL, SHAREPOINT_START_PAGE,
    OUTLOOK_USER_EMAIL, OUTLOOK_FOLDER_NAME,
)
import os
import shutil
import json
import hashlib
from datetime import datetime
from typing import List
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from bm25_retriever import BM25Retriever

METADATA_FILE = "./data/vectorstore_metadata.json"

def get_file_hash(file_path):
    """Get MD5 hash of a file for change detection."""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None

def get_directory_hash(directory):
    """Get combined hash of all files in a directory."""
    if not os.path.exists(directory):
        return None
    
    hashes = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = get_file_hash(file_path)
            if file_hash:
                hashes.append(f"{file_path}:{file_hash}")
    
    if not hashes:
        return None
    
    combined = "|".join(sorted(hashes))
    return hashlib.md5(combined.encode()).hexdigest()

def get_current_metadata():
    """Get current metadata of enabled source files and directories."""
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "vectorstore_exists": os.path.exists(CHROMA_DB_PATH),
        "enabled_sources": []
    }
    
    # Only check enabled sources
    if ENABLE_WEB_SOURCE:
        metadata["url"] = WEB_SOURCE_URL
        metadata["web_pagination"] = {"start_page": BLOG_START_PAGE}
        metadata["enabled_sources"].append("web")
    
    if ENABLE_PDF_SOURCE:
        metadata["pdfs"] = get_directory_hash(PDF_SOURCE_DIR)
        metadata["enabled_sources"].append("pdfs")
    
    if ENABLE_EXCEL_SOURCE:
        metadata["excel"] = get_directory_hash(EXCEL_SOURCE_DIR)
        metadata["enabled_sources"].append("excel")
    
    if ENABLE_DOC_SOURCE:
        metadata["docs"] = get_directory_hash(DOC_SOURCE_DIR)
        metadata["enabled_sources"].append("docs")
    
    if ENABLE_SHAREPOINT_SOURCE:
        # Store SharePoint metadata - use empty string if start_page is not set (means Documents library)
        sharepoint_path = f"{SHAREPOINT_START_PAGE}" if SHAREPOINT_START_PAGE else "Documents Library"
        metadata["sharepoint"] = f"{SHAREPOINT_SITE_URL}/{sharepoint_path}"
        metadata["enabled_sources"].append("sharepoint")
    
    if ENABLE_OUTLOOK_SOURCE:
        # Store Outlook metadata - folder and user email
        metadata["outlook"] = f"{OUTLOOK_USER_EMAIL}/{OUTLOOK_FOLDER_NAME}"
        metadata["enabled_sources"].append("outlook")
    
    return metadata

def load_stored_metadata():
    """Load previously stored metadata."""
    if not os.path.exists(METADATA_FILE):
        return None
    
    try:
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_metadata(metadata):
    """Save current metadata."""
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def get_changed_sources():
    """Get list of sources that have changed (incremental rebuild)."""
    print("[*] Checking for changed sources...")
    
    # If vectorstore doesn't exist, all enabled sources need to be rebuilt
    if not os.path.exists(CHROMA_DB_PATH):
        print("[!] Vectorstore not found - all enabled sources need rebuild")
        current_metadata = get_current_metadata()
        return current_metadata.get("enabled_sources", [])
    
    # Load stored metadata
    stored_metadata = load_stored_metadata()
    if not stored_metadata:
        print("[!] No stored metadata found - all enabled sources need rebuild")
        current_metadata = get_current_metadata()
        return current_metadata.get("enabled_sources", [])
    
    # Get current metadata
    current_metadata = get_current_metadata()
    
    # Check which enabled sources have changed
    enabled_sources = current_metadata.get("enabled_sources", [])
    stored_enabled = stored_metadata.get("enabled_sources", [])
    changed_sources = []
    
    print(f"[*] Checking enabled sources: {', '.join(enabled_sources)}")
    print(f"[*] Stored enabled sources: {', '.join(stored_enabled)}")
    
    # Check if any NEW sources have been enabled
    new_sources = set(enabled_sources) - set(stored_enabled)
    if new_sources:
        print(f"[!] New sources detected: {', '.join(new_sources)}")
        changed_sources.extend(new_sources)
    
    # Check if any sources have changed their content
    for source in enabled_sources:
        if stored_metadata.get(source) != current_metadata.get(source):
            print(f"[!] {source} has changed")
            print(f"   Stored: {stored_metadata.get(source)}")
            print(f"   Current: {current_metadata.get(source)}")
            if source not in changed_sources:
                changed_sources.append(source)

    # Additional check: if web pagination changed, mark web as changed
    if "web" in enabled_sources:
        if stored_metadata.get("web_pagination") != current_metadata.get("web_pagination"):
            print("[!] web pagination settings have changed")
            changed_sources.append("web")
    
    if changed_sources:
        print(f"[*] Changed sources: {', '.join(changed_sources)}")
    else:
        print("[OK] No changes detected in enabled sources")
    
    return changed_sources

def should_rebuild_vectorstore():
    """Check if vectorstore needs to be rebuilt based on enabled source changes."""
    changed_sources = get_changed_sources()
    return len(changed_sources) > 0

def load_existing_vectorstore():
    """Load existing vectorstore without rebuilding with optimized HNSW indexing."""
    print("[*] Loading existing vectorstore with graph indexing (HNSW)...")
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # Configure ChromaDB with HNSW (graph-based) indexing for better retrieval
        # HNSW creates a hierarchical graph structure for efficient nearest neighbor search
        vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embeddings,
            collection_metadata={
                "hnsw:space": "cosine",  # Use cosine similarity for semantic search
                "hnsw:construction_ef": 200,  # Higher = better accuracy during indexing (default: 100)
                "hnsw:search_ef": 100,  # Higher = better search accuracy (default: 10)
                "hnsw:M": 48,  # Number of connections per node (default: 16, max: 64)
                # Higher M = more graph connections = better recall but more memory
            }
        )
        
        # Test if vectorstore is working
        total_docs = vectorstore._collection.count()
        print(f"[OK] Loaded vectorstore with {total_docs} documents")
        print(f"[OK] HNSW graph indexing enabled (M=48, search_ef=100)")
        return vectorstore
    except Exception as e:
        print(f"[!] Failed to load existing vectorstore: {e}")
        return None

def rebuild_vectorstore_if_needed():
    """Rebuild vectorstore incrementally - only process changed sources."""
    print("=" * 60)
    print("INCREMENTAL VECTORSTORE REBUILD")
    print("=" * 60)
    
    # Get changed sources
    changed_sources = get_changed_sources()
    
    if not changed_sources:
        print("[OK] No changes detected - using existing vectorstore")
        return load_existing_vectorstore()
    
    print(f"[*] Changed sources detected: {', '.join(changed_sources)}")
    
    # Use incremental rebuild for changed sources only
    vectorstore = build_incremental_vectorstore(changed_sources)
    
    # Save metadata after successful rebuild
    current_metadata = get_current_metadata()
    save_metadata(current_metadata)
    print("[OK] Saved vectorstore metadata for future change detection")
    
    return vectorstore

def build_incremental_vectorstore(changed_sources):
    """Build vectorstore incrementally - only process changed sources."""
    print(f"[*] Using enhanced full rebuild for incremental build (simple version)")
    return build_enhanced_vectorstore_full()
    
    # Load existing vectorstore
    print("[*] Loading existing vectorstore for incremental update...")
    existing_vectorstore = load_existing_vectorstore()
    if not existing_vectorstore:
        print("[!] Failed to load existing vectorstore - doing full rebuild")
        return build_selective_vectorstore()
    
    # Process only changed sources
    new_docs = []
    
    if "web" in changed_sources:
        print("[*] Processing changed web content...")
        from app.helpers import fetch_web_content
        web_docs = fetch_web_content(WEB_SOURCE_URL)
        new_docs.extend(web_docs)
        print(f"[OK] Fetched {len(web_docs)} web documents")
    
    if "pdfs" in changed_sources:
        print("[*] Processing changed PDF files...")
        from app.helpers import process_pdf_files
        pdf_docs = process_pdf_files(PDF_SOURCE_DIR)
        new_docs.extend(pdf_docs)
        print(f"[OK] Processed {len(pdf_docs)} PDF documents")
    
    if "excel" in changed_sources:
        print("[*] Processing changed Excel files...")
        from app.helpers import process_excel_files
        excel_docs = process_excel_files(EXCEL_SOURCE_DIR)
        new_docs.extend(excel_docs)
        print(f"[OK] Processed {len(excel_docs)} Excel documents")
    
    if "docs" in changed_sources:
        print("[*] Processing changed Word documents...")
        from app.helpers import process_doc_files
        doc_docs = process_doc_files(DOC_SOURCE_DIR)
        new_docs.extend(doc_docs)
        print(f"[OK] Processed {len(doc_docs)} Word documents")
    
    if "sharepoint" in changed_sources:
        print("[*] Processing changed SharePoint content...")
        print("[INFO] Keeping old SharePoint data - adding new SharePoint documents...")
        
        # Process and add new SharePoint content (keep old data)
        from app.sharepoint_processor import process_sharepoint_content
        try:
            sharepoint_docs = process_sharepoint_content()
            new_docs.extend(sharepoint_docs)
            print(f"[OK] Processed {len(sharepoint_docs)} new SharePoint documents")
            print("[INFO] Old SharePoint documents are preserved in vectorstore")
        except Exception as e:
            print(f"[ERROR] SharePoint processing failed: {e}")
    
    if "outlook" in changed_sources:
        print("[*] Processing changed Outlook email content...")
        from app.outlook_processor import process_outlook_content
        try:
            outlook_docs = process_outlook_content()
            new_docs.extend(outlook_docs)
            print(f"[OK] Processed {len(outlook_docs)} Outlook email documents")
        except Exception as e:
            print(f"[ERROR] Outlook processing failed: {e}")
    
    if not new_docs:
        print("[WARNING] No new documents found for changed sources")
        return existing_vectorstore
    
    # Add new documents to existing vectorstore in batches to avoid token limit
    print(f"[*] Adding {len(new_docs)} new documents to existing vectorstore in batches...")
    batch_size = 50  # Add 50 documents at a time to stay under token limit
    try:
        for i in range(0, len(new_docs), batch_size):
            batch = new_docs[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(new_docs) + batch_size - 1) // batch_size
            print(f"   [*] Adding batch {batch_num}/{total_batches} ({len(batch)} documents)...")
            existing_vectorstore.add_documents(batch)
        print(f"[OK] Successfully added all {len(new_docs)} documents to vectorstore in {total_batches} batches")
        return existing_vectorstore
    except Exception as e:
        print(f"[ERROR] Failed to add documents incrementally: {e}")
        print("[*] Falling back to full rebuild...")
        return build_selective_vectorstore()

def build_enhanced_vectorstore_full() -> Chroma:
    """
    Build vectorstore using EnhancedVectorstoreBuilder for ALL enabled sources.
    This is the main ingestion pipeline for Option E.
    """
    print("[*] Building enhanced vectorstore with semantic chunking + dedup + graph")

    builder = EnhancedVectorstoreBuilder()
    reporter = builder.reporter  # already created inside EnhancedVectorstoreBuilder

    all_chunks: List[Document] = []

    # ---- WEB / BLOG (if you use it) ----
    if ENABLE_WEB_SOURCE:
        try:
            from app.helpers import fetch_web_content
            from config import WEB_SOURCE_URL
            web_docs = fetch_web_content(WEB_SOURCE_URL)
            print(f"[INGEST] Web docs: {len(web_docs)}")
            chunks = builder.process_documents(web_docs, source_type="web")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[WARN] Web ingestion failed: {e}")

    # ---- PDF ----
    if ENABLE_PDF_SOURCE and os.path.exists(PDF_SOURCE_DIR):
        try:
            from app.helpers import process_pdf_files
            pdf_docs = process_pdf_files(PDF_SOURCE_DIR)
            print(f"[INGEST] PDF docs: {len(pdf_docs)}")
            chunks = builder.process_documents(pdf_docs, source_type="pdf")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[WARN] PDF ingestion failed: {e}")

    # ---- EXCEL ----
    if ENABLE_EXCEL_SOURCE and os.path.exists(EXCEL_SOURCE_DIR):
        try:
            from app.helpers import process_excel_files
            excel_docs = process_excel_files(EXCEL_SOURCE_DIR)
            print(f"[INGEST] Excel docs: {len(excel_docs)}")
            chunks = builder.process_documents(excel_docs, source_type="excel")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[WARN] Excel ingestion failed: {e}")

    # ---- WORD DOCS ----
    if ENABLE_DOC_SOURCE and os.path.exists(DOC_SOURCE_DIR):
        try:
            from app.helpers import process_doc_files
            doc_docs = process_doc_files(DOC_SOURCE_DIR)
            print(f"[INGEST] Word docs: {len(doc_docs)}")
            chunks = builder.process_documents(doc_docs, source_type="doc")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[WARN] Doc ingestion failed: {e}")

    # ---- SHAREPOINT ----
    if ENABLE_SHAREPOINT_SOURCE:
        try:
            from app.sharepoint_processor import process_sharepoint_content
            sp_docs = process_sharepoint_content()
            print(f"[INGEST] SharePoint docs: {len(sp_docs)}")
            chunks = builder.process_documents(sp_docs, source_type="sharepoint")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[WARN] SharePoint ingestion failed: {e}")

    # ---- OUTLOOK / EMAIL ----
    if ENABLE_OUTLOOK_SOURCE:
        try:
            from app.outlook_processor import process_outlook_content
            email_docs = process_outlook_content()
            print(f"[INGEST] Email docs: {len(email_docs)}")
            chunks = builder.process_documents(email_docs, source_type="email")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"[WARN] Outlook ingestion failed: {e}")

    print(f"[INGEST] Total enhanced chunks: {len(all_chunks)}")

    vectorstore = builder.build_vectorstore(
        all_chunks, persist_directory=CHROMA_DB_PATH
    )

    report = builder.get_report()
    print("\n===== ENHANCED INGEST REPORT =====")
    print(report)
    print("==================================\n")

    return vectorstore

def build_selective_vectorstore():
    """Build vectorstore with only enabled sources using enhanced pipeline (Option E)."""
    print("[*] Using enhanced full rebuild for selective build (Option E)")
    return build_enhanced_vectorstore_full()

def manage_vectorstore_backup_and_rebuild():
    """Manage vectorstore backup and rebuild with proper versioning."""
    import shutil
    from datetime import datetime
    import time
    
    # Create data directory if it doesn't exist
    os.makedirs("./data", exist_ok=True)
    
    backup_path = "./data/chroma_db_backup"
    current_path = CHROMA_DB_PATH
    
    print("=" * 60)
    print("VECTORSTORE BACKUP AND REBUILD MANAGEMENT")
    print("=" * 60)
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current vectorstore: {current_path}")
    print(f"Backup vectorstore: {backup_path}")
    print("-" * 60)
    
    # Step 1: Create backup of existing vectorstore (if it exists)
    if os.path.exists(current_path):
        try:
            # Remove old backup if it exists
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                print("[OK] Removed old backup vectorstore")
            
            # Create backup of current vectorstore
            shutil.copytree(current_path, backup_path)
            print("[OK] Created backup of existing vectorstore")
            print(f"  Backup created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"[WARNING] Could not create backup: {e}")
    else:
        print("[INFO] No existing vectorstore found - this will be the first build")
    
    # Step 2: Remove current vectorstore to force fresh rebuild
    if os.path.exists(current_path):
        try:
            shutil.rmtree(current_path)
            print("[OK] Removed current vectorstore for fresh rebuild")
        except Exception as e:
            print(f"[WARNING] Could not remove current vectorstore: {e}")
    
    # Step 3: Rebuild vectorstore with latest data
    print("[OK] Starting fresh vectorstore rebuild...")
    print("-" * 60)
    return rebuild_vectorstore_if_needed()

def initialize_vectorstore():
    """Smart vectorstore initialization that only rebuilds when needed."""
    print("=" * 60)
    print(">> INITIALIZING CF-CHATBOT KNOWLEDGE BASE")
    print("=" * 60)
    
    # Check if rebuild is needed
    if should_rebuild_vectorstore():
        print("[*] Rebuilding vectorstore...")
        vectorstore = rebuild_vectorstore_if_needed()
    else:
        # Try to load existing vectorstore
        vectorstore = load_existing_vectorstore()
        if vectorstore is None:
            print("[!] Failed to load existing vectorstore, rebuilding...")
            vectorstore = rebuild_vectorstore_if_needed()
    
    print("[OK] Vectorstore initialization complete!")
    print("=" * 60)
    return vectorstore

# Initialize vectorstore based on environment variable
def get_vectorstore():
    """Get vectorstore instance - always try to load existing, rebuild only if INITIALIZE_VECTORSTORE=true."""
    
    # First, try to load existing vectorstore (always attempt this)
    try:
        if os.path.exists(CHROMA_DB_PATH):
            print("[*] Loading existing vectorstore...")
            return load_existing_vectorstore()
        else:
            print("[!] No existing vectorstore found")
            # If no vectorstore exists and INITIALIZE_VECTORSTORE=true, create one
            if INITIALIZE_VECTORSTORE:
                print("[*] INITIALIZE_VECTORSTORE=true - creating new vectorstore...")
                return initialize_vectorstore()
            else:
                print("[*] INITIALIZE_VECTORSTORE=false - no vectorstore available")
                return None
    except Exception as e:
        print(f"[!] Failed to load existing vectorstore: {e}")
        # If loading fails and INITIALIZE_VECTORSTORE=true, try to rebuild
        if INITIALIZE_VECTORSTORE:
            print("[*] INITIALIZE_VECTORSTORE=true - attempting rebuild...")
            return initialize_vectorstore()
        else:
            return None

def check_and_rebuild_if_needed():
    """Check if rebuild is needed and rebuild only if INITIALIZE_VECTORSTORE=true."""
    if not INITIALIZE_VECTORSTORE:
        print("[*] INITIALIZE_VECTORSTORE=false - skipping rebuild check")
        return False
    
    print("[*] INITIALIZE_VECTORSTORE=true - checking if rebuild is needed...")
    
    # Check if rebuild is needed based on enabled sources
    if should_rebuild_vectorstore():
        print("[*] Rebuild needed - initializing vectorstore...")
        return initialize_vectorstore()
    else:
        print("[OK] No rebuild needed - using existing vectorstore")
        return True

# Initialize vectorstore - always try to load existing
vectorstore = get_vectorstore()

# Check if rebuild is needed (only if INITIALIZE_VECTORSTORE=true)
if INITIALIZE_VECTORSTORE:
    print("[*] INITIALIZE_VECTORSTORE=true - checking for rebuild...")
    rebuild_result = check_and_rebuild_if_needed()
    if rebuild_result:
        # Reload vectorstore after potential rebuild
        vectorstore = get_vectorstore()

if vectorstore:
    # Create a hybrid retriever with MMR (Maximal Marginal Relevance) for diverse results
    # MMR balances relevance with diversity to avoid redundant results
    retriever = vectorstore.as_retriever(
        search_type="mmr",  # Use MMR instead of plain similarity
        search_kwargs={
            "k": 25,  # Number of documents to return
            "fetch_k": 50,  # Fetch more candidates for MMR to choose from
            "lambda_mult": 0.7,  # Balance relevance (1.0) vs diversity (0.0) - 0.7 is good balance
        }
    )
    
    # Also create a similarity retriever as fallback
    similarity_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 25,
        }
    )
    
    print("[OK] Vectorstore available with hybrid retrieval:")
    print("    - Primary: MMR (Maximal Marginal Relevance) for diverse results")
    print("    - Graph indexing: HNSW for efficient similarity search")
    print("    - Fallback: Similarity search")
    
    # ============================================================================
    # OPTION E: BM25 INITIALIZATION
    # ============================================================================
    bm25_retriever = None
    try:
        print("[*] Building BM25 index for Option E hybrid retrieval...")
        # Pull all documents once for BM25
        # NOTE: Chroma exposes .get() to fetch docs
        all_docs_data = vectorstore.get(include=["metadatas", "documents"])
        raw_texts = all_docs_data["documents"]
        metadatas = all_docs_data["metadatas"]

        docs = []
        for text, meta in zip(raw_texts, metadatas):
            docs.append(Document(page_content=text, metadata=meta or {}))

        bm25_retriever = BM25Retriever(docs)
        print(f"[OK] BM25 index ready over {len(docs)} documents")
    except Exception as e:
        print(f"[WARN] Failed to build BM25 index: {e}")
        bm25_retriever = None
else:
    retriever = None
    similarity_retriever = None
    bm25_retriever = None
    print("[INFO] No vectorstore available - set INITIALIZE_VECTORSTORE=true to create one")