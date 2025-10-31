"""
Enrich SharePoint documents with better searchable content
by adding page titles and context to the text content.
"""
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
from config import MONGODB_URL, MONGODB_DATABASE, MONGODB_VECTORSTORE_COLLECTION
from dotenv import load_dotenv
import os

load_dotenv()

def enrich_sharepoint_documents():
    """Add page titles and context to SharePoint documents to improve retrieval."""
    
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DATABASE]
    collection = db[MONGODB_VECTORSTORE_COLLECTION]
    
    print("\n" + "="*80)
    print("ENRICHING SHAREPOINT DOCUMENTS WITH METADATA")
    print("="*80 + "\n")
    
    # Initialize embeddings for re-embedding
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Find all SharePoint documents
    sharepoint_docs = list(collection.find({
        "metadata.source": "cloudfuze_doc360"
    }))
    
    print(f"Found {len(sharepoint_docs)} SharePoint documents to enrich\n")
    
    updated_count = 0
    
    for doc in sharepoint_docs:
        doc_id = doc['_id']
        current_text = doc.get('text', '')
        metadata = doc.get('metadata', {})
        page_title = metadata.get('page_title', '')
        page_url = metadata.get('page_url', '')
        
        # Check if already enriched
        if current_text.startswith("# "):
            print(f"  [SKIP] Already enriched: {page_title[:50]}...")
            continue
        
        # Create enriched content
        # Add page title and context at the beginning
        enriched_content_parts = []
        
        # Add title as heading
        if page_title:
            # Clean up the title (remove "DOC 360 - " prefix if present)
            clean_title = page_title.replace("DOC 360 - ", "").strip()
            enriched_content_parts.append(f"# {clean_title}")
            enriched_content_parts.append("")  # blank line
        
        # Add context about the document type
        doc_type = "CloudFuze Migration Documentation"
        enriched_content_parts.append(f"**Document Type:** {doc_type}")
        enriched_content_parts.append("")
        
        # Add the original content
        enriched_content_parts.append(current_text)
        
        # Combine everything
        enriched_text = "\n".join(enriched_content_parts)
        
        # Re-generate embedding
        try:
            new_embedding = embeddings.embed_query(enriched_text)
            
            # Update the document
            collection.update_one(
                {'_id': doc_id},
                {
                    '$set': {
                        'text': enriched_text,
                        'embedding': new_embedding
                    }
                }
            )
            
            updated_count += 1
            print(f"  [✓] Enriched: {page_title[:60]}... ({len(current_text)} → {len(enriched_text)} chars)")
            
        except Exception as e:
            print(f"  [✗] Failed to enrich {page_title}: {e}")
    
    print(f"\n{'='*80}")
    print(f"ENRICHMENT COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Updated {updated_count} documents")
    print(f"✅ Skipped {len(sharepoint_docs) - updated_count} already enriched documents")
    print(f"\n🚀 SharePoint documents now have better context for retrieval!")

if __name__ == "__main__":
    enrich_sharepoint_documents()


