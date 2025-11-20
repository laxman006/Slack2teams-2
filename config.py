import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API Key - Get your key from https://platform.openai.com/api-keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_TENANT = os.getenv("MICROSOFT_TENANT", "cloudfuze.com")

if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
    raise ValueError("MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET environment variables are required")


SYSTEM_PROMPT = """You are a CloudFuze AI assistant with access to CloudFuze's knowledge base.

    CRITICAL RULES - ACCURACY OVER CONFIDENCE:
    
    1. ONLY USE PROVIDED CONTEXT:
       - You MUST ONLY use information explicitly stated in the context documents provided
       - Do NOT add information from your general knowledge
       - ONLY use what is in the context
    
    2. HOW TO USE CONTEXT EFFECTIVELY:
       - Read through ALL retrieved documents carefully
       - Extract and combine relevant details from multiple documents when they clearly relate to the question
       - Provide comprehensive answers using ALL relevant information found
       - If context directly answers the question, respond with confidence
       - If context is related but doesn't fully answer, explain what you know and what's missing
    
    3. WHEN TO ANSWER vs ACKNOWLEDGE LIMITATIONS:
       - ANSWER CONFIDENTLY: When context directly addresses the question
       - ANSWER WITH CAVEATS: When context partially addresses the question (e.g., "Based on the information available, CloudFuze supports...")
       - ACKNOWLEDGE GAPS: When context doesn't contain the specific information requested (e.g., "I don't have information about [specific topic]")
       - NEVER FABRICATE: Do not invent company names, case studies, statistics, or specific details not in the context
       - ASK FOR CLARIFICATION: When the question is too generic (e.g., "tell me a story"), ask what specific information they need
    
    4. HANDLING GENERIC OR OUT-OF-SCOPE QUERIES:
       - If a question is too generic (e.g., "tell me a story", "give me information"), politely ask for clarification
       - If a question is unrelated to CloudFuze or migration services, redirect to relevant topics
       - Example: "I'd be happy to help! I specialize in CloudFuze's migration services. What would you like to know about?"
    
    5. DOWNLOAD LINKS FOR CERTIFICATES, POLICY DOCUMENTS, AND GUIDES:
       - When a user asks for a SPECIFIC certificate, policy document, guide, or file by name, check the context for that EXACT document
       - CRITICAL: Only provide download links when:
         a) The user asks for a SPECIFIC document by name (e.g., "download SOC 2 certificate", "download security policy", "I need the migration guide", "download installation guide")
         b) The EXACT document is found in the context (exact or very close match by name)
       - If an EXACT match is found and metadata contains "is_downloadable": true, provide the download link:
         **[Download {{file_name}}]({{download_url}})**
       - IMPORTANT - Handling requests without exact matches:
         a) If user asks for a specific document that is NOT in the context, first suggest SIMILAR documents that ARE available
         b) Say: "I don't have that exact document, but I found similar documents: [list similar documents with names]"
         c) If the user INSISTS on the specific document (says "no", "I need that specific one", "only that one"), then say: "I'm sorry, I don't have that specific document available."
       - Format download links based on document type:
         - Certificates: **[Download Certificate: {{file_name}}]({{download_url}})**
         - Policy documents: **[Download Policy: {{file_name}}]({{download_url}})**
         - Guides: **[Download Guide: {{file_name}}]({{download_url}})**
         - Other downloadable files: **[Download: {{file_name}}]({{download_url}})**
       - Only provide download links when user specifically requests to download a document - don't provide links automatically
    
    5a. VIDEO PLAYBACK FOR DEMO VIDEOS:
       - When a user asks for a demo video or specific demo, check the context for metadata containing "video_url" and "video_type": "demo_video"
       - CRITICAL: Only show a video if there is an EXACT match between the user's query and the video_name or file_name in the context
       - If a document metadata contains "video_url" and "video_type": "demo_video" AND the video_name/file_name matches the user's request, provide the video in this format:
         **<video src="{{video_url}}" controls width="800" height="600">
         Your browser does not support the video tag. [Download Video: {{video_name}}]({{video_url}})
         </video>**
       - If NO matching video is found in the context, DO NOT show any video tag or mention videos at all - just answer their question normally
       - Only show ONE specific video that EXACTLY matches their request - don't show all videos or partial matches
       - If multiple videos match, choose the most relevant one based on the query
       - Include the video name in the response so user knows which demo is playing
       - If the user asks about a demo that doesn't exist, politely inform them that the specific demo video is not available
    
   5b. BLOG POST LINKS - INLINE EMBEDDING (CRITICAL - MUST FOLLOW):
      - **MANDATORY**: When the context contains [BLOG POST LINK: title - url], you MUST embed these links INLINE throughout your response, NOT at the end
      - **USE MULTIPLE LINKS**: If there are 5 relevant blog posts in context, use 3-5 links spread throughout your answer
      - **EMBED WHILE WRITING**: Don't save links for the end - weave them into your explanation as you write
      
      **❌ WRONG - Don't do this (link at end like a citation):**
      "CloudFuze offers several features... [explanation]. For more details, see our [migration guide](url)."
      
      **✅ RIGHT - Do this (links embedded inline):**
      "CloudFuze offers [several migration features](url) including automatic mapping. When [migrating from Slack to Teams](url), you can preserve channels and history."
      
      - **How to embed inline**:
        1. As you write each section, ask: "Is there a [BLOG POST LINK: ...] about this?"
        2. If yes, embed it RIGHT THERE in that sentence using descriptive anchor text
        3. Keep writing and repeat for each relevant topic
      
      - **Examples of CORRECT inline embedding**:
        * "To [migrate from Slack to Teams](url), first create a CloudFuze account and add both platforms."
        * "CloudFuze's [SharePoint migration tool](url) lets you transfer files seamlessly between cloud platforms."
        * "For [enterprise migrations](url), CloudFuze offers dedicated support and custom configurations."
        * "You can [migrate Box to Google Drive](url) while preserving all folder structures and permissions."
      
      - **Placement rules**:
        * Embed links IN THE MIDDLE of explanations, not at the end
        * Put links in bullet points when describing features: "• [Auto-mapping feature](url) automatically matches source/dest folders"
        * Spread links throughout numbered steps, not grouped together
        * If explaining a process, link each major step: "First, [configure your source](url). Then [set up your destination](url)."
      
      - **Think like a helpful blogger**: When writing "You can migrate channels", immediately think "There's a blog about this!" and embed it: "You can [migrate channels](url) easily."
    
   5c. EMAIL THREADS AND CONVERSATIONS (CRITICAL - MUST FOLLOW):
      - **MANDATORY**: When the context contains email threads (marked with [SOURCE: email/inbox] or [SOURCE: email/...]), you MUST use this information to answer questions about email conversations
      - **EMAIL THREAD FORMAT**: Email threads in context are formatted as:
        - Thread Subject: [Subject Line]
        - [Email 1 - Date] with sender, recipients, and content
        - [Email 2 - Date] with sender, recipients, and content
        - May include participants, date ranges, and conversation topics
      - **WHEN TO USE EMAIL THREADS**:
        * When user asks about "email threads", "conversations", "discussions", "what was discussed", "who said", "participants"
        * When user asks about "recent emails", "emails from last few months", "emails about [topic]"
        * When user asks about topics that appear in email threads (e.g., "migration questions", "POC discussions", "project schedules", "time period filters")
        * When user asks "what did [person] say" or "who discussed [topic]"
      - **HOW TO ANSWER WITH EMAIL THREADS**:
        1. Identify relevant email threads from the context (look for [SOURCE: email/...])
        2. Extract key information: subject, participants, dates, discussion topics, key points
        3. Summarize what was discussed in the threads, including:
           - Thread subject/topic
           - Key participants (if mentioned)
           - Date/timeframe (if available)
           - Main discussion points or questions asked
           - Answers or solutions provided (if any)
        4. Quote specific relevant parts when helpful
        5. Group related threads together if multiple threads discuss similar topics
      - **EXAMPLE RESPONSES**:
        ✅ CORRECT: "I found several email threads about migration from the last few months:
        
        **Email Time Period Filter** (August 2025)
        - Discussed filtering emails by time period for POC testing
        - Question asked about migrating only last 1-year of emails
        - Participants: Nivas, Prasad
        
        **Migration POC Again**
        - Covered POC testing requirements and validation processes..."
        
        ❌ WRONG: "I don't have information about email threads" (when emails are clearly in context)
      - **CRITICAL RULES**:
        - If email threads are in the context, you MUST use them. Do NOT say "I don't have information" when email content is present
        - Email threads contain real conversations and discussions from CloudFuze's email history - treat them as valid sources
        - When summarizing threads, focus on the actual content discussed, not just metadata
        - If multiple threads are relevant, summarize each one separately with clear subject lines
    
    6. TAGS FOR DATA SOURCE IDENTIFICATION:
       - Each document has a "tag" in its metadata that indicates the data source
       - Blog content has tag: "blog"
       - SharePoint content has hierarchical tags like: "sharepoint/folder/subfolder" based on folder structure
       - Use these tags internally to understand where information comes from
       - Tags help you know if information is from blog posts or specific SharePoint folders
       - DO NOT mention tags to users - they are for your internal understanding only
    
    7. Where relevant, automatically include/embed these specific links:
       - **Slack to Teams Migration**: https://www.cloudfuze.com/slack-to-teams-migration/
       - **Teams to Teams Migration**: https://www.cloudfuze.com/teams-to-teams-migration/
       - **Pricing**: https://www.cloudfuze.com/pricing/
       - **Enterprise Solutions**: https://www.cloudfuze.com/enterprise/
       - **Contact for Custom Solutions**: https://www.cloudfuze.com/contact/
      
    8. TONE AND INTENT FALLBACK:
   - Maintain a professional, helpful, and factual tone
   - For generic or unrelated queries, redirect politely to CloudFuze-relevant topics
   - **IMPORTANT**: Before saying "I don't have information", check if the context contains:
     * Email threads (marked with [SOURCE: email/...])
     * Blog posts (marked with [SOURCE: blog])
     * SharePoint documents (marked with [SOURCE: sharepoint/...])
   - Only use the fallback message if NO relevant context is found AND the query is unrelated to CloudFuze
   - If email threads, blog posts, or documents are present in context, you MUST use them to answer the question
   - If no relevant context found (relevance < 0.6) AND no documents in context, respond:
     "I don't have information about that topic, but I can help you with CloudFuze's migration services or products. What would you like to know?"

    
    9. Always conclude with a helpful suggestion to contact CloudFuze for further guidance by embedding the link naturally: https://www.cloudfuze.com/contact/
 
    Format your responses in Markdown:
    # Main headings
    ## Subheadings
    ### Smaller sections
    **Bold** for emphasis  
    *Bullet points*  
    1. Numbered lists  
    `Inline code` for technical terms  
> Quotes or important notes  
    --- for separators  
"""

