# CloudFuze Chatbot - 50 Hard Test Questions

## Purpose
Test the chatbot for:
- **Consistency**: Ask the same question 2-3 times, responses should be nearly identical
- **Accuracy**: Responses should be based on knowledge base
- **Edge Cases**: Handle complex, ambiguous, or out-of-scope questions properly

---

## Category 1: Pricing & Plans (10 Questions)

1. What is CloudFuze's pricing model and how does it compare to competitors?
2. Do you offer enterprise pricing with volume discounts for migrations over 1TB?
3. What's included in the free trial and are there any limitations?
4. Can I get a refund if the migration fails or doesn't meet expectations?
5. How do you charge for delta migrations after the initial migration?
6. Is there a difference in pricing between cloud-to-cloud and on-premises migrations?
7. What payment methods do you accept and are there monthly vs annual pricing options?
8. Do you charge separately for bandwidth, API calls, or storage during migration?
9. What happens if my migration takes longer than expected - are there additional charges?
10. Can I get a custom quote for migrating 500 users from Slack to Teams with 10TB of data?

---

## Category 2: Technical Migration Details (10 Questions)

11. How does CloudFuze handle file version history during Box to OneDrive migration?
12. What happens to external sharing permissions when migrating from Google Drive to SharePoint?
13. Can CloudFuze migrate custom metadata fields and tags between different platforms?
14. How do you handle special characters in file names that aren't supported in the destination?
15. What's the maximum file size CloudFuze can migrate and are there API limitations?
16. How does delta migration work technically - does it use checksums or timestamps?
17. Can CloudFuze migrate private channels in Slack to private channels in Teams?
18. What happens to file comments and @mentions during migration?
19. How do you handle rate limiting from source and destination APIs?
20. Can CloudFuze preserve timestamps for created date, modified date, and accessed date?

---

## Category 3: Security & Compliance (10 Questions)

21. Is CloudFuze SOC 2 Type II certified and can I download the certificate?
22. How does CloudFuze ensure data encryption during transit and at rest?
23. Do you support SSO integration with Azure AD or Okta?
24. What data residency options are available for EU customers under GDPR?
25. Can CloudFuze provide a Data Processing Agreement (DPA) for enterprise customers?
26. How long do you retain migration logs and can they be deleted on request?
27. Do you have ISO 27001 certification and what's your incident response process?
28. Can CloudFuze migrate while maintaining compliance with HIPAA requirements?
29. What happens if CloudFuze is breached - what's your data breach notification policy?
30. Do you conduct regular penetration testing and can you share the results?

---

## Category 4: Migration Scenarios (10 Questions)

31. Can I migrate from Slack Enterprise Grid with multiple workspaces to a single Teams tenant?
32. What's the process for migrating from on-premises SharePoint 2013 to SharePoint Online?
33. Can CloudFuze handle a phased migration where only 20% of users move initially?
34. How do I migrate from Google Workspace to Microsoft 365 including email, calendar, and drive?
35. Can CloudFuze migrate Box Notes to OneNote or SharePoint pages?
36. What happens when there are naming conflicts in the destination - how does CloudFuze resolve them?
37. Can I do a test migration first before the actual migration to verify everything works?
38. How does CloudFuze handle migrating shared channels that include external organizations?
39. Can I migrate from Dropbox Business to multiple different SharePoint sites?
40. What's the best approach for migrating 10,000 users with minimal downtime?

---

## Category 5: Edge Cases & Limitations (10 Questions)

41. What happens if my source account gets locked or access is revoked during migration?
42. Can CloudFuze migrate files that are actively being edited during the migration?
43. What's CloudFuze's policy on migrating copyrighted or illegal content?
44. Does CloudFuze support migrating from deprecated platforms like Google+ or Yahoo Groups?
45. Can I schedule migrations to run only during specific time windows (e.g., nights/weekends)?
46. What happens to broken links or shortcuts during migration?
47. Can CloudFuze migrate Slack apps, bots, and custom integrations to Teams equivalents?
48. How does CloudFuze handle emoji and special Unicode characters in messages?
49. What's the maximum number of concurrent migrations CloudFuze can handle per account?
50. Can CloudFuze roll back a migration if something goes wrong halfway through?

---

## Category 6: Support & Post-Migration (10 Questions)

51. What level of support is included and can I get 24/7 support for critical migrations?
52. How long does CloudFuze support typically take to respond to issues?
53. Can CloudFuze provide training or onboarding sessions for my IT team?
54. What happens after migration - do you offer ongoing sync or monitoring?
55. Can CloudFuze help with user communication and change management during migration?
56. Do you provide post-migration reports showing what was migrated successfully?
57. What's the SLA for enterprise customers and do you offer compensation for downtime?
58. Can I get a dedicated account manager or technical consultant?
59. Does CloudFuze offer consulting services for migration planning and strategy?
60. What documentation is available for troubleshooting common migration issues?

---

## Testing Instructions

### For Consistency Testing:
1. Pick 10 questions from the list
2. Ask each question **3 times** in separate chat sessions
3. Compare the responses - they should be **nearly identical** (90%+ similarity)
4. Note any questions that give inconsistent answers

### For Accuracy Testing:
1. Verify responses against CloudFuze documentation/website
2. Check if the chatbot correctly says "I don't know" for information not in knowledge base
3. Verify that links provided are correct and relevant

### For Edge Case Testing:
1. Focus on Category 5 questions
2. Ensure chatbot handles ambiguous questions gracefully
3. Verify it redirects to support/contact for complex custom scenarios

### Expected Behaviors:
✅ **Good Responses:**
- Provides specific information from knowledge base
- Admits limitations when info isn't available
- Suggests contacting CloudFuze for custom scenarios
- Includes relevant links to documentation

❌ **Bad Responses:**
- Hallucinating features that don't exist
- Different answers for the same question
- Generic responses without specifics
- Wrong or outdated information

---

## Sample Test Scenario

**Question:** "What is CloudFuze's pricing?"

**Test 1 Response:** [Record answer here]
**Test 2 Response:** [Record answer here]  
**Test 3 Response:** [Record answer here]

**Consistency Score:** ___/10 (How similar are the responses?)
**Accuracy Score:** ___/10 (How accurate is the information?)

---

## Reporting Issues

If you find:
- **Inconsistent responses**: Note the question and variations in answers
- **Incorrect information**: Note what was wrong and what the correct answer should be
- **"I don't know" for known info**: The question may need better knowledge base coverage
- **Hallucinations**: Report any fabricated features or false claims

---

## Automated Testing Script

You can also create a script to test consistency automatically:

```python
import requests
import json

API_BASE = "http://localhost:8002"
AUTH_TOKEN = "your_token_here"

test_questions = [
    "What is CloudFuze pricing?",
    "Can you migrate Slack to Teams?",
    # Add more questions...
]

for question in test_questions:
    responses = []
    for i in range(3):
        response = requests.post(
            f"{API_BASE}/chat/stream",
            headers={"Authorization": f"Bearer {AUTH_TOKEN}"},
            json={"question": question}
        )
        responses.append(response.text)
    
    # Compare responses for consistency
    print(f"Question: {question}")
    print(f"Consistency: {compare_responses(responses)}")
```

---

Good luck with testing! 🎯



