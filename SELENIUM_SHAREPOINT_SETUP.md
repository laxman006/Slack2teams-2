# Selenium-Based SharePoint Extraction Setup

## 📋 Overview

This uses **Selenium browser automation** to extract SharePoint content. It opens a browser, you authenticate once, and it automatically extracts all page content.

## ✅ Why Selenium is Best for Automation

1. **Full Content Access**: Gets actual HTML content from pages
2. **Works with Your Auth**: Uses your Microsoft authentication
3. **Fully Automated**: After setup, runs automatically
4. **Reliable**: Works exactly like a human browsing
5. **No API Limitations**: Bypasses Microsoft Graph API limitations

## 🚀 Quick Setup (5 minutes)

### **Step 1: Install Dependencies**

**Windows:**
```powershell
.\setup_selenium.bat
```

**Linux/Mac:**
```bash
chmod +x setup_selenium.sh
./setup_selenium.sh
```

**Manual:**
```bash
pip install selenium webdriver-manager
```

### **Step 2: Test the Extraction**

```bash
python test_selenium_sharepoint.py
```

This will:
1. Open a Chrome browser window
2. Show SharePoint login page
3. You sign in with your Microsoft account
4. Script extracts all content automatically
5. Browser closes when done

### **Step 3: Enable in Production**

In your `.env`:
```bash
ENABLE_SHAREPOINT_SOURCE=true
INITIALIZE_VECTORSTORE=true
```

Then run:
```bash
python server.py
```

## 📦 What Gets Installed

- **selenium**: Browser automation library
- **webdriver-manager**: Auto-downloads ChromeDriver
- **ChromeDriver**: Browser driver for automation

## ⚙️ How It Works

1. **Opens Chrome browser** (headless mode - runs in background)
2. **Navigates to SharePoint** site
3. **Uses your authentication** (you login once)
4. **Extracts page HTML** from rendered pages
5. **Parses content** using BeautifulSoup
6. **Creates Documents** for vectorstore
7. **Closes browser** automatically

## 🎯 What Gets Extracted

- All SharePoint pages from DOC360 site
- Tables (compatibility matrices, etc.)
- FAQs (question-answer pairs)
- Text content (feature definitions, etc.)
- Links and sub-pages (follows automatically)

## ⚠️ First Run Notes

- First run will **prompt you to authenticate**
- You sign in once in the browser window
- Subsequent runs can be automated
- Browser runs in headless mode (no window)

## 🐛 Troubleshooting

**"Selenium not installed":**
```bash
pip install selenium webdriver-manager
```

**"ChromeDriver error":**
```bash
pip install webdriver-manager
```

**"Authentication timeout":**
- Make sure you login within 2 minutes
- Check your browser is not blocking popups

## ✅ Ready to Use

Once setup is complete, SharePoint content will be extracted automatically every time you:
- Enable `ENABLE_SHAREPOINT_SOURCE=true`
- Run `INITIALIZE_VECTORSTORE=true`
- Start your application

Your chatbot will have access to all SharePoint knowledge base content!