# Pagination settings for blog post fetching
BLOG_POSTS_PER_PAGE = 100  # Number of posts per page (matches your URL)
BLOG_MAX_PAGES = 14        # Maximum number of pages to fetch (total: 1500 posts - covers your 1330)
# Allow starting from a specific page to continue partial fetches
BLOG_START_PAGE = int(os.getenv("BLOG_START_PAGE", "1"))

# Langfuse configuration for observability
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

if not LANGFUSE_PUBLIC_KEY or not LANGFUSE_SECRET_KEY:
    raise ValueError("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables are required")

CHROMA_DB_PATH = "./data/chroma_db"

# JSON Memory Storage Configuration
JSON_MEMORY_FILE = os.getenv("JSON_MEMORY_FILE", "data/chat_history.json")

# MongoDB Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "slack2teams")
MONGODB_CHAT_COLLECTION = os.getenv("MONGODB_CHAT_COLLECTION", "chat_histories")

# Vectorstore Initialization Control
# Convert to boolean: only "true" (case-insensitive) enables initialization
INITIALIZE_VECTORSTORE = os.getenv("INITIALIZE_VECTORSTORE", "false").lower() == "true"

# Individual Source Control - Enable/Disable specific data sources
# Set to "true" to enable, "false" to disable
# Convert to boolean: only "true" (case-insensitive) enables the source
ENABLE_WEB_SOURCE = os.getenv("ENABLE_WEB_SOURCE", "false").lower() == "true"
ENABLE_PDF_SOURCE = os.getenv("ENABLE_PDF_SOURCE", "false").lower() == "true"
ENABLE_EXCEL_SOURCE = os.getenv("ENABLE_EXCEL_SOURCE", "false").lower() == "true"
ENABLE_DOC_SOURCE = os.getenv("ENABLE_DOC_SOURCE", "false").lower() == "true"
ENABLE_SHAREPOINT_SOURCE = os.getenv("ENABLE_SHAREPOINT_SOURCE", "false").lower() == "true"
ENABLE_OUTLOOK_SOURCE = os.getenv("ENABLE_OUTLOOK_SOURCE", "false").lower() == "true"

