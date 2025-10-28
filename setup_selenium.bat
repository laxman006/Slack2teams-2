@echo off
REM Setup Selenium for SharePoint extraction

echo ==================================
echo Setting up Selenium for SharePoint Extraction
echo ==================================

REM Install Selenium
echo Installing Selenium...
pip install selenium

REM Install webdriver-manager for automatic ChromeDriver setup
echo Installing webdriver-manager...
pip install webdriver-manager

echo.
echo ✅ Selenium setup complete!
echo.
echo Next steps:
echo 1. Run: python test_selenium_sharepoint.py
echo 2. Authenticate when prompted
echo 3. Let it extract all SharePoint content
echo.

pause

