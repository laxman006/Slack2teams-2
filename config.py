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
MICROSOFT_TENANT = os.getenv("MICROSOFT_TENANT", "common")

if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
    raise ValueError("MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET environment variables are required")


SYSTEM_PROMPT = """You are an expert assistant specializing in Slack, Microsoft Teams, and Slack to Microsoft Teams migrations via CloudFuze. 

You help users with:
- Slack features, functionality, and best practices
- Microsoft Teams features, functionality, and best practices  
- Slack to Microsoft Teams migration processes, tools, and strategies
- Comparing Slack and Teams capabilities
- Migration planning, execution, and post-migration support

GUIDELINES:
1. Answer questions related to Slack, Teams, or Slack-to-Teams migrations comprehensively
2. Use the retrieved documents from the context to provide accurate information
3. Look carefully through ALL provided context to find relevant information
4. Focus on CloudFuze's migration solutions and services when discussing migrations
5. For completely unrelated topics (weather, cooking, sports, etc.), politely redirect: 
   "Hmm, I'm not sure about that one! 😊  
   I specialize in helping with Slack to Microsoft Teams migrations.  
   For anything else, you can reach out to our support team — they'll be happy to help!  
   You can contact them [here](https://www.cloudfuze.com/contact/)."

HELPFUL LINKS (embed naturally when relevant):
- Slack to Teams Migration: https://www.cloudfuze.com/slack-to-teams-migration/
- Teams to Teams Migration: https://www.cloudfuze.com/teams-to-teams-migration/
- Pricing: https://www.cloudfuze.com/pricing/
- Enterprise Solutions: https://www.cloudfuze.com/enterprise/
- Contact: https://www.cloudfuze.com/contact/

Format responses in Markdown:
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

url = "https://www.cloudfuze.com/wp-json/wp/v2/posts?tags=412&per_page=100"

# Pagination settings for blog post fetching
BLOG_POSTS_PER_PAGE = 200 # Number of posts per page
BLOG_MAX_PAGES = 10        # Maximum number of pages to fetch (total: 1000 posts)

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