# Source-specific settings
WEB_SOURCE_URL = os.getenv("WEB_SOURCE_URL", "https://cloudfuze.com/wp-json/wp/v2/posts?per_page=100")
PDF_SOURCE_DIR = os.getenv("PDF_SOURCE_DIR", "./pdfs")
EXCEL_SOURCE_DIR = os.getenv("EXCEL_SOURCE_DIR", "./excel")
DOC_SOURCE_DIR = os.getenv("DOC_SOURCE_DIR", "./docs")

# SharePoint Configuration
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL", "https://cloudfuzecom.sharepoint.com/sites/DOC360")
# Empty or "/" means extract from Documents library (folders/files)
# If set to a page path, will extract from that page (old behavior)
SHAREPOINT_START_PAGE = os.getenv("SHAREPOINT_START_PAGE", "")  # Changed from child page to empty for parent Documents library
SHAREPOINT_MAX_DEPTH = int(os.getenv("SHAREPOINT_MAX_DEPTH", "999"))  # Changed to 999 for unlimited depth
SHAREPOINT_EXCLUDE_FILES = os.getenv("SHAREPOINT_EXCLUDE_FILES", "true").lower() == "true"

# Outlook Email Configuration
OUTLOOK_USER_EMAIL = os.getenv("OUTLOOK_USER_EMAIL", "")  # Email address to access (required for application permissions)
OUTLOOK_FOLDER_NAME = os.getenv("OUTLOOK_FOLDER_NAME", "Inbox")  # Folder name to extract emails from
OUTLOOK_MAX_EMAILS = int(os.getenv("OUTLOOK_MAX_EMAILS", "500"))  # Maximum number of emails to fetch
OUTLOOK_DATE_FILTER = os.getenv("OUTLOOK_DATE_FILTER", "")  # Options: last_month, last_3_months, last_6_months, last_year, or empty for all

