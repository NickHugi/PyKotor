param (
    [string]$version = "1.0.0"
)

$projectRoot = "$PSScriptRoot\..\..\.."
$toolPath = "$PSScriptRoot\.."
$distPath = "$projectRoot\dist\HoloPazaak"

# Clean dist
if (Test-Path $distPath) {
    Remove-Item $distPath -Recurse -Force
}

# Install dependencies if needed (using uv/pip)
# Assuming environment is already set up or managed via standard flows

# Run PyInstaller
pyinstaller --noconfirm --onefile --windowed --name "HoloPazaak" `
    --add-data "$toolPath/src/holopazaak/data;holopazaak/data" `
    --paths "$toolPath/src" `
    "$toolPath/src/holopazaak/app.py" `
    --distpath "$distPath" `
    --workpath "$PSScriptRoot\build" `
    --specpath "$PSScriptRoot"

Write-Host "Build complete. Output in $distPath"

