from app.helpers import build_vectorstore, build_combined_vectorstore
from app.pdf_processor import process_pdf_directory, chunk_pdf_documents
from config import (
    CHROMA_DB_PATH, INITIALIZE_VECTORSTORE,
    ENABLE_WEB_SOURCE, ENABLE_PDF_SOURCE, ENABLE_EXCEL_SOURCE, ENABLE_DOC_SOURCE, ENABLE_SHAREPOINT_SOURCE,
    WEB_SOURCE_URL, PDF_SOURCE_DIR, EXCEL_SOURCE_DIR, DOC_SOURCE_DIR, BLOG_START_PAGE,
    SHAREPOINT_SITE_URL, SHAREPOINT_START_PAGE,
    ENABLE_TEAMS_TRANSCRIPTS, TEAMS_TRANSCRIPT_DAYS_BACK,
    VECTORSTORE_BACKEND, MONGODB_VECTORSTORE_COLLECTION,
)
import os
import shutil
import json
import hashlib
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Import MongoDB vector store if backend is set to MongoDB
if VECTORSTORE_BACKEND == "mongodb":
    try:
        from app.mongodb_vectorstore import MongoDBVectorStore
        MONGODB_AVAILABLE = True
        print("[*] MongoDB vector store backend selected")
    except ImportError as e:
        MONGODB_AVAILABLE = False
        print(f"[WARNING] MongoDB vector store not available: {e}")
        print("[*] Falling back to ChromaDB")
else:
    MONGODB_AVAILABLE = False

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
        metadata["sharepoint"] = f"{SHAREPOINT_SITE_URL}{SHAREPOINT_START_PAGE}"
        metadata["enabled_sources"].append("sharepoint")
    
    if 'ENABLE_TEAMS_TRANSCRIPTS' in globals() and ENABLE_TEAMS_TRANSCRIPTS:
        metadata["teams_transcripts"] = f"teams_last_{TEAMS_TRANSCRIPT_DAYS_BACK}_days"
        metadata["enabled_sources"].append("teams_transcripts")
    
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
    """Load existing vectorstore without rebuilding."""
    print(f"[*] Loading existing vectorstore (backend: {VECTORSTORE_BACKEND})...")
    
    try:
        embeddings = OpenAIEmbeddings()
        
        # Use MongoDB backend if configured
        if VECTORSTORE_BACKEND == "mongodb" and MONGODB_AVAILABLE:
            vectorstore = MongoDBVectorStore(
                collection_name=MONGODB_VECTORSTORE_COLLECTION,
                embedding_function=embeddings
            )
            stats = vectorstore.get_collection_stats()
            total_docs = stats["total_documents"]
            print(f"[OK] Loaded MongoDB vectorstore with {total_docs} documents")
            return vectorstore
        
        # Default: Use ChromaDB
        else:
            vectorstore = Chroma(
                persist_directory=CHROMA_DB_PATH,
                embedding_function=embeddings
            )
            
            # Test if vectorstore is working
            total_docs = vectorstore._collection.count()
            print(f"[OK] Loaded ChromaDB vectorstore with {total_docs} documents")
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
    from app.helpers import build_vectorstore, build_combined_vectorstore
    
    print(f"[*] Incremental rebuild for changed sources: {', '.join(changed_sources)}")
    
    # If no vectorstore exists, do full rebuild
    if not os.path.exists(CHROMA_DB_PATH):
        print("[*] No existing vectorstore - doing full rebuild")
        return build_selective_vectorstore()
    
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
        from app.sharepoint_processor import process_sharepoint_content
        try:
            sharepoint_docs = process_sharepoint_content()
            new_docs.extend(sharepoint_docs)
            print(f"[OK] Processed {len(sharepoint_docs)} SharePoint documents")
        except Exception as e:
            print(f"[ERROR] SharePoint processing failed: {e}")
    
    if "teams_transcripts" in changed_sources:
        print("[*] Processing Teams meeting transcripts...")
        from app.helpers import process_teams_transcripts
        try:
            from config import TEAMS_TRANSCRIPT_USER_EMAILS, TEAMS_TRANSCRIPT_DAYS_BACK
            teams_docs = process_teams_transcripts(
                user_emails=TEAMS_TRANSCRIPT_USER_EMAILS,
                days_back=TEAMS_TRANSCRIPT_DAYS_BACK,
            )
            new_docs.extend(teams_docs)
            print(f"[OK] Processed {len(teams_docs)} Teams transcripts")
        except Exception as e:
            print(f"[ERROR] Teams transcript processing failed: {e}")
    
    if not new_docs:
        print("[WARNING] No new documents found for changed sources")
        return existing_vectorstore
    
    # Add new documents to existing vectorstore
    print(f"[*] Adding {len(new_docs)} new documents to existing vectorstore...")
    try:
        existing_vectorstore.add_documents(new_docs)
        print("[OK] Successfully added new documents to vectorstore")
        return existing_vectorstore
    except Exception as e:
        print(f"[ERROR] Failed to add documents incrementally: {e}")
        print("[*] Falling back to full rebuild...")
        return build_selective_vectorstore()