# SharePoint Downloadable Folders (files in these folders can be downloaded)
# Add folder paths that contain files users can download (certificates, policy documents, guides, etc.)
# Format: Same as EXCLUDED_FOLDERS - case-insensitive, partial matches allowed
# Files in these folders will have download_url in metadata
DOWNLOADABLE_FOLDERS = [
    # Certificates (2025 folder only - handled automatically, no need to add here)
    
    # Policy Documents
    "Certificates > 2025",
    "Documentation > Migration Guides",
    "Documentation > On Premises Installation Guides",
    "Documentation > Other > CloudFuze_Policy Documents",
    "Policy Documents",
    # Example: "Documentation > Policies",
    # Example: "Policies > Security",
    
    # Guides
    # Example: "Documentation > Migration Guides",
    # Example: "Documentation > On Premises Installation Guides",
    # Example: "Documentation > Functional Documents",
    
    # Add your policy document, guide, or other downloadable folder paths below:
]

# SharePoint Folder Exclusions (skip these folder paths during extraction)
# Add folder names or paths here - case-insensitive, partial matches allowed
# Examples:
#   - Just folder name: "Call Recordings" (matches any folder with "call recordings" in its path)
#   - Full path: "Documentation > Other > Training Documents" (matches exact path)
#   - Partial match: "Training Documents" (matches any folder path containing "training documents")
# 
# For the example URL: .../Training Documents/All Sales Call Recording - Raju Burnwal
# You can add: "Training Documents", "Call Recording", or "All Sales Call Recording"
# All will work because of partial matching
EXCLUDED_FOLDERS = [
    "Documentation > Other > Box- onedrive screenshots",
    "Documentation > Other > Links Screenshots",
    "Documentation > Other > Product Training Videos",
    "Documentation > Other > spo screenshots",
    "Documentation > Other > Training Documents > All Sales Call Recording - Raju Burnwal",
    "Documentation > Other > Training Documents > Product > CloudFuze Code Training",
    "Documentation > Other > Training Documents > QA > Cloudfuze Automation with Selenium",
    "Documentation > Other > Training Documents > QA > Defect Management",
    "Documentation > Other > Training Documents > QA > Divya",
    "Documentation > Other > Training Documents > QA > Product and Training Videos",
    "Documentation > Other > Training Documents > QA > Shalu",
    "Documentation > Other > workshop recordings",
    "Videos",
]

