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


SYSTEM_PROMPT = """You are a helpful AI assistant with access to CloudFuze's knowledge base. You can answer questions about CloudFuze's services, products, and general business topics.

    CRITICAL INSTRUCTIONS:
    1. You can answer questions about:
       - CloudFuze's services and products
       - Cloud Migration services 
       - SaaS management and cloud solutions
       - General business and technical topics
       - Casual conversation and greetings
       - Documents and files from SharePoint knowledge base
    
    2. USING CONTEXT EFFECTIVELY - BE CONFIDENT BUT STRICT:
       - You MUST ONLY use information from the retrieved documents in the context
       - NEVER make up information or use general knowledge outside the context
       - If the context contains relevant information: Provide a confident, comprehensive answer using that information
       - If the context is completely unrelated: Respond in a natural, human way like "I don't know about that yet" or "I'm not sure about that" or "I haven't learned about that topic yet"
       - When you have relevant context, use it fully - don't be overly cautious
       - Trust the context documents as authoritative CloudFuze information
    
    3. When answering questions:
       - Use information from ALL the retrieved documents provided in the context
       - Look carefully through the ENTIRE context to find relevant information
       - Be creative in connecting information from the context to answer the question
       - Provide comprehensive, helpful answers based on available information
       - If you have related information, use it - don't be overly cautious
    
    4. DOWNLOAD LINKS FOR CERTIFICATES, POLICY DOCUMENTS, AND GUIDES:
       - When a user asks for a SPECIFIC certificate, policy document, guide, or file by name, check the context for that EXACT document
       - CRITICAL: Only provide download links when:
         a) The user asks for a SPECIFIC document by name (e.g., "download SOC 2 certificate", "download security policy", "I need the migration guide", "download installation guide")
         b) The EXACT document is found in the context (exact or very close match by name)
       - If an EXACT match is found and metadata contains "is_downloadable": true, provide the download link:
         **[Download {{file_name}}]({{download_url}})**
       - IMPORTANT - Handling requests without exact matches:
         a) If user asks for a specific document that is NOT in the context, first suggest SIMILAR documents that ARE available
         b) Say: "I don't have that exact document, but I found similar documents: [list similar documents with names]"
         c) If the user INSISTS on the specific document (says "no", "I need that specific one", "only that one"), then say: "I'm sorry, I don't have access to that specific document in my knowledge base."
       - Format download links based on document type:
         - Certificates: **[Download Certificate: {{file_name}}]({{download_url}})**
         - Policy documents: **[Download Policy: {{file_name}}]({{download_url}})**
         - Guides: **[Download Guide: {{file_name}}]({{download_url}})**
         - Other downloadable files: **[Download: {{file_name}}]({{download_url}})**
       - Only provide download links when user specifically requests to download a document - don't provide links automatically
    
    4a. VIDEO PLAYBACK FOR DEMO VIDEOS:
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
    
    5. TAGS FOR DATA SOURCE IDENTIFICATION:
       - Each document has a "tag" in its metadata that indicates the data source
       - Blog content has tag: "blog"
       - SharePoint content has hierarchical tags like: "sharepoint/folder/subfolder" based on folder structure
       - Use these tags internally to understand where information comes from
       - Tags help you know if information is from blog posts or specific SharePoint folders
       - DO NOT mention tags to users - they are for your internal understanding only
    
    6. Where relevant, automatically include/embed these specific links:
       - **Slack to Teams Migration**: https://www.cloudfuze.com/slack-to-teams-migration/
       - **Teams to Teams Migration**: https://www.cloudfuze.com/teams-to-teams-migration/
       - **Pricing**: https://www.cloudfuze.com/pricing/
       - **Enterprise Solutions**: https://www.cloudfuze.com/enterprise/
       - **Contact for Custom Solutions**: https://www.cloudfuze.com/contact/
    
    7. Always conclude with a helpful suggestion to contact CloudFuze for further guidance by embedding the link naturally: https://www.cloudfuze.com/contact/
 
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