"""
CloudFuze Chatbot Consistency Test Script
Tests 60 unique questions 3 times each (180 total) and reports performance
"""

import requests
import json
import time
from datetime import datetime
from difflib import SequenceMatcher
import re

# Configuration
API_BASE = "http://localhost:8002"
CHAT_ENDPOINT = f"{API_BASE}/chat/stream"

# 60 Unique Test Questions
QUESTIONS = [
    "What is CloudFuze's pricing model and how does it compare to competitors?",
    "How does CloudFuze handle permission mapping when migrating shared folders from Google Drive to OneDrive with external collaborators?",
    "Can CloudFuze migrate Slack private channels to Microsoft Teams private channels?",
    "What security certifications does CloudFuze hold?",
    "How does delta migration work in CloudFuze?",
    "What happens to file version history during a Box to OneDrive migration?",
    "Can CloudFuze migrate Google Docs and convert them to Microsoft Office formats?",
    "How does CloudFuze handle user mapping between source and destination platforms?",
    "What is the maximum file size CloudFuze can migrate?",
    "Does CloudFuze support SSO integration with Azure AD or Okta?",
    "How does CloudFuze handle special characters in file names during migration?",
    "Can CloudFuze perform bidirectional sync between cloud platforms?",
    "What happens to file timestamps during migration?",
    "Is CloudFuze SOC 2 Type II certified?",
    "How does CloudFuze handle nested folder permissions during migration?",
    "Can CloudFuze migrate Box Notes and what format are they converted to?",
    "How does CloudFuze ensure data integrity during migration?",
    "What happens to external sharing permissions when migrating between platforms?",
    "Does CloudFuze encrypt data during transit and at rest?",
    "How does CloudFuze handle API rate limits from different cloud platforms?",
    "Can CloudFuze migrate custom metadata fields from Box to SharePoint?",
    "What happens to Slack threaded conversations during Teams migration?",
    "Does CloudFuze store customer data after migration completion?",
    "How does CloudFuze handle files that are being actively edited during migration?",
    "What is the typical migration speed for CloudFuze?",
    "Can CloudFuze migrate 'anyone with the link' sharing settings?",
    "What authentication methods does CloudFuze support?",
    "Can CloudFuze migrate Slack custom emojis to Teams?",
    "How does CloudFuze handle duplicate file names in the destination?",
    "What happens to file comments and annotations during migration?",
    "Is CloudFuze GDPR compliant for cross-border migrations?",
    "Can CloudFuze migrate Google Shared Drives separately from My Drive?",
    "How does CloudFuze handle corrupted or unreadable files?",
    "Can CloudFuze preserve file ownership during migration?",
    "What happens to files in trash or recycle bin during migration?",
    "Does CloudFuze offer a free trial?",
    "How does CloudFuze handle Windows path length limitations (260 characters)?",
    "Can CloudFuze migrate Dropbox Paper documents?",
    "How does CloudFuze handle group permissions during migration?",
    "What happens to @ mentions and user tags during Slack to Teams migration?",
    "Can CloudFuze migrate SharePoint workflows?",
    "Does CloudFuze support multi-factor authentication when connecting to platforms?",
    "How does CloudFuze handle time zone differences for file timestamps?",
    "Can CloudFuze migrate from Slack Enterprise Grid with multiple workspaces?",
    "What is CloudFuze's data retention policy after migration?",
    "Can CloudFuze perform delta migrations and how are they charged?",
    "Does CloudFuze provide audit logs during migration?",
    "Can CloudFuze migrate Box metadata templates and cascade policies?",
    "What support options does CloudFuze offer?",
    "What happens to orphaned files owned by deleted users?",
    "Can CloudFuze resume a failed or interrupted migration?",
    "How does CloudFuze handle symbolic links and shortcuts during migration?",
    "Does CloudFuze support tenant-to-tenant Microsoft 365 migrations?",
    "Can CloudFuze migrate OneDrive Personal Vault files?",
    "How does CloudFuze handle CSV user mapping and what format is required?",
    "Can CloudFuze filter or exclude certain files from migration?",
    "What is the typical timeline for a 10TB migration with 500 users?",
    "What happens to Slack pinned messages and bookmarks during migration?",
    "Can CloudFuze provide a Business Associate Agreement (BAA) for HIPAA compliance?",
    "Can CloudFuze migrate SharePoint document sets and content types?",
]

# Shuffle order: each question asked 3 times, randomized
SHUFFLED_ORDER = [
    0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 0, 16, 17, 18,
    19, 20, 21, 1, 22, 23, 24, 25, 4, 26, 27, 28, 29, 30, 31, 3, 32, 33, 34,
    35, 36, 37, 8, 38, 39, 40, 4, 41, 5, 42, 43, 44, 10, 45, 17, 1, 46, 47,
    14, 48, 6, 7, 49, 13, 50, 51, 0, 52, 16, 53, 12, 54, 55, 18, 56, 2, 19,
    57, 58, 14, 3, 59, 60, 5, 61, 20, 23, 8, 22, 62, 63, 21, 9, 10, 15, 26,
    28, 64, 29, 7, 30, 65, 16, 24, 31, 32, 18, 25, 17, 19, 33, 44, 34, 35,
    6, 36, 27, 37, 38, 39, 46, 40, 14, 27, 38, 41, 42, 45, 43, 66, 58, 59,
    60, 61, 24, 62, 63, 9, 15, 64, 65, 25, 31, 30, 25, 33, 44, 35, 36, 27,
    37, 39, 46, 40, 41, 42, 43, 66, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58,
    59
]


