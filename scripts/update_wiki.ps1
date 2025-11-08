#!/usr/bin/env pwsh
# Script to update the wiki submodule

Write-Host "Updating wiki submodule..." -ForegroundColor Cyan

# Navigate to the submodule directory
Push-Location wiki

try {
    # Fetch latest changes
    git fetch origin
    
    # Pull the latest master branch
    git pull origin master
    
    Write-Host "✓ Wiki submodule updated successfully" -ForegroundColor Green
} catch {
    Write-Host "✗ Error updating wiki submodule: $_" -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}

Write-Host "Done!" -ForegroundColor Cyan

