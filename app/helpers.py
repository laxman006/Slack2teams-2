import os
import requests
import json
import markdown
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from config import CHROMA_DB_PATH, BLOG_POSTS_PER_PAGE, BLOG_MAX_PAGES, BLOG_START_PAGE
from app.pdf_processor import process_pdf_directory, chunk_pdf_documents
from app.excel_processor import process_excel_directory, chunk_excel_documents
from app.doc_processor import process_doc_directory, chunk_doc_documents
from app.sharepoint_processor import process_sharepoint_content


def fetch_posts(base_url: str, per_page=10, max_pages=6, start_page=1, extra_params: dict | None = None):
    """Fetch posts from WordPress API with pagination support.

    start_page allows continuing from a specific page (e.g., 4 to skip first 3 pages).
    """
    all_posts = []
    page = start_page
    session = requests.Session()
    
    while page <= max_pages:
        # Build query with preserved params + pagination
        params = dict(extra_params or {})
        params["per_page"] = per_page
        params["page"] = page
        url = f"{base_url}?{urlencode(params, doseq=True)}"
        print(f"Fetching: {url}")
        try:
            resp = session.get(url, timeout=60, stream=True)
            resp.raise_for_status()
            posts = json.loads(resp.content.decode("utf-8"))
            if not posts:
                break
            all_posts.extend(posts)
            print(f"Page {page} fetched, total so far: {len(all_posts)}")
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
        page += 1
    
    return all_posts

def load_webpage(url: str):
    """Fetch posts from WordPress API and return raw text."""
    # Check if URL contains pagination parameters to determine if we should use pagination
    if "per_page=" in url and "page=" in url:
        # Single page request - use original method
        response = requests.get(url)
        data = response.json()
    else:
        # Use pagination while preserving existing query params like tags/category
        parsed = urlparse(url)
        base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        base_params = dict(parse_qsl(parsed.query))
        # Remove any explicit page from preserved params (we control it)
        base_params.pop("page", None)
        # Respect configured per_page; remove to avoid duplication
        base_params.pop("per_page", None)
        data = fetch_posts(
            base_url,
            per_page=BLOG_POSTS_PER_PAGE,
            max_pages=BLOG_MAX_PAGES,
            start_page=BLOG_START_PAGE,
            extra_params=base_params,
        )
    
    texts = []
    for post in data:
        if "content" in post and "rendered" in post["content"]:
            texts.append(post["content"]["rendered"])
    return "\n\n".join(texts)

def fetch_web_content(url: str):
    """Fetch and chunk web content into LangChain Documents for incremental updates.

    Respects BLOG_POSTS_PER_PAGE, BLOG_MAX_PAGES, and BLOG_START_PAGE to allow
    continuing partial fetches without reprocessing earlier pages.
    """
    # Load raw text via pagination-aware loader
    raw_text = load_webpage(url)

    # Clean HTML tags from web content for better semantic search
    print("Cleaning HTML tags from web content...")
    soup = BeautifulSoup(raw_text, "html.parser")
    clean_text = soup.get_text(separator="\n", strip=True)
    print(f"[OK] Cleaned web content: {len(raw_text)} chars -> {len(clean_text)} chars")

    # Chunking strategy consistent with vectorstore builders
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=300,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    docs = splitter.create_documents([clean_text])

    # Add metadata for source tracking
    # Use simple string values to avoid Chroma's complex metadata error
    for doc in docs:
        doc.metadata["source_type"] = "web"
        doc.metadata["source"] = "cloudfuze_blog"
        doc.metadata["fetch_config"] = f"pages_{BLOG_START_PAGE}-{BLOG_MAX_PAGES}_per_{BLOG_POSTS_PER_PAGE}"

    return docs

def strip_markdown(md_text: str) -> str:
    """Convert Markdown/HTML to plain text."""
    html = markdown.markdown(md_text)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text()

def preserve_markdown(md_text: str) -> str:
    """Preserve Markdown formatting for better display."""
    # Clean up any HTML tags that might interfere with Markdown
    soup = BeautifulSoup(md_text, "html.parser")
    clean_text = soup.get_text()
    
    # Return the clean Markdown text (don't convert to HTML)
    return clean_text

