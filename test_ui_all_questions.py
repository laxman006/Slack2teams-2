"""Test all 211 questions from test_50_questions.py in the UI - OPTIMIZED FOR SPEED."""
import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime

# Import all questions from the test file
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

async def wait_for_response_complete(page):
    """Wait for bot response to complete - FAST VERSION."""
    try:
        # Wait for feedback buttons to appear (this means streaming is DONE)
        await page.wait_for_selector('.message.bot:last-child .feedback-buttons .feedback-btn', 
                                     state='visible', 
                                     timeout=120000)
        # Immediately return - no extra waiting!
        return True
    except Exception as e:
        print(f"   [TIMEOUT] {str(e)[:80]}")
        return False

async def get_last_bot_response(page):
    """Extract the last bot response."""
    try:
        bot_messages = await page.query_selector_all('.message.bot')
        if not bot_messages:
            return None
        
        last_message = bot_messages[-1]
        content = await last_message.evaluate('''(element) => {
            const contentDiv = element.querySelector(".message-content");
            return contentDiv ? contentDiv.textContent : element.textContent;
        }''')
        
        return content.strip() if content else None
    except:
        return None

async def send_question(page, question):
    """Send a question."""
    try:
        input_field = await page.query_selector('#user-input')
        if not input_field:
            return False
        
        await input_field.fill(question)
        
        send_btn = await page.query_selector('#send-btn')
        if not send_btn:
            return False
        
        await send_btn.click()
        return True
    except:
        return False

async def clear_chat_and_wait(page):
    """Clear chat and wait 11 seconds."""
    try:
        print("\n[SETUP] Clearing chat...")
        new_chat_btn = await page.query_selector('#newChatBtn')
        if new_chat_btn:
            await new_chat_btn.click()
            print("[SETUP] Waiting 11 seconds for DB to clear...")
            for i in range(11, 0, -1):
                print(f"        {i}...", end='\r')
                await asyncio.sleep(1)
            print("\n[SETUP] Ready to test!\n")
            return True
        else:
            print("[WARNING] New Chat button not found")
            return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

async def test_all_questions():
    """Test all questions - OPTIMIZED FOR SPEED."""
    print("="*100)
    print(f"UI TEST: {len(test_queries)} QUESTIONS - SPEED OPTIMIZED")
    print("="*100)
    print("\nMake sure you're logged in at http://localhost:8002/index.html")
    print("Starting in 5 seconds...")
    await asyncio.sleep(5)
    
    results = {
        "answered": 0,
        "refused": 0,
        "errors": 0,
        "total": len(test_queries),
        "details": []
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("\n[SETUP] Opening browser...")
        await page.goto('http://localhost:8002/index.html', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # Check login
        if 'login' in page.url:
            print("\n[ERROR] Not logged in! Waiting 30 seconds...")
            for i in range(30, 0, -1):
                print(f"        {i}...", end='\r')
                await asyncio.sleep(1)
            print()
        
        # Wait for chat interface
        print("[SETUP] Waiting for chat interface...")
        try:
            await page.wait_for_selector('#user-input', state='visible', timeout=30000)
            print("[SETUP] Chat ready!")
        except:
            print("[ERROR] Chat interface not found!")
            await browser.close()
            return
        
        # Clear chat
        await clear_chat_and_wait(page)
        
        # Test each question
        for i, query in enumerate(test_queries, 1):
            print(f"\n[{i}/{len(test_queries)}] {query}")
            print("-" * 100)
            
            try:
                if page.is_closed():
                    print("   [ERROR] Browser closed!")
                    results["errors"] += len(test_queries) - i + 1
                    break
                
                # Send question
                if not await send_question(page, query):
                    print("   [ERROR] Failed to send")
                    results["errors"] += 1
                    continue
                
                # Wait for response to complete
                if not await wait_for_response_complete(page):
                    print("   [ERROR] Response timeout")
                    results["errors"] += 1
                    continue
                
                # Get response
                response = await get_last_bot_response(page)
                
                if not response:
                    print("   [ERROR] No response")
                    results["errors"] += 1
                    continue
                
                # Check if refusal
                response_lower = response.lower()
                is_refusal = any(phrase in response_lower for phrase in [
                    "don't know", "don't have", "haven't learned",
                    "not sure about that", "i'm not sure", "no information"
                ])
                
                if is_refusal:
                    print(f"   [REFUSED] {response[:100]}...")
                    results["refused"] += 1
                    results["details"].append({
                        "question": query,
                        "status": "refused",
                        "response": response[:200]
                    })
                else:
                    print(f"   [ANSWERED] {response[:100]}...")
                    results["answered"] += 1
                    results["details"].append({
                        "question": query,
                        "status": "answered",
                        "response": response[:200]
                    })
                
                # NO DELAY - Send next question immediately!
                
            except Exception as e:
                print(f"   [ERROR] {str(e)[:80]}")
                results["errors"] += 1
        
        await browser.close()
    
    # Summary
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100)
    print(f"Total: {results['total']}")
    print(f"Answered: {results['answered']} ({results['answered']/results['total']*100:.1f}%)")
    print(f"Refused: {results['refused']} ({results['refused']/results['total']*100:.1f}%)")
    print(f"Errors: {results['errors']} ({results['errors']/results['total']*100:.1f}%)")
    print(f"\nExpected: ~{results['total']-5} answered, ~5 refused")
    
    if results['answered'] > 0:
        answer_rate = results['answered']/results['total']
        print(f"\nAnswer rate: {answer_rate*100:.1f}%")
        if answer_rate >= 0.90:
            print("EXCELLENT - Chatbot is highly confident!")
        elif answer_rate >= 0.80:
            print("GOOD - Chatbot is working well")
        elif answer_rate >= 0.70:
            print("FAIR - Chatbot needs improvement")
        else:
            print("POOR - Chatbot is too cautious")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"ui_test_results_{timestamp}.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to: {results_file}")

if __name__ == "__main__":
    asyncio.run(test_all_questions())