def build_selective_vectorstore():
    """Build vectorstore with only enabled sources."""
    from app.helpers import build_vectorstore, build_combined_vectorstore
    
    # Collect enabled sources
    enabled_dirs = []
    enabled_sources = []
    
    # Check web source
    if ENABLE_WEB_SOURCE:
        enabled_sources.append("web")
    
    # Check PDF source
    if ENABLE_PDF_SOURCE and os.path.exists(PDF_SOURCE_DIR):
        enabled_dirs.append(PDF_SOURCE_DIR)
        enabled_sources.append("pdf")
    
    # Check Excel source
    if ENABLE_EXCEL_SOURCE and os.path.exists(EXCEL_SOURCE_DIR):
        enabled_dirs.append(EXCEL_SOURCE_DIR)
        enabled_sources.append("excel")
    
    # Check Word source
    if ENABLE_DOC_SOURCE and os.path.exists(DOC_SOURCE_DIR):
        enabled_dirs.append(DOC_SOURCE_DIR)
        enabled_sources.append("doc")
    
    # Check SharePoint source
    if ENABLE_SHAREPOINT_SOURCE:
        enabled_sources.append("sharepoint")
    
    # Check Teams transcripts source
    if 'ENABLE_TEAMS_TRANSCRIPTS' in globals() and ENABLE_TEAMS_TRANSCRIPTS:
        enabled_sources.append("teams_transcripts")
    
    print(f"Building vectorstore with sources: {', '.join(enabled_sources)}")
    
    # Build based on enabled sources
    if len(enabled_sources) == 1 and "web" in enabled_sources:
        # Only web source enabled
        return build_vectorstore(WEB_SOURCE_URL)
    elif enabled_dirs or ENABLE_SHAREPOINT_SOURCE or (('ENABLE_TEAMS_TRANSCRIPTS' in globals()) and ENABLE_TEAMS_TRANSCRIPTS):
        # Multiple sources enabled
        pdf_dir = PDF_SOURCE_DIR if ENABLE_PDF_SOURCE else None
        excel_dir = EXCEL_SOURCE_DIR if ENABLE_EXCEL_SOURCE else None
        doc_dir = DOC_SOURCE_DIR if ENABLE_DOC_SOURCE else None
        
        return build_combined_vectorstore(
            WEB_SOURCE_URL if ENABLE_WEB_SOURCE else None,
            pdf_dir, excel_dir, doc_dir, ENABLE_SHAREPOINT_SOURCE
        )
    else:
        # No sources enabled - create empty vectorstore
        print("Warning: No sources enabled!")
        return build_vectorstore(WEB_SOURCE_URL)  # Fallback to web

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
        # Check if vectorstore exists based on backend
        if VECTORSTORE_BACKEND == "mongodb" and MONGODB_AVAILABLE:
            # For MongoDB, always try to connect (collection may exist)
            print("[*] Loading MongoDB vectorstore...")
            return load_existing_vectorstore()
        
        elif os.path.exists(CHROMA_DB_PATH):
            # For ChromaDB, check if directory exists
            print("[*] Loading ChromaDB vectorstore...")
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
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 25  # Fetch more documents for better coverage
        }
    )
    print("[OK] Vectorstore available for chatbot")
else:
    retriever = None
    print("[INFO] No vectorstore available - set INITIALIZE_VECTORSTORE=true to create one")