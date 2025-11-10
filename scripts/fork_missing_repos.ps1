#!/usr/bin/env pwsh
# Script to fork missing submodule repositories to th3w1zard1 user account
# This script uses 'gh repo fork' to create forks of repositories that are
# referenced in .gitmodules but haven't been forked yet to th3w1zard1

Set-StrictMode -Version Latest

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-WarningMessage {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Invoke-ExternalCommand {
    param(
        [Parameter(Mandatory = $true)] [string] $Tool,
        [Parameter()] [string[]] $Arguments = @()
    )

    try {
        $output = & $Tool @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        return [PSCustomObject]@{
            ExitCode = $exitCode
            Output   = if ($null -eq $output) { @() } elseif ($output -is [System.Array]) { $output } else { @($output) }
        }
    } catch {
        return [PSCustomObject]@{
            ExitCode = 1
            Output   = @($_.Exception.Message)
        }
    }
}

function Get-RepoIdentifierFromUrl {
    param([string]$Url)

    if (-not $Url) {
        return $null
    }

    $regex = [regex]'github\.com[:\/](?<owner>[^\/]+)\/(?<repo>[^\/]+?)(?:\.git)?$'
    $match = $regex.Match($Url)
    if ($match.Success) {
        $owner = $match.Groups['owner'].Value
        $repo = $match.Groups['repo'].Value
        
        # For wiki repositories (ends with .wiki), remove .wiki suffix to get the actual repo name
        if ($repo -match '\.wiki$') {
            $repo = $repo -replace '\.wiki$', ''
        }
        
        return "$owner/$repo"
    }

    return $null
}

function Get-ForkInfo {
    param(
        [string]$RepoIdentifier
    )

    $info = [PSCustomObject]@{
        IsFork             = $false
        ParentFullName     = $null
        ParentDefaultBranch = $null
    }

    if (-not $RepoIdentifier) {
        return $info
    }

    $ghResult = Invoke-ExternalCommand -Tool 'gh' -Arguments @('api', "repos/$RepoIdentifier")
    if ($ghResult.ExitCode -ne 0) {
        return $info
    }

    try {
        $repoInfo = ($ghResult.Output | Out-String | ConvertFrom-Json)
    } catch {
        return $info
    }

    if (-not $repoInfo.fork) {
        return $info
    }

    if (-not $repoInfo.parent) {
        return $info
    }

    $parentFullName = $repoInfo.parent.full_name
    if (-not $parentFullName) {
        return $info
    }

    $info.IsFork = $true
    $info.ParentFullName = $parentFullName
    $info.ParentDefaultBranch = $repoInfo.parent.default_branch

    return $info
}

# Repos that failed to clone - we need to determine their original upstream repos
# Format: @{ LocalPath = "vendor/xyz"; FailedUrl = "https://github.com/th3w1zard1/xyz.git"; UpstreamRepo = "original/xyz" }
$failedRepos = @(
    @{ LocalPath = "wiki"; FailedUrl = "https://github.com/th3w1zard1/PyKotor.wiki.git"; UpstreamRepo = $null; Note = "GitHub wiki - special handling needed" },
    @{ LocalPath = "vendor/CHORD"; FailedUrl = "https://github.com/th3w1zard1/CHORD.git"; UpstreamRepo = $null; Note = "Need to identify upstream" },
    @{ LocalPath = "vendor/pazaak-eggborne"; FailedUrl = "https://github.com/th3w1zard1/pazaak-eggborne.git"; UpstreamRepo = "eggborne/pazaak-eggborne" },
    @{ LocalPath = "vendor/pure-pazaak-michaeljoelphillips"; FailedUrl = "https://github.com/th3w1zard1/pure-pazaak-michaeljoelphillips.git"; UpstreamRepo = "michaeljoelphillips/pure-pazaak" },
    @{ LocalPath = "vendor/pazaak-loomisdf"; FailedUrl = "https://github.com/th3w1zard1/pazaak-loomisdf.git"; UpstreamRepo = "loomisdf/Pazaak-Card-Game-Clone" },
    @{ LocalPath = "vendor/pazaak-alexander-ye"; FailedUrl = "https://github.com/th3w1zard1/pazaak-alexander-ye.git"; UpstreamRepo = "alexander-ye/Pazaak" },
    @{ LocalPath = "vendor/Pazaak-sKm-games"; FailedUrl = "https://github.com/th3w1zard1/Pazaak-sKm-games.git"; UpstreamRepo = "sKm-games/Pazaak" },
    @{ LocalPath = "vendor/Pazaak-Camputron"; FailedUrl = "https://github.com/th3w1zard1/Pazaak-Camputron.git"; UpstreamRepo = "Camputron/Pazaak" },
    @{ LocalPath = "vendor/pazaak-EclecticTaco"; FailedUrl = "https://github.com/th3w1zard1/pazaak-EclecticTaco.git"; UpstreamRepo = "EclecticTaco/Pazaak-WebVersion" },
    @{ LocalPath = "vendor/pazaak-eMonk42"; FailedUrl = "https://github.com/th3w1zard1/pazaak-eMonk42.git"; UpstreamRepo = "eMonk42/Pazaak" },
    @{ LocalPath = "vendor/Pazaak-ebc1201"; FailedUrl = "https://github.com/th3w1zard1/Pazaak-ebc1201.git"; UpstreamRepo = "ebc1201/Pazaak" },
    @{ LocalPath = "vendor/Pazaak-JustWaltuh"; FailedUrl = "https://github.com/th3w1zard1/Pazaak-JustWaltuh.git"; UpstreamRepo = "JustWaltuh/Pazaak" },
    @{ LocalPath = "vendor/pure-pazaak-LinkWentz"; FailedUrl = "https://github.com/th3w1zard1/pure-pazaak-LinkWentz.git"; UpstreamRepo = "LinkWentz/pure-pazaak" },
    @{ LocalPath = "vendor/ConsolePazaak"; FailedUrl = "https://github.com/th3w1zard1/ConsolePazaak.git"; UpstreamRepo = "OhRyanOh/ConsolePazaak" },
    @{ LocalPath = "vendor/pazaak-KhanRayhanAli"; FailedUrl = "https://github.com/th3w1zard1/pazaak-KhanRayhanAli.git"; UpstreamRepo = "KhanRayhanAli/Pazaak" },
    @{ LocalPath = "vendor/Kotor.NET"; FailedUrl = "https://github.com/th3w1zard1/Kotor.NET.git"; UpstreamRepo = $null; Note = "Need to identify upstream" }
)

Write-Info ""
Write-Info "════════════════════════════════════════════════════════════"
Write-Info "PyKotor Fork Missing Repositories Utility"
Write-Info "════════════════════════════════════════════════════════════"
Write-Info ""

# Check if gh CLI is available
$ghCheck = Invoke-ExternalCommand -Tool 'gh' -Arguments @('--version')
if ($ghCheck.ExitCode -ne 0) {
    Write-ErrorMessage "GitHub CLI (gh) is not available or not installed."
    Write-ErrorMessage "Please install it from: https://cli.github.com/"
    exit 1
}

Write-Success "✓ GitHub CLI detected: $($ghCheck.Output[0])"
Write-Info ""

# Check if user is authenticated
$whoamiResult = Invoke-ExternalCommand -Tool 'gh' -Arguments @('auth', 'status')
if ($whoamiResult.ExitCode -ne 0) {
    Write-ErrorMessage "Not authenticated with GitHub CLI."
    Write-ErrorMessage "Please run: gh auth login"
    exit 1
}

Write-Success "✓ Authenticated with GitHub CLI"
Write-Info ""

$successCount = 0
$failCount = 0
$skipCount = 0

foreach ($repo in $failedRepos) {
    $localPath = $repo.LocalPath
    $upstreamRepo = $repo.UpstreamRepo
    
    Write-Info "════════════════════════════════════════════════════════════"
    Write-Info "Forking: $localPath"
    if ($repo.PSObject.Properties.Name -contains 'Note' -and -not [string]::IsNullOrEmpty($repo.Note)) {
        Write-WarningMessage "Note: $($repo.Note)"
    }
    
    if (-not $upstreamRepo) {
        Write-WarningMessage "⊘ Skipping: Upstream repository not identified. Please fork manually."
        $skipCount++
        continue
    }
    
    $repoName = [System.IO.Path]::GetFileName($localPath)
    Write-Info "  Upstream: $upstreamRepo"
    Write-Info "  Target: th3w1zard1/$repoName"
    
    # Try to fork the repository (note: fork in user account, then rename if needed)
    $forkResult = Invoke-ExternalCommand -Tool 'gh' -Arguments @('repo', 'fork', $upstreamRepo, '--fork-name=' + $repoName)
    
    if ($forkResult.ExitCode -eq 0) {
        Write-Success "✓ Successfully forked $upstreamRepo"
        $successCount++
    } else {
        Write-ErrorMessage "✗ Failed to fork $upstreamRepo"
        foreach ($line in $forkResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-ErrorMessage "  $line"
            }
        }
        $failCount++
    }
    Write-Info ""
}

Write-Info "════════════════════════════════════════════════════════════"
Write-Info "Fork Summary:"
Write-Info "════════════════════════════════════════════════════════════"
Write-Success "✓ Successfully forked: $successCount"
if ($skipCount -gt 0) {
    Write-WarningMessage "⊘ Skipped (manual action needed): $skipCount"
}
if ($failCount -gt 0) {
    Write-ErrorMessage "✗ Failed: $failCount"
}
Write-Info ""

if ($failCount -gt 0 -or $skipCount -gt 0) {
    Write-WarningMessage "⚠ Some repositories need attention. See output above for details."
    exit 1
} else {
    Write-Success "✓ All repositories forked successfully!"
    exit 0
}

