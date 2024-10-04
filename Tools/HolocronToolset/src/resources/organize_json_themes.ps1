$targetFolder = "ColorThemeJsonFiles"  # Arbitrary folder name
$hexPattern = '#[a-fA-F0-9]{6}'        # Regex pattern for hex color code

# Create target folder if it doesn't exist
if (!(Test-Path $targetFolder)) {
    New-Item -ItemType Directory -Path $targetFolder
}

# Get all JSON files in the current directory (excluding subdirectories)
$allJsonFiles = Get-ChildItem -File -Filter *.json
Write-Host "Found $($allJsonFiles.Length) total json files to parse..."
$allJsonFiles | ForEach-Object {
    $fileContent = Get-Content $_.FullName
    # Find all matches for hex color codes
    $hexMatches = [regex]::Matches($fileContent, $hexPattern).Count

    # check if there's a large amount of hexcodes being used in the file
    # anything less is probably not a theme.
    if ($hexMatches -ge 40) {
        Write-Host "`nWEACTUALLYFOUNDONE.------------------------------------`nFound $((100 * $hexMatches)/100) in file '$($_.FullName)'"
        Move-Item -LiteralPath $_.FullName -Destination $targetFolder
    } else {
        Write-Host "Deleting file '$($_.FullName)' as it contains less than 8 hex color codes ($((100 * $hexMatches)/100) total found)"
        Remove-Item -LiteralPath $_.FullName -Force
    }
}
