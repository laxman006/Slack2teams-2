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
    
    2. IMPORTANT: You MUST ONLY use information from the retrieved documents provided in the context
       - If the context contains relevant information: Provide a detailed answer using that information
       - If the context does not contain relevant information: Say "I don't have specific information about that in my knowledge base"
       - NEVER use general knowledge or information not provided in the context
    
    3. When answering questions:
       - Use information from the retrieved documents provided in the context
       - Look carefully through ALL the provided context to find relevant information
       - Provide comprehensive answers based on the available information
       - Be helpful and conversational while staying within the knowledge base
    
    4. Where relevant, automatically include/embed these specific links:
       - **Slack to Teams Migration**: https://www.cloudfuze.com/slack-to-teams-migration/
       - **Teams to Teams Migration**: https://www.cloudfuze.com/teams-to-teams-migration/
       - **Pricing**: https://www.cloudfuze.com/pricing/
       - **Enterprise Solutions**: https://www.cloudfuze.com/enterprise/
       - **Contact for Custom Solutions**: https://www.cloudfuze.com/contact/
    
    5. Always conclude with a helpful suggestion to contact CloudFuze for further guidance by embedding the link naturally: https://www.cloudfuze.com/contact/
 
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
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "http://localhost:3100")

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

# Teams Transcript Configuration
ENABLE_TEAMS_TRANSCRIPTS = os.getenv("ENABLE_TEAMS_TRANSCRIPTS", "false").lower() == "true"
TEAMS_TRANSCRIPT_DAYS_BACK = int(os.getenv("TEAMS_TRANSCRIPT_DAYS_BACK", "30"))
TEAMS_TRANSCRIPT_USER_EMAILS = os.getenv("TEAMS_TRANSCRIPT_USER_EMAILS", "").split(",") if os.getenv("TEAMS_TRANSCRIPT_USER_EMAILS") else None

# Source-specific settings
WEB_SOURCE_URL = os.getenv("WEB_SOURCE_URL", "https://cloudfuze.com/wp-json/wp/v2/posts?per_page=100")
PDF_SOURCE_DIR = os.getenv("PDF_SOURCE_DIR", "./pdfs")
EXCEL_SOURCE_DIR = os.getenv("EXCEL_SOURCE_DIR", "./excel")
DOC_SOURCE_DIR = os.getenv("DOC_SOURCE_DIR", "./docs")

# SharePoint Configuration
SHAREPOINT_SITE_URL = os.getenv("SHAREPOINT_SITE_URL", "https://cloudfuzecom.sharepoint.com/sites/DOC360")
SHAREPOINT_START_PAGE = os.getenv("SHAREPOINT_START_PAGE", "/SitePages/Multi%20User%20Golden%20Image%20Combinations.aspx")
SHAREPOINT_MAX_DEPTH = int(os.getenv("SHAREPOINT_MAX_DEPTH", "3"))
SHAREPOINT_EXCLUDE_FILES = os.getenv("SHAREPOINT_EXCLUDE_FILES", "true").lower() == "true"