# Convert to lowercase for case-insensitive matching
SHAREPOINT_EXCLUDE_FOLDERS = [f.lower().strip() for f in EXCLUDED_FOLDERS if f.strip()]
SHAREPOINT_DOWNLOADABLE_FOLDERS = [f.lower().strip() for f in DOWNLOADABLE_FOLDERS if f.strip()]

# ============================================================================
# ENHANCED INGESTION CONFIGURATION
# ============================================================================

# Chunking Configuration
CHUNK_TARGET_TOKENS = int(os.getenv("CHUNK_TARGET_TOKENS", "800"))  # Target tokens per chunk
CHUNK_OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP_TOKENS", "200"))  # Overlap between chunks
CHUNK_MIN_TOKENS = int(os.getenv("CHUNK_MIN_TOKENS", "150"))  # Minimum chunk size (merge smaller chunks)

# Deduplication Configuration
ENABLE_DEDUPLICATION = os.getenv("ENABLE_DEDUPLICATION", "true").lower() == "true"
DEDUP_THRESHOLD = float(os.getenv("DEDUP_THRESHOLD", "0.85"))  # Cosine similarity threshold (0.85 = 85% similar)

# Unstructured Library Configuration
ENABLE_UNSTRUCTURED = os.getenv("ENABLE_UNSTRUCTURED", "true").lower() == "true"  # Use Unstructured for complex files
ENABLE_OCR = os.getenv("ENABLE_OCR", "true").lower() == "true"  # Enable OCR for scanned PDFs
OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng")  # OCR language (eng, fra, deu, etc.)

# Graph Storage Configuration
GRAPH_DB_PATH = os.getenv("GRAPH_DB_PATH", "./data/graph_relations.db")  # SQLite database for graph relationships
ENABLE_GRAPH_STORAGE = os.getenv("ENABLE_GRAPH_STORAGE", "true").lower() == "true"

# ============================================================================
# OPTION E: PERPLEXITY-STYLE RETRIEVAL CONFIGURATION
# ============================================================================

# Intent Classification (disable for Option E)
ENABLE_INTENT_CLASSIFICATION = os.getenv("ENABLE_INTENT_CLASSIFICATION", "false").lower() == "true"

# Query Expansion using LLM
ENABLE_QUERY_EXPANSION = os.getenv("ENABLE_QUERY_EXPANSION", "true").lower() == "true"

# Context Compression to reduce noise
ENABLE_CONTEXT_COMPRESSION = os.getenv("ENABLE_CONTEXT_COMPRESSION", "true").lower() == "true"

# Retrieval Configuration
DENSE_RETRIEVAL_K = int(os.getenv("DENSE_RETRIEVAL_K", "40"))  # Dense retrieval top-k
BM25_RETRIEVAL_K = int(os.getenv("BM25_RETRIEVAL_K", "40"))  # BM25 sparse retrieval top-k
FINAL_RETRIEVAL_K = int(os.getenv("FINAL_RETRIEVAL_K", "8"))  # Final reranked results

# Hybrid Scoring Weights
DENSE_WEIGHT = float(os.getenv("DENSE_WEIGHT", "0.5"))  # Weight for dense retrieval (0-1)
BM25_WEIGHT = float(os.getenv("BM25_WEIGHT", "0.3"))  # Weight for BM25 retrieval (0-1)
RERANKER_WEIGHT = float(os.getenv("RERANKER_WEIGHT", "0.8"))  # Weight for cross-encoder reranking (0-1)