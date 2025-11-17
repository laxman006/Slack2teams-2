# Update .env file for full rebuild with filtered emails

$envFile = ".env"

# Settings to update/add
$settings = @{
    "INITIALIZE_VECTORSTORE" = "true"
    "ENABLE_WEB_SOURCE" = "true"
    "ENABLE_PDF_SOURCE" = "false"
    "ENABLE_EXCEL_SOURCE" = "false"
    "ENABLE_DOC_SOURCE" = "false"
    "ENABLE_SHAREPOINT_SOURCE" = "true"
    "ENABLE_OUTLOOK_SOURCE" = "true"
    "OUTLOOK_USER_EMAIL" = "presales@cloudfuze.com"
    "OUTLOOK_FOLDER_NAME" = "Inbox"
    "OUTLOOK_DATE_FILTER" = "last_12_months"
    "OUTLOOK_MAX_EMAILS" = "10000"
    "OUTLOOK_FILTER_EMAIL" = "presalesteam@cloudfuze.com"
}

Write-Host "Updating .env file for rebuild..." -ForegroundColor Yellow
Write-Host ""

# Read current .env content
if (Test-Path $envFile) {
    $content = Get-Content $envFile
} else {
    $content = @()
}

# Update or add each setting
foreach ($key in $settings.Keys) {
    $value = $settings[$key]
    $found = $false
    
    for ($i = 0; $i -lt $content.Count; $i++) {
        if ($content[$i] -match "^$key=") {
            $content[$i] = "$key=$value"
            $found = $true
            Write-Host "Updated: $key=$value" -ForegroundColor Green
            break
        }
    }
    
    if (-not $found) {
        $content += "$key=$value"
        Write-Host "Added: $key=$value" -ForegroundColor Cyan
    }
}

# Save updated content
$content | Set-Content $envFile

Write-Host ""
Write-Host "✓ .env file updated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Ready to rebuild with:" -ForegroundColor Yellow
Write-Host "  - Blogs: ALL" -ForegroundColor White
Write-Host "  - SharePoint: ALL files" -ForegroundColor White
Write-Host "  - Emails: FILTERED (presalesteam@cloudfuze.com only, last 12 months)" -ForegroundColor White

