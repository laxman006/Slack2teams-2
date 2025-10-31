"""Comprehensive test with 50 questions to diagnose chatbot responses."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from config import OPENAI_API_KEY, CHROMA_DB_PATH, SYSTEM_PROMPT
from app.llm import format_docs
from langchain_core.prompts import ChatPromptTemplate

# Initialize
embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
vectorstore = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embeddings)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.3, max_tokens=800)

# 50 test questions covering various topics
test_queries = [
    # CloudFuze basics
    "What is CloudFuze?",
    "What does CloudFuze do?",
    "Tell me about CloudFuze services",
    
    # Migration questions
    "How do I migrate from Box to SharePoint?",
    "How to migrate from Dropbox to Google Drive?",
    "How to migrate from Slack to Teams?",
    "What migration options does CloudFuze offer?",
    "Can I migrate from OneDrive to SharePoint?",
    "How does delta migration work?",
    "What is one-time migration?",
    "gmail to outlook",
    
    # Features
    "What features does CloudFuze have?",
    "Does CloudFuze support version migration?",
    "Can CloudFuze migrate permissions?",
    "Does CloudFuze migrate shared links?",
    "What about external shares?",
    
    # Certificates
    "Download SOC 2 certificate",
    "What certificates do you have?",
    "Show me security certificates",
    "Do you have SOC 2 Type 2?",
    "What compliance certificates are available?",
    
    # Policy documents
    "What policy documents do you have?",
    "Show me security policies",
    "Do you have an information security policy?",
    "What about data protection policy?",
    "Show me access control policy",
    
    # Migration guides
    "What migration guides are available?",
    "Do you have a Box to SharePoint guide?",
    "Show me Dropbox migration guides",
    "What guides do you have?",
    
    # Technical questions
    "What is the CloudFuze architecture?",
    "How does CloudFuze ensure security?",
    "What cloud platforms does CloudFuze support?",
    "Can CloudFuze handle large migrations?",
    
    # Specific migrations
    "How to migrate from Box to OneDrive?",
    "Gmail to Outlook migration",
    "Google Drive to SharePoint",
    "Dropbox to OneDrive",
    "Egnyte to SharePoint",
    
    # Combinations
    "What source and destination combinations are supported?",
    "Can I migrate from any cloud to any cloud?",
    "What are the migration combinations?",
    
    # Pricing and contact
    "How much does CloudFuze cost?",
    "What is CloudFuze pricing?",
    "How to contact CloudFuze?",
    
    # Should refuse (completely unrelated)
    "What is the capital of France?",
    "How to cook pasta?",
    "What is quantum physics?",
    "Tell me about the weather",
    "What is machine learning?",
    
    # More migration questions
    "migrate from egnyte to onedrive",
    "slack to google chat migration steps",
    "box to google drive migration",
    "sharepoint to sharepoint migration",
    "teams to teams migration",
    "amazon workdocs to sharepoint",
    "dropbox team folders to sharepoint",
    "onedrive personal to onedrive business",
    "google my drive to google shared drive",
    "box for business to onedrive",
    
    # Advanced features
    "does cloudfuze support incremental migration",
    "can cloudfuze migrate file versions",
    "what about metadata migration",
    "does it preserve timestamps",
    "can cloudfuze migrate comments",
    "what about collaborative permissions",
    "does it handle external users",
    "can cloudfuze migrate large files",
    "what is the file size limit",
    "does it support bulk migration",
    
    # Security and compliance
    "is cloudfuze secure",
    "does cloudfuze have iso certification",
    "what security measures does cloudfuze use",
    "is data encrypted during migration",
    "does cloudfuze store my data",
    "what is cloudfuze's data retention policy",
    "does cloudfuze comply with gdpr",
    "is cloudfuze hipaa compliant",
    "what about soc 2 compliance",
    "does cloudfuze have security audits",
    
    # Technical implementation
    "how long does migration take",
    "what is the migration speed",
    "does cloudfuze use apis",
    "what authentication methods are supported",
    "does it support single sign on",
    "can i schedule migrations",
    "does cloudfuze provide migration reports",
    "what happens if migration fails",
    "can i pause and resume migration",
    "does cloudfuze support rollback",
    
    # Specific document requests
    "download iso 27001 certificate",
    "show me vulnerability management policy",
    "download data protection policy",
    "access control policy document",
    "show me gdpr compliance certificate",
    "download backup policy",
    "show me incident response policy",
    "what is the change management policy",
    "download acceptable use policy",
    "show me network security policy",
    
    # More migration guides
    "box to onedrive migration guide",
    "google drive to onedrive guide",
    "slack to teams migration faq",
    "dropbox to sharepoint guide",
    "egnyte to box migration guide",
    
    # More specific scenarios
    "how to migrate shared folders",
    "migrate external collaborators",
    "what happens to folder permissions",
    "can i migrate selective folders",
    "how to handle duplicate files",
    "migrate deleted items",
    "what about file locks during migration",
    "how to migrate team drives",
    "can i migrate nested folders",
    "what is the maximum folder depth",
    
    # More compliance and security
    "show me physical security policy",
    "download human resource policy",
    "what is your password policy",
    "show me remote access policy",
    "download disaster recovery plan",
    "what about business continuity plan",
    "show me third party management policy",
    "download application security policy",
    "what is the audit logging policy",
    "show me encryption policy",
    
    # More technical details
    "what apis does cloudfuze expose",
    "how to integrate cloudfuze with my app",
    "what programming languages are supported",
    "does cloudfuze have a rest api",
    "what is the api rate limit",
    "how to handle api errors",
    "what about api authentication",
    "does cloudfuze support webhooks",
    "how to monitor migration progress via api",
    "what endpoints are available",
    
    # Migration troubleshooting
    "why is my migration slow",
    "how to fix migration errors",
    "what if files are missing after migration",
    "how to verify migration success",
    "what if permissions are wrong",
    "how to handle large file errors",
    "what if external users cant access files",
    "how to fix broken shared links",
    "what about character limit errors",
    "how to handle special characters in filenames",
    
    # Specific cloud platforms
    "migrate from citrix sharefile",
    "box for business features",
    "google workspace migration",
    "microsoft 365 integration",
    "azure ad support"
]

print("\n" + "="*100)
print(f"COMPREHENSIVE TEST: {len(test_queries)} QUESTIONS")
print("="*100)

results = {
    "answered": 0,
    "refused": 0,
    "total": len(test_queries)
}

for i, query in enumerate(test_queries, 1):
    print(f"\n[{i}/{len(test_queries)}] QUERY: {query}")
    print("-" * 100)
    
    try:
        # Retrieve documents
        doc_results = vectorstore.similarity_search_with_score(query, k=10)
        
        if not doc_results:
            print("   [WARNING] No documents retrieved!")
            results["refused"] += 1
            continue
        
        docs = [doc for doc, score in doc_results]
        
        # Show top 3 documents
        print(f"   Top 3 docs: ", end="")
        for j, (doc, score) in enumerate(doc_results[:3], 1):
            file_name = doc.metadata.get('file_name', 'Unknown')
            print(f"{file_name[:40]}... ({score:.3f})", end=" | " if j < 3 else "")
        print()
        
        # Format and generate response
        formatted_docs = format_docs(docs[:5])
        context_text = "\n\n".join([f"Document {j+1}:\n{formatted_doc}" for j, formatted_doc in enumerate(formatted_docs)])
        
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "Context: {context}\n\nQuestion: {question}")
        ])
        
        messages = prompt_template.format_messages(context=context_text, question=query)
        response = llm.invoke(messages)
        
        # Check if response contains "don't know" or "don't have" phrases
        response_lower = response.content.lower()
        is_refusal = any(phrase in response_lower for phrase in [
            "don't know",
            "don't have",
            "haven't learned",
            "not sure about that",
            "i'm not sure",
            "no information"
        ])
        
        if is_refusal:
            print(f"   [REFUSED] Response: {response.content[:150]}...")
            results["refused"] += 1
        else:
            print(f"   [ANSWERED] Response: {response.content[:150]}...")
            results["answered"] += 1
            
    except Exception as e:
        print(f"   [ERROR] {e}")
        results["refused"] += 1

# Summary
print("\n" + "="*100)
print("SUMMARY")
print("="*100)
print(f"Total questions: {results['total']}")
print(f"Answered: {results['answered']} ({results['answered']/results['total']*100:.1f}%)")
print(f"Refused: {results['refused']} ({results['refused']/results['total']*100:.1f}%)")
print()
print(f"Expected behavior:")
expected_answered = results['total'] - 5  # Only 5 unrelated questions should be refused
print(f"  - Should answer: ~{expected_answered}/{results['total']} (CloudFuze-related questions)")
print(f"  - Should refuse: ~5/{results['total']} (unrelated questions like cooking, weather, etc.)")

# Show breakdown by category
if results['answered'] > 0:
    print(f"\nAnswer rate: {results['answered']/results['total']*100:.1f}%")
    if results['answered']/results['total'] >= 0.90:
        print("EXCELLENT - Chatbot is highly confident!")
    elif results['answered']/results['total'] >= 0.80:
        print("GOOD - Chatbot is working well")
    elif results['answered']/results['total'] >= 0.70:
        print("FAIR - Chatbot needs improvement")
    else:
        print("POOR - Chatbot is too cautious")

