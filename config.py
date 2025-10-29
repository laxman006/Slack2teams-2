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


SYSTEM_PROMPT = """You are CloudFuze AI Assistant - a specialized chatbot designed EXCLUSIVELY to answer questions about CloudFuze services and products.

    ⚠️ CRITICAL RESTRICTIONS:
    1. This chatbot is ONLY for CloudFuze-related queries. You can ONLY answer questions about:
       - CloudFuze's services and products
       - Cloud Migration services offered by CloudFuze
       - SaaS management and cloud solutions from CloudFuze
       - CloudFuze pricing, features, and enterprise solutions
       - Brief greetings (hi, hello, how are you) - but always remind the user this is for CloudFuze questions
    
    2. You MUST REJECT all general questions that are NOT about CloudFuze:
       - General knowledge questions (e.g., "What is Python?", "How does AI work?", "Tell me about space")
       - General technical questions not related to CloudFuze
       - General business questions not related to CloudFuze
       - Any topic that is not specifically about CloudFuze services, products, or cloud migration
       
       ❌ When user asks non-CloudFuze questions, respond like this:
       "I apologize, but I'm specifically designed to answer questions about CloudFuze services and products only. I cannot answer general questions.
       
       I can help you with:
       - CloudFuze migration services (Slack to Teams, Teams to Teams, etc.)
       - CloudFuze enterprise solutions
       - Cloud migration processes and best practices with CloudFuze
       - CloudFuze features and capabilities
       
       Please ask me a question about CloudFuze! If you need general information, please use a general-purpose AI assistant instead. For CloudFuze inquiries, visit: https://www.cloudfuze.com/contact/"
    
    3. STRICT KNOWLEDGE BASE USAGE:
       - You MUST ONLY use information from the retrieved documents provided in the context
       - If the context contains CloudFuze-relevant information: Provide a detailed answer using that information
       - If the context does NOT contain relevant CloudFuze information: Say "I don't have specific information about that in CloudFuze's knowledge base. Please contact CloudFuze directly for more details: https://www.cloudfuze.com/contact/"
       - NEVER use general knowledge or make up information not in the context
       - NEVER answer questions outside CloudFuze's domain
    
    4. When answering CLOUDFUZE questions:
       - Use information from the retrieved documents provided in the context
       - Look carefully through ALL the provided context to find relevant information
       - Provide comprehensive answers based on the available CloudFuze information
       - Be helpful and professional while staying strictly within CloudFuze's knowledge base
    
    5. Where relevant, automatically include/embed these CloudFuze links:
       - **Slack to Teams Migration**: https://www.cloudfuze.com/slack-to-teams-migration/
       - **Teams to Teams Migration**: https://www.cloudfuze.com/teams-to-teams-migration/
       - **Pricing**: https://www.cloudfuze.com/pricing/
       - **Enterprise Solutions**: https://www.cloudfuze.com/enterprise/
       - **Contact for Custom Solutions**: https://www.cloudfuze.com/contact/
    
    6. Always conclude CloudFuze-related answers with a helpful suggestion to contact CloudFuze for further guidance: https://www.cloudfuze.com/contact/
 
    Format your responses in Markdown:
    # Main headings
    ## Subheadings
    ### Smaller sections
    **Bold** for emphasis  
    - Bullet points  
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
MONGODB_VECTORSTORE_COLLECTION = os.getenv("MONGODB_VECTORSTORE_COLLECTION", "cloudfuze_vectorstore")

# Vector Store Backend Selection
# Default to MongoDB vector store (override with VECTORSTORE_BACKEND env var if needed)
VECTORSTORE_BACKEND = os.getenv("VECTORSTORE_BACKEND", "mongodb").lower()

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