def build_vectorstore(url: str):
    """Build and persist embeddings for web documents."""
    raw_text = load_webpage(url)
    
    # CRITICAL: Clean HTML tags from web content for better semantic search
    print("Cleaning HTML tags from web content...")
    soup = BeautifulSoup(raw_text, "html.parser")
    clean_text = soup.get_text(separator="\n", strip=True)
    print(f"[OK] Cleaned web content: {len(raw_text)} chars -> {len(clean_text)} chars")
    
    # Use larger chunks with more overlap for better semantic search
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,  # Larger chunks for more context
        chunk_overlap=300,  # More overlap to maintain context across chunks
        separators=["\n\n", "\n", ". ", " ", ""]  # Smart splitting by paragraphs, sentences
    )
    docs = splitter.create_documents([clean_text])
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(docs, embeddings, persist_directory=CHROMA_DB_PATH)
    return vectorstore

def build_combined_vectorstore(url: str = None, pdf_directory: str = None, excel_directory: str = None, doc_directory: str = None, sharepoint_enabled: bool = False):
    """Build and persist embeddings for enabled sources only."""
    all_docs = []
    
    # Process web content if URL provided
    if url:
        print("Loading web content...")
        raw_text = load_webpage(url)
        
        # CRITICAL: Clean HTML tags from web content for better semantic search
        print("Cleaning HTML tags from web content...")
        soup = BeautifulSoup(raw_text, "html.parser")
        clean_text = soup.get_text(separator="\n", strip=True)
        print(f"[OK] Cleaned web content: {len(raw_text)} chars -> {len(clean_text)} chars")
        
        # Use larger chunks with more overlap for better semantic search
        web_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,  # Larger chunks for more context
            chunk_overlap=300,  # More overlap to maintain context across chunks
            separators=["\n\n", "\n", ". ", " ", ""]  # Smart splitting by paragraphs, sentences
        )
        web_docs = web_splitter.create_documents([clean_text])
        
        # Add source metadata to web docs
        for doc in web_docs:
            doc.metadata["source_type"] = "web"
            doc.metadata["source"] = "cloudfuze_blog"
        
        all_docs.extend(web_docs)
        print(f"  - Web documents: {len(web_docs)}")
    else:
        print("Web content disabled - skipping...")
    
    # Process PDF documents if directory provided
    if pdf_directory and os.path.exists(pdf_directory):
        print("Processing PDF documents...")
        pdf_docs = process_pdf_directory(pdf_directory)
        pdf_chunks = chunk_pdf_documents(pdf_docs, chunk_size=1000, chunk_overlap=200)
        all_docs.extend(pdf_chunks)
        print(f"  - PDF documents: {len(pdf_chunks)}")
    else:
        print("PDF processing disabled or directory not found - skipping...")
    
    # Process Excel files if directory provided
    if excel_directory and os.path.exists(excel_directory):
        print("Processing Excel documents...")
        excel_docs = process_excel_directory(excel_directory)
        excel_chunks = chunk_excel_documents(excel_docs, chunk_size=1000, chunk_overlap=200)
        all_docs.extend(excel_chunks)
        print(f"  - Excel documents: {len(excel_chunks)}")
    else:
        print("Excel processing disabled or directory not found - skipping...")
    
    # Process Word documents if directory provided
    if doc_directory and os.path.exists(doc_directory):
        print("Processing Word documents...")
        doc_docs = process_doc_directory(doc_directory)
        doc_chunks = chunk_doc_documents(doc_docs, chunk_size=1000, chunk_overlap=200)
        all_docs.extend(doc_chunks)
        print(f"  - Word documents: {len(doc_chunks)}")
    else:
        print("Word document processing disabled or directory not found - skipping...")
    
    # Process SharePoint content if enabled
    if sharepoint_enabled:
        print("Processing SharePoint content...")
        try:
            sharepoint_docs = process_sharepoint_content()
            all_docs.extend(sharepoint_docs)
            print(f"  - SharePoint documents: {len(sharepoint_docs)}")
        except Exception as e:
            print(f"[ERROR] SharePoint processing failed: {e}")
            print("  - SharePoint documents: 0 (failed)")
    else:
        print("SharePoint processing disabled - skipping...")
    
    print(f"Total documents to process: {len(all_docs)}")
    
    # Create embeddings and vectorstore
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(all_docs, embeddings, persist_directory=CHROMA_DB_PATH)
    
    print("Selective knowledge base created successfully!")
    return vectorstore