def get_auth_token():
    """
    Get authentication token - skips prompt in non-interactive mode
    """
    import sys
    
    # Check if running in non-interactive mode
    if not sys.stdin.isatty():
        print("Running in non-interactive mode, skipping authentication...")
        return None
    
    print("\n" + "="*70)
    print("AUTHENTICATION REQUIRED")
    print("="*70)
    print("\nTo get your auth token:")
    print("1. Open browser DevTools (F12)")
    print("2. Go to Application/Storage > Local Storage > http://localhost:8002")
    print("3. Find 'user' key and copy the entire JSON value")
    print("4. Or go to Console and type: localStorage.getItem('user')")
    print("\nPaste the user JSON here (or press Enter to skip auth):")
    
    try:
        user_input = input().strip()
        
        if user_input:
            try:
                user_data = json.loads(user_input)
                return user_data.get('access_token', '')
            except:
                print("WARNING: Could not parse user data. Continuing without auth...")
                return None
        return None
    except (EOFError, KeyboardInterrupt):
        print("\nSkipping authentication...")
        return None


def ask_question(question, auth_token=None):
    """
    Send a question to the chatbot and get the full response
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    payload = {
        "question": question,
        "chat_history": []
    }
    
    try:
        response = requests.post(
            CHAT_ENDPOINT,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        )
        
        if response.status_code != 200:
            return f"ERROR: HTTP {response.status_code}"
        
        full_response = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    try:
                        data = json.loads(line_str[6:])
                        if data.get('type') == 'token':
                            full_response += data.get('token', '')
                        elif data.get('type') == 'done':
                            break
                        elif data.get('type') == 'error':
                            return f"ERROR: {data.get('error', 'Unknown error')}"
                    except json.JSONDecodeError:
                        continue
        
        return full_response.strip()
    
    except requests.exceptions.ConnectionError:
        return "ERROR: Could not connect to server. Is the backend running?"
    except requests.exceptions.Timeout:
        return "ERROR: Request timeout"
    except Exception as e:
        return f"ERROR: {str(e)}"


def calculate_similarity(text1, text2):
    """
    Calculate similarity between two texts (0-100%)
    """
    # Remove extra whitespace
    text1 = re.sub(r'\s+', ' ', text1.strip())
    text2 = re.sub(r'\s+', ' ', text2.strip())
    
    return SequenceMatcher(None, text1, text2).ratio() * 100


def analyze_consistency(responses):
    """
    Analyze consistency of 3 responses
    Returns: (avg_similarity, max_diff, status)
    """
    if len(responses) < 3:
        return 0, 100, "INCOMPLETE"
    
    # Check for errors
    errors = [r for r in responses if r.startswith("ERROR:")]
    if errors:
        return 0, 100, "ERROR"
    
    # Check for "I don't know" variations
    dont_know_phrases = [
        "i don't have",
        "i don't know",
        "i cannot provide",
        "not available in my knowledge",
        "don't have specific information"
    ]
    
    dont_know_count = sum(
        1 for r in responses 
        if any(phrase in r.lower() for phrase in dont_know_phrases)
    )
    
    # Calculate pairwise similarities
    sim_12 = calculate_similarity(responses[0], responses[1])
    sim_13 = calculate_similarity(responses[0], responses[2])
    sim_23 = calculate_similarity(responses[1], responses[2])
    
    avg_similarity = (sim_12 + sim_13 + sim_23) / 3
    max_diff = 100 - min(sim_12, sim_13, sim_23)
    
    # Determine status
    if dont_know_count > 0 and dont_know_count < 3:
        status = "INCONSISTENT_IDK"
    elif avg_similarity >= 90:
        status = "EXCELLENT"
    elif avg_similarity >= 75:
        status = "GOOD"
    elif avg_similarity >= 60:
        status = "FAIR"
    else:
        status = "POOR"
    
    return avg_similarity, max_diff, status


def generate_report(results, total_time):
    """
    Generate a comprehensive test report
    """
    print("\n" + "="*70)
    print("CHATBOT CONSISTENCY TEST REPORT")
    print("="*70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Questions: {len(QUESTIONS)} unique (180 total with repeats)")
    print(f"Total Time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Avg Time per Question: {total_time/180:.2f} seconds")
    print("="*70)
    
    # Overall statistics
    statuses = [r['status'] for r in results.values()]
    similarities = [r['avg_similarity'] for r in results.values()]
    
    excellent = statuses.count('EXCELLENT')
    good = statuses.count('GOOD')
    fair = statuses.count('FAIR')
    poor = statuses.count('POOR')
    inconsistent = statuses.count('INCONSISTENT_IDK')
    errors = statuses.count('ERROR')
    
    avg_similarity_overall = sum(similarities) / len(similarities) if similarities else 0
    
    print("\nOVERALL PERFORMANCE:")
    print(f"  Average Similarity: {avg_similarity_overall:.1f}%")
    print(f"\n  [EXCELLENT] (>=90%): {excellent} questions ({excellent/len(QUESTIONS)*100:.1f}%)")
    print(f"  [GOOD] (75-89%):     {good} questions ({good/len(QUESTIONS)*100:.1f}%)")
    print(f"  [FAIR] (60-74%):     {fair} questions ({fair/len(QUESTIONS)*100:.1f}%)")
    print(f"  [POOR] (<60%):       {poor} questions ({poor/len(QUESTIONS)*100:.1f}%)")
    print(f"  [INCONSISTENT]:      {inconsistent} questions ({inconsistent/len(QUESTIONS)*100:.1f}%)")
    print(f"  [ERRORS]:            {errors} questions ({errors/len(QUESTIONS)*100:.1f}%)")
    
    # Grade
    if avg_similarity_overall >= 90:
        grade = "A+ (Excellent)"
    elif avg_similarity_overall >= 85:
        grade = "A (Very Good)"
    elif avg_similarity_overall >= 75:
        grade = "B (Good)"
    elif avg_similarity_overall >= 65:
        grade = "C (Fair)"
    else:
        grade = "D/F (Needs Improvement)"
    
    print(f"\n  Overall Grade: {grade}")
    print("="*70)
    
    # Problem areas
    print("\nPROBLEM AREAS:")
    problems = [(q_idx, data) for q_idx, data in results.items() 
                if data['status'] in ['POOR', 'INCONSISTENT_IDK', 'ERROR']]
    
    if problems:
        for q_idx, data in problems[:10]:  # Show top 10 problems
            print(f"\n[PROBLEM] Q{q_idx+1}: {QUESTIONS[q_idx][:80]}...")
            print(f"   Status: {data['status']}")
            print(f"   Similarity: {data['avg_similarity']:.1f}%")
            if data['status'] == 'INCONSISTENT_IDK':
                print("   WARNING: Some responses say 'I don't know', others provide answers")
    else:
        print("  [OK] No major problems detected!")
    
    print("\n" + "="*70)
    
    # Save detailed report to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"test_report_{timestamp}.txt"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("CLOUDFULZE CHATBOT DETAILED TEST REPORT\n")
        f.write("="*100 + "\n\n")
        
        for q_idx in range(len(QUESTIONS)):
            data = results[q_idx]
            f.write(f"Q{q_idx+1}: {QUESTIONS[q_idx]}\n")
            f.write(f"Status: {data['status']} | Similarity: {data['avg_similarity']:.1f}%\n")
            f.write("-"*100 + "\n")
            
            for i, response in enumerate(data['responses'], 1):
                f.write(f"\nResponse {i}:\n{response}\n")
            
            f.write("\n" + "="*100 + "\n\n")
    
    print(f"\n[SAVED] Detailed report saved to: {report_file}")
    print("="*70 + "\n")


def main():
    """
    Main test execution
    """
    print("\n" + "="*70)
    print("CLOUDFULZE CHATBOT CONSISTENCY TEST")
    print("="*70)
    print("\nThis will test 60 questions, each 3 times (180 total)")
    print("Estimated time: 15-30 minutes")
    print("="*70)
    
    # Get authentication
    auth_token = get_auth_token()
    
    # Auto-start after brief delay
    print("\nWARNING: Make sure the backend server is running on http://localhost:8002")
    print("Starting test in 2 seconds...")
    time.sleep(2)
    
    # Store results
    responses_by_question = {i: {'responses': [], 'avg_similarity': 0, 'max_diff': 0, 'status': ''} 
                            for i in range(len(QUESTIONS))}
    
    start_time = time.time()
    
    # Run tests
    print("\n" + "="*70)
    print("TESTING IN PROGRESS...")
    print("="*70 + "\n")
    
    for test_num, q_idx in enumerate(SHUFFLED_ORDER, 1):
        question = QUESTIONS[q_idx]
        
        print(f"[{test_num}/180] Q{q_idx+1} (attempt {len(responses_by_question[q_idx]['responses'])+1}/3)")
        print(f"  {question[:70]}...")
        
        response = ask_question(question, auth_token)
        responses_by_question[q_idx]['responses'].append(response)
        
        # Show preview
        preview = response[:100].replace('\n', ' ')
        print(f"  > {preview}...")
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    total_time = time.time() - start_time
    
    # Analyze consistency
    print("\n" + "="*70)
    print("ANALYZING RESULTS...")
    print("="*70 + "\n")
    
    for q_idx in range(len(QUESTIONS)):
        responses = responses_by_question[q_idx]['responses']
        avg_sim, max_diff, status = analyze_consistency(responses)
        responses_by_question[q_idx]['avg_similarity'] = avg_sim
        responses_by_question[q_idx]['max_diff'] = max_diff
        responses_by_question[q_idx]['status'] = status
    
    # Generate report
    generate_report(responses_by_question, total_time)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

