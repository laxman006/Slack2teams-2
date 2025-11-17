# Update .env to include BOTH email addresses for full year capture

$envFile = ".env"
$content = Get-Content $envFile

Write-Host "Updating OUTLOOK_FILTER_EMAIL to include both addresses..." -ForegroundColor Yellow
Write-Host ""

# Update OUTLOOK_FILTER_EMAIL
$found = $false
for ($i = 0; $i -lt $content.Count; $i++) {
    if ($content[$i] -match "^OUTLOOK_FILTER_EMAIL=") {
        $content[$i] = "OUTLOOK_FILTER_EMAIL=pre-sales@cloudfuze.com,presalesteam@cloudfuze.com"
        $found = $true
        Write-Host "Updated: OUTLOOK_FILTER_EMAIL" -ForegroundColor Green
        break
    }
}

if (-not $found) {
    $content += "OUTLOOK_FILTER_EMAIL=pre-sales@cloudfuze.com,presalesteam@cloudfuze.com"
    Write-Host "Added: OUTLOOK_FILTER_EMAIL" -ForegroundColor Cyan
}

# Ensure OUTLOOK_DATE_FILTER is set to last_year
$foundDate = $false
for ($i = 0; $i -lt $content.Count; $i++) {
    if ($content[$i] -match "^OUTLOOK_DATE_FILTER=") {
        $content[$i] = "OUTLOOK_DATE_FILTER=last_year"
        $foundDate = $true
        break
    }
}

if (-not $foundDate) {
    $content += "OUTLOOK_DATE_FILTER=last_year"
}

# Save
$content | Set-Content $envFile

Write-Host ""
Write-Host "✓ .env updated successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Filter now includes:" -ForegroundColor Yellow
Write-Host "  • pre-sales@cloudfuze.com (old address - for older emails)" -ForegroundColor White
Write-Host "  • presalesteam@cloudfuze.com (new distribution list - recent emails)" -ForegroundColor White
Write-Host ""
Write-Host "Date range: last_year (365 days)" -ForegroundColor Yellow

