#!/usr/bin/env pwsh
# Script to update all submodules in the repository with full git state reconciliation
# This script is fully idempotent and handles all edge cases including path mismatches

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
        [Parameter()] [string[]] $Arguments = @(),
        [bool]$SuppressOutput = $false
    )

    # Log the command being executed (raw, no normalization)
    if (-not $SuppressOutput) {
        $argString = if ($Arguments.Count -gt 0) { $Arguments -join ' ' } else { '' }
        $cmdString = if ($argString) { "$Tool $argString" } else { $Tool }
        Write-Host "" -ForegroundColor Gray
        Write-Host "[CMD] $cmdString" -ForegroundColor DarkGray
    }

    try {
        $output = & $Tool @Arguments 2>&1
        $exitCode = $LASTEXITCODE
        
        # Log the raw output (no filtering, no normalization)
        if (-not $SuppressOutput) {
            Write-Host "[EXIT CODE] $exitCode" -ForegroundColor DarkGray
            
            if ($null -eq $output) {
                Write-Host "[OUTPUT] (empty)" -ForegroundColor DarkGray
            }
            else {
                # Ensure output is always an array
                $outputLines = @($output)
                
                # Check if we have any output lines
                if ($outputLines.Count -eq 0 -or ($outputLines.Count -eq 1 -and [string]::IsNullOrWhiteSpace($outputLines[0]))) {
                    Write-Host "[OUTPUT] (empty)" -ForegroundColor DarkGray
                }
                else {
                    Write-Host "[OUTPUT START]" -ForegroundColor DarkGray
                    
                    # Calculate total output length
                    $totalLength = 0
                    foreach ($line in $outputLines) {
                        $totalLength += ([string]$line).Length
                    }
                    
                    # If output is excessively large (over 5000 chars), show first portion then truncate
                    if ($totalLength -gt 5000) {
                        $charCount = 0
                        $lineCount = 0
                        $charLimit = 2000
                        $lineLimit = 20

                        foreach ($line in $outputLines) {
                            $lineValue = [string]$line
                            $lineLength = $lineValue.Length

                            if ($charCount -ge $charLimit -or $lineCount -ge $lineLimit) {
                                break
                            }

                            if ($charCount + $lineLength -le $charLimit) {
                                Write-Host $lineValue -ForegroundColor Gray
                                $charCount += $lineLength
                            }
                            else {
                                $remaining = $charLimit - $charCount
                                if ($remaining -gt 0) {
                                    Write-Host ($lineValue.Substring(0, $remaining)) -ForegroundColor Gray
                                    $charCount += $remaining
                                }
                                break
                            }

                            $lineCount++
                        }

                        if ($charCount -lt $totalLength) {
                            Write-Host "" -ForegroundColor Gray
                            Write-Host "... (output truncated - showing first ~${charCount} chars of $totalLength total chars) ..." -ForegroundColor DarkGray
                        }
                    }
                    else {
                        foreach ($line in $outputLines) {
                            Write-Host $line -ForegroundColor Gray
                        }
                    }
                    Write-Host "[OUTPUT END]" -ForegroundColor DarkGray
                    Write-Host "" -ForegroundColor Gray
                }
            }
        }
        
        return [PSCustomObject]@{
            ExitCode = $exitCode
            Output   = if ($null -eq $output) { @() } elseif ($output -is [System.Array]) { $output } else { @($output) }
        }
    }
    catch {
        if (-not $SuppressOutput) {
            Write-Host "[EXCEPTION] $($_.Exception.Message)" -ForegroundColor Red
        }
        return [PSCustomObject]@{
            ExitCode = 1
            Output   = @($_.Exception.Message)
        }
    }
}

function Get-SubmodulePaths {
    $result = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--file', '.gitmodules', '--get-regexp', 'path')
    if ($result.ExitCode -ne 0) {
        $errorMsg = ($result.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        Write-WarningMessage "Unable to read .gitmodules: $errorMsg"
        return @()
    }

    $paths = @()
    foreach ($line in $result.Output) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            $splitIndex = $line.LastIndexOf(' ')
            if ($splitIndex -ge 0 -and $splitIndex -lt ($line.Length - 1)) {
                $paths += $line.Substring($splitIndex + 1).Trim()
            }
        }
    }

    return ($paths | Where-Object { $_ } | Select-Object -Unique)
}

function Get-GitConfigSubmoduleNames {
    # Collect submodule identifiers (section names) present in .git/config
    $names = @()

    $urlResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--name-only', '--get-regexp', '^submodule\..+\.url')
    if ($urlResult.ExitCode -eq 0) {
        foreach ($entry in $urlResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($entry) -and $entry -match '^submodule\.(.+)\.url$') {
                $names += $Matches[1]
            }
        }
    }

    $pathResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--name-only', '--get-regexp', '^submodule\..+\.path')
    if ($pathResult.ExitCode -eq 0) {
        foreach ($entry in $pathResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($entry) -and $entry -match '^submodule\.(.+)\.path$') {
                $names += $Matches[1]
            }
        }
    }

    return (@($names | Where-Object { $_ } | Select-Object -Unique))
}

function Get-ConfigPathForSubmodule {
    param([string]$SubmoduleName)

    if (-not $SubmoduleName) {
        return $null
    }

    $pathResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', "submodule.$SubmoduleName.path")
    if ($pathResult.ExitCode -eq 0) {
        $value = ($pathResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        if ($value) {
            return $value.Trim()
        }
    }

    return $null
}

function Test-SubmodulePathClean {
    param([string]$SubmodulePath)

    if (-not (Test-Path $SubmodulePath)) {
        return [PSCustomObject]@{
            IsClean = $true
            Reason  = "Path does not exist on disk."
        }
    }

    if (-not (Test-Path $SubmodulePath -PathType Container)) {
        return [PSCustomObject]@{
            IsClean = $false
            Reason  = "Path exists but is not a directory."
        }
    }

    $gitMarker = Join-Path $SubmodulePath ".git"
    $hasGitMetadata = Test-Path $gitMarker

    if ($hasGitMetadata) {
        # Ensure working tree is clean
        $statusResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('-C', $SubmodulePath, 'status', '--porcelain')
        if ($statusResult.ExitCode -ne 0) {
            $msg = ($statusResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
            return [PSCustomObject]@{
                IsClean = $false
                Reason  = "Unable to inspect submodule working tree: $msg"
            }
        }

        $hasChanges = $statusResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        if ($hasChanges) {
            return [PSCustomObject]@{
                IsClean = $false
                Reason  = "Working tree has local modifications or untracked files."
            }
        }

        # Determine current branch
        $branchResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('-C', $SubmodulePath, 'rev-parse', '--abbrev-ref', 'HEAD')
        if ($branchResult.ExitCode -ne 0) {
            $msg = ($branchResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
            return [PSCustomObject]@{
                IsClean = $false
                Reason  = "Unable to determine active branch: $msg"
            }
        }

        $branchName = ($branchResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        if (-not $branchName -or $branchName -eq 'HEAD') {
            return [PSCustomObject]@{
                IsClean = $false
                Reason  = "Submodule is in a detached HEAD state."
            }
        }

        # Ensure origin exists
        $remoteCheck = Invoke-ExternalCommand -Tool 'git' -Arguments @('-C', $SubmodulePath, 'remote', 'get-url', 'origin')
        if ($remoteCheck.ExitCode -ne 0) {
            return [PSCustomObject]@{
                IsClean = $false
                Reason  = "Origin remote is missing; cannot verify pushed commits."
            }
        }

        # Ensure branch is not ahead of remote
        $aheadResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('-C', $SubmodulePath, 'rev-list', '--count', "origin/${branchName}..HEAD")
        if ($aheadResult.ExitCode -ne 0) {
            $msg = ($aheadResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
            return [PSCustomObject]@{
                IsClean = $false
                Reason  = "Unable to compare with origin/${branchName}: $msg"
            }
        }

        $aheadCountRaw = ($aheadResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        try {
            $aheadCount = [int]$aheadCountRaw
        }
        catch {
            $aheadCount = -1
        }

        if ($aheadCount -gt 0) {
            return [PSCustomObject]@{
                IsClean = $false
                Reason  = "Local branch '$branchName' is ahead of origin/${branchName} by $aheadCount commit(s)."
            }
        }

        return [PSCustomObject]@{
            IsClean = $true
            Reason  = "Submodule repository is clean and fully synced with origin."
        }
    }

    # Not a git repository; ensure no tracked/untracked content in parent repo
    $statusRoot = Invoke-ExternalCommand -Tool 'git' -Arguments @('status', '--porcelain', '--', $SubmodulePath)
    if ($statusRoot.ExitCode -ne 0) {
        $msg = ($statusRoot.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        return [PSCustomObject]@{
            IsClean = $false
            Reason  = "Unable to inspect repository status for '$SubmodulePath': $msg"
        }
    }

    $hasRepoChanges = $statusRoot.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    if ($hasRepoChanges) {
        return [PSCustomObject]@{
            IsClean = $false
            Reason  = "Repository has tracked or untracked items at '$SubmodulePath'."
        }
    }

    return [PSCustomObject]@{
        IsClean = $true
        Reason  = "Directory is empty from git's perspective."
    }
}

function Remove-StaleSubmodulePathIfClean {
    param([string]$SubmodulePath)

    if (-not $SubmodulePath) {
        return
    }

    $cleanCheck = Test-SubmodulePathClean -SubmodulePath $SubmodulePath
    if (-not $cleanCheck.IsClean) {
        Write-WarningMessage "    ⚠ Preserving working directory '$SubmodulePath'."
        Write-WarningMessage "      Reason: $($cleanCheck.Reason)"
        return
    }

    if (-not (Test-Path $SubmodulePath)) {
        Write-Info "    No working directory present for '$SubmodulePath'. Nothing to remove."
        return
    }

    Write-Info "    Removing working directory '$SubmodulePath' (no local changes detected)..."
    try {
        Remove-Item -Path $SubmodulePath -Recurse -Force -ErrorAction Stop
        Write-Success "    ✓ Removed stale submodule directory: $SubmodulePath"
    }
    catch {
        Write-WarningMessage "    ⚠ Failed to remove directory '$SubmodulePath': $($_.Exception.Message)"
    }
}

function Sync-SubmoduleState {
    # Synchronizes git config with .gitmodules, handling path changes gracefully
    Write-Info ""
    Write-Info "════════════════════════════════════════════════════════════"
    Write-Info "Pre-flight Git State Reconciliation"
    Write-Info "════════════════════════════════════════════════════════════"
    
    $gitmodulesSubmodules = Get-SubmodulePaths
    $gitConfigSubmodules = Get-GitConfigSubmoduleNames
    
    $gitmodulesCount = if ($gitmodulesSubmodules -is [System.Array]) { $gitmodulesSubmodules.Count } else { if ($gitmodulesSubmodules) { 1 } else { 0 } }
    $gitConfigCount = if ($gitConfigSubmodules -is [System.Array]) { $gitConfigSubmodules.Count } else { if ($gitConfigSubmodules) { 1 } else { 0 } }
    
    Write-Info "Submodules in .gitmodules: $gitmodulesCount"
    Write-Info "Submodules in .git/config: $gitConfigCount"
    
    # Find config entries whose identifiers do not exist in .gitmodules
    $staleConfigNames = @()
    foreach ($configName in $gitConfigSubmodules) {
        if ($gitmodulesSubmodules -notcontains $configName) {
            $staleConfigNames += $configName
        }
    }
    
    if ($staleConfigNames.Count -gt 0) {
        Write-WarningMessage "⚠ Detected $($staleConfigNames.Count) stale submodule entr$(if ($staleConfigNames.Count -eq 1) { 'y' } else { 'ies' }) in git config:"
        foreach ($staleName in $staleConfigNames) {
            Write-WarningMessage "  - $staleName (present in .git/config but NOT defined in .gitmodules)"
        }
        Write-WarningMessage ""
        Write-WarningMessage "  Attempting to clean up stale git config entries and .git/modules cache..."
        
        foreach ($staleName in $staleConfigNames) {
            # Get the submodule name from git config
            Write-Info "    Removing submodule '$staleName' from git config..."
            $removeResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--remove-section', "submodule.$staleName")
            if ($removeResult.ExitCode -ne 0) {
                Write-WarningMessage "    ⚠ Warning: Could not remove submodule from git config"
                foreach ($line in $removeResult.Output) {
                    if (-not [string]::IsNullOrWhiteSpace($line)) {
                        Write-WarningMessage "      $line"
                    }
                }
            }
            else {
                Write-Success "    ✓ Removed from git config"
            }

            # Remove from .git/modules cache
            $moduleCachePath = ".git/modules/$staleName"
            if (Test-Path $moduleCachePath) {
                Write-Info "    Removing .git/modules/$staleName cache..."
                try {
                    Remove-Item -Path $moduleCachePath -Recurse -Force -ErrorAction Stop
                    Write-Success "    ✓ Removed cache directory"
                }
                catch {
                    Write-WarningMessage "    ⚠ Warning: Could not remove cache directory: $($_.Exception.Message)"
                }
            }

            $stalePath = Get-ConfigPathForSubmodule -SubmoduleName $staleName
            if (-not $stalePath) {
                $stalePath = $staleName
            }

            # Remove working directory if the submodule has been deleted and is clean
            Remove-StaleSubmodulePathIfClean -SubmodulePath $stalePath
        }
    }
    
    # Now sync .gitmodules to git config
    Write-Info ""
    Write-Info "Synchronizing .gitmodules configuration to git config..."
    
    # First, try standard sync
    $syncResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('submodule', 'sync', '--recursive')
    if ($syncResult.ExitCode -ne 0) {
        Write-WarningMessage "⚠ git submodule sync encountered issues:"
        foreach ($line in $syncResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "  $line"
            }
        }
    }
    
    # Force re-initialization of all submodules from .gitmodules
    Write-Info "  Force-initializing all submodules from .gitmodules..."
    $initResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('submodule', 'init')
    if ($initResult.ExitCode -ne 0) {
        Write-WarningMessage "⚠ git submodule init encountered issues:"
        foreach ($line in $initResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "  $line"
            }
        }
    }
    else {
        Write-Success "✓ Git state synchronized successfully"
    }
    
    # Verify no path mismatches remain
    $gitmodulesSubmodulesPost = Get-SubmodulePaths
    $gitConfigSubmodulesPost = Get-GitConfigSubmoduleNames
    
    $mismatchPaths = @()
    foreach ($gpath in $gitmodulesSubmodulesPost) {
        if ($gitConfigSubmodulesPost -notcontains $gpath) {
            $mismatchPaths += $gpath
        }
    }
    
    if ($mismatchPaths.Count -gt 0) {
        Write-WarningMessage ""
        Write-WarningMessage "⚠ MISMATCH DETECTED: After sync, the following .gitmodules paths are missing from git config:"
        foreach ($mpath in $mismatchPaths) {
            Write-WarningMessage "  - $mpath"
        }
        Write-WarningMessage "  This may indicate submodules were never initialized or git config is corrupted."
        Write-WarningMessage "  Initialization will be attempted during submodule update."
    }
    else {
        Write-Success "✓ All .gitmodules paths are now synchronized in git config"
    }
    
    Write-Info "════════════════════════════════════════════════════════════"
    Write-Info ""
}

function Get-SubmoduleUrl {
    param([string]$SubmodulePath)
    
    $result = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--file', '.gitmodules', '--get', "submodule.$SubmodulePath.url")
    if ($result.ExitCode -ne 0) {
        return $null
    }
    
    return ($result.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
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
        # GitHub wikis are accessed via owner/repo.wiki.git but the API uses owner/repo
        if ($repo -match '\.wiki$') {
            $repo = $repo -replace '\.wiki$', ''
        }
        
        return "$owner/$repo"
    }

    return $null
}

function Get-UpstreamUrl {
    param(
        [string]$OriginUrl,
        [string]$ParentFullName
    )

    if (-not $ParentFullName) {
        return $null
    }

    if ($OriginUrl -like 'git@github.com:*') {
        return "git@github.com:$ParentFullName.git"
    }

    return "https://github.com/$ParentFullName.git"
}

function Get-ForkInfo {
    param(
        [string]$RepoIdentifier,
        [bool]$GhAvailable,
        [string]$OriginUrl
    )

    $info = [PSCustomObject]@{
        IsFork              = $false
        ParentFullName      = $null
        ParentDefaultBranch = $null
        UpstreamUrl         = $null
    }

    if (-not $GhAvailable -or -not $RepoIdentifier) {
        return $info
    }

    $ghResult = Invoke-ExternalCommand -Tool 'gh' -Arguments @('api', "repos/$RepoIdentifier")
    if ($ghResult.ExitCode -ne 0) {
        Write-WarningMessage "  ⚠ Unable to query GitHub for fork information on '$RepoIdentifier'"
        Write-WarningMessage "    Command: gh api repos/$RepoIdentifier"
        Write-WarningMessage "    Exit Code: $($ghResult.ExitCode)"
        Write-WarningMessage "    Full Output:"
        foreach ($line in $ghResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "      $line"
            }
        }
        Write-WarningMessage "    Note: This may occur if gh CLI is not authenticated or the repository doesn't exist on this fork."
        return $info
    }

    try {
        $repoInfo = ($ghResult.Output | Out-String | ConvertFrom-Json)
    }
    catch {
        Write-WarningMessage "  Received invalid JSON from GitHub CLI when checking fork info."
        return $info
    }

    if (-not $repoInfo.fork) {
        return $info
    }

    if (-not $repoInfo.parent) {
        Write-WarningMessage "  This repository is flagged as a fork but the upstream metadata is unavailable (possibly deleted)."
        return $info
    }

    $parentFullName = $repoInfo.parent.full_name
    if (-not $parentFullName) {
        Write-WarningMessage "  Unable to determine parent repository name for fork."
        return $info
    }

    $info.IsFork = $true
    $info.ParentFullName = $parentFullName
    $info.ParentDefaultBranch = $repoInfo.parent.default_branch
    $info.UpstreamUrl = Get-UpstreamUrl -OriginUrl $OriginUrl -ParentFullName $parentFullName

    return $info
}

function Get-RemoteDefaultBranch {
    param(
        [string]$RemoteName = 'origin'
    )

    # Try using symbolic-ref first (more reliable)
    $symlinkResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('symbolic-ref', "refs/remotes/$RemoteName/HEAD")
    if ($symlinkResult.ExitCode -eq 0) {
        $output = ($symlinkResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        if ($output -match 'refs/remotes/.+/(.+)$') {
            return $Matches[1]
        }
    }

    # Fallback: use ls-remote --symref
    $lsRemoteResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('ls-remote', '--symref', $RemoteName, 'HEAD')
    if ($lsRemoteResult.ExitCode -eq 0) {
        foreach ($line in $lsRemoteResult.Output) {
            if ($line -match 'ref:\s+refs/heads/(.+)\s+HEAD') {
                return $Matches[1]
            }
        }
    }

    return $null
}

function Ensure-SubmoduleRemotesConfiguration {
    param(
        [string]$UpstreamUrl,
        [string]$OriginUrl = $null
    )

    if (-not (Test-WorkingTreeClean)) {
        Write-ErrorMessage "  ✗ Cannot configure remotes when working tree has uncommitted changes."
        return $false
    }

    # Resolve origin URL if not provided
    if (-not $OriginUrl) {
        $originResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', 'remote.origin.url')
        if ($originResult.ExitCode -eq 0) {
            $OriginUrl = ($originResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        }
    }

    if (-not $OriginUrl) {
        Write-ErrorMessage "  ✗ Cannot configure remotes: origin URL not found"
        return $false
    }

    Write-Info "    Current remotes before configuration:"
    $null = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', '-v')

    # Ensure origin remote URL is correct
    $checkOrigin = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', 'remote.origin.url')
    $currentOriginUrl = if ($checkOrigin.ExitCode -eq 0) { ($checkOrigin.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1) } else { $null }
    if ($currentOriginUrl -ne $OriginUrl) {
        Write-Info "    Configuring origin remote..."
        $setOriginResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', 'set-url', 'origin', $OriginUrl)
        if ($setOriginResult.ExitCode -ne 0) {
            Write-ErrorMessage "    ✗ Failed to set origin URL"
            return $false
        }
        Write-Success "      ✓ Origin configured"
    }

    $hasUpstream = $false
    if ($UpstreamUrl) {
        $checkUpstream = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', 'remote.upstream.url')
        if ($checkUpstream.ExitCode -ne 0) {
            Write-Info "    Adding upstream remote..."
            $addUpstreamResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', 'add', 'upstream', $UpstreamUrl)
            if ($addUpstreamResult.ExitCode -ne 0) {
                Write-ErrorMessage "    ✗ Failed to add upstream remote"
                return $false
            }
            Write-Success "      ✓ Upstream added"
            $hasUpstream = $true
        }
        else {
            $currentUpstreamUrl = ($checkUpstream.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
            if ($currentUpstreamUrl -ne $UpstreamUrl) {
                Write-Info "    Updating upstream remote..."
                $setUpstreamResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', 'set-url', 'upstream', $UpstreamUrl)
                if ($setUpstreamResult.ExitCode -ne 0) {
                    Write-ErrorMessage "    ✗ Failed to update upstream URL"
                    return $false
                }
                Write-Success "      ✓ Upstream updated"
            }
            $hasUpstream = $true
        }
    }

    Write-Info "    Remotes after configuration:"
    $null = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', '-v')

    # Fetch remotes so default branch information is current
    Write-Info "    Fetching remotes to refresh branch data..."
    $fetchOriginResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('fetch', 'origin')
    if ($fetchOriginResult.ExitCode -ne 0) {
        Write-WarningMessage "    ⚠ Failed to fetch from origin"
    }
    else {
        Write-Success "      ✓ Fetched from origin"
    }

    if ($hasUpstream) {
        $fetchUpstreamResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('fetch', 'upstream')
        if ($fetchUpstreamResult.ExitCode -ne 0) {
            Write-WarningMessage "    ⚠ Failed to fetch from upstream"
        }
        else {
            Write-Success "      ✓ Fetched from upstream"
        }
    }

    # Determine default branches
    $originDefaultBranch = Get-RemoteDefaultBranch -RemoteName 'origin'
    if (-not $originDefaultBranch) { $originDefaultBranch = 'master' }
    Write-Info "    Origin default branch resolved as '$originDefaultBranch'"

    $upstreamDefaultBranch = $null
    if ($hasUpstream) {
        $upstreamDefaultBranch = Get-RemoteDefaultBranch -RemoteName 'upstream'
        if (-not $upstreamDefaultBranch) { $upstreamDefaultBranch = $originDefaultBranch }
        Write-Info "    Upstream default branch resolved as '$upstreamDefaultBranch'"
    }

    # Ensure remote-tracking aliases origin/master and upstream/master exist
    $originBranchExists = $false
    $originHashResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('rev-parse', "origin/$originDefaultBranch")
    if ($originHashResult.ExitCode -eq 0) {
        $originBranchExists = $true
    }

    $upstreamBranchExists = $false
    if ($hasUpstream -and $upstreamDefaultBranch) {
        $upstreamHashResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('rev-parse', "upstream/$upstreamDefaultBranch")
        if ($upstreamHashResult.ExitCode -eq 0) {
            $upstreamBranchExists = $true
        }
    }

    # Ensure local master branch exists and tracks origin default branch
    Write-Info "    Ensuring local 'master' branch tracks origin/$originDefaultBranch..."
    $sourceRef = $null
    if ($originBranchExists) {
        $sourceRef = "origin/$originDefaultBranch"
    }
    elseif ($upstreamBranchExists) {
        $sourceRef = "upstream/$upstreamDefaultBranch"
    }

    $checkMasterResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('rev-parse', '--verify', 'master')
    if ($checkMasterResult.ExitCode -ne 0) {
        if ($sourceRef) {
            Invoke-ExternalCommand -Tool 'git' -Arguments @('checkout', '-B', 'master', $sourceRef) | Out-Null
        }
        else {
            Write-WarningMessage "    ⚠ Remote default branch not found. Creating empty 'master' branch."
            Invoke-ExternalCommand -Tool 'git' -Arguments @('checkout', '-B', 'master') | Out-Null
        }
    }
    else {
        Invoke-ExternalCommand -Tool 'git' -Arguments @('checkout', 'master') | Out-Null
    }

    # Configure branch settings for pull/push defaults
    Invoke-ExternalCommand -Tool 'git' -Arguments @('config', 'branch.master.remote', 'origin') | Out-Null
    Invoke-ExternalCommand -Tool 'git' -Arguments @('config', 'branch.master.merge', "refs/heads/$originDefaultBranch") | Out-Null
    if ($originBranchExists) {
        Invoke-ExternalCommand -Tool 'git' -Arguments @('branch', '--set-upstream-to', "origin/$originDefaultBranch", 'master') | Out-Null
    }
    else {
        Write-WarningMessage "    ⚠ origin/$originDefaultBranch does not exist; upstream configuration skipped."
    }

    if ($hasUpstream -and $upstreamBranchExists) {
        Invoke-ExternalCommand -Tool 'git' -Arguments @('config', 'branch.master.pushRemote', 'upstream') | Out-Null
        Invoke-ExternalCommand -Tool 'git' -Arguments @('config', 'remote.pushDefault', 'upstream') | Out-Null
    }

    Write-Info "    Branch configuration summary:"
    $null = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', 'branch.master.remote')
    $null = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', 'branch.master.merge')
    if ($hasUpstream -and $upstreamBranchExists) {
        $null = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', 'branch.master.pushRemote')
        $null = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', 'remote.pushDefault')
    }

    Write-Success "    ✓ Remotes and branches configured successfully"
    return $true
}

function Test-WorkingTreeClean {
    $statusResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('status', '--porcelain')
    if ($statusResult.ExitCode -ne 0) {
        Write-ErrorMessage "  ✗ Failed to check working tree status"
        return $false
    }
    
    $hasChanges = @($statusResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }).Count -gt 0
    if ($hasChanges) {
        Write-ErrorMessage "  ✗ Working tree has uncommitted changes:"
        foreach ($line in $statusResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-ErrorMessage "      $line"
            }
        }
        return $false
    }
    
    return $true
}

function Pull-From-Upstream {
    param(
        [string]$RemoteName = 'upstream'
    )

    # Check working tree is clean
    if (-not (Test-WorkingTreeClean)) {
        return $false
    }

    # Get default branch from upstream
    $upstreamDefaultBranch = Get-RemoteDefaultBranch -RemoteName $RemoteName
    if (-not $upstreamDefaultBranch) {
        Write-WarningMessage "  ⚠ Could not determine default branch on $RemoteName"
        return $false
    }

    Write-Info "    Pulling from $RemoteName/$upstreamDefaultBranch..."
    
    $pullResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('pull', '--ff-only', $RemoteName, $upstreamDefaultBranch)
    if ($pullResult.ExitCode -ne 0) {
        Write-ErrorMessage "    ✗ Pull failed"
        return $false
    }

    # Check if already up to date
    $outputStr = ($pullResult.Output | Out-String).Trim()
    $isUpToDate = $outputStr -match 'Already up to date|Already up-to-date' -or ($pullResult.Output -join ' ') -match 'Already up'
    
    if ($isUpToDate) {
        Write-Info "    ✓ Already up to date with $RemoteName/$upstreamDefaultBranch"
    }
    else {
        Write-Success "    ✓ Pulled latest from $RemoteName/$upstreamDefaultBranch"
    }

    return $true
}

function Push-To-Remote {
    param(
        [string]$RemoteName = 'origin',
        [string]$LocalBranch = 'master'
    )

    $resultInfo = [PSCustomObject]@{
        Success     = $false
        Pushed      = $false
        CommitCount = 0
    }

    # Check working tree is clean
    if (-not (Test-WorkingTreeClean)) {
        return $resultInfo
    }

    # Get default branch on origin
    $originDefaultBranch = Get-RemoteDefaultBranch -RemoteName $RemoteName
    if (-not $originDefaultBranch) {
        Write-WarningMessage "  ⚠ Could not determine default branch on $RemoteName"
        return $resultInfo
    }

    Write-Info "    Checking for commits to push to $RemoteName..."

    $commitCountResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('rev-list', '--count', "$RemoteName/$originDefaultBranch..$LocalBranch")
    if ($commitCountResult.ExitCode -ne 0) {
        Write-WarningMessage "    ⚠ Could not check for commits on $RemoteName/$originDefaultBranch"
        return $resultInfo
    }

    try {
        $resultInfo.CommitCount = [int]($commitCountResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
    }
    catch {
        $resultInfo.CommitCount = 0
    }

    if ($resultInfo.CommitCount -eq 0) {
        Write-Info "    ⊘ No commits to push to $RemoteName"
        $resultInfo.Success = $true
        return $resultInfo
    }

    Write-Info "    Found $($resultInfo.CommitCount) commit(s) to push. Pushing to $RemoteName/$originDefaultBranch..."

    $pushResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('push', $RemoteName, "$LocalBranch`:$originDefaultBranch")
    if ($pushResult.ExitCode -ne 0) {
        Write-ErrorMessage "    ✗ Push failed"
        return $resultInfo
    }

    Write-Success "    ✓ Successfully pushed $($resultInfo.CommitCount) commit(s) to $RemoteName/$originDefaultBranch"
    $resultInfo.Success = $true
    $resultInfo.Pushed = $true
    return $resultInfo
}

function Resolve-TargetBranch {
    param(
        [string]$CurrentBranch,
        [string]$RemoteHead,
        [string[]]$AvailableRemoteBranches
    )

    $preferredBranches = @()
    if ($CurrentBranch) { $preferredBranches += $CurrentBranch }
    if ($RemoteHead) { $preferredBranches += $RemoteHead }
    $preferredBranches += @('main', 'master')

    foreach ($candidate in $preferredBranches | Where-Object { $_ }) {
        if ($AvailableRemoteBranches -contains "origin/$candidate") {
            return $candidate
        }
    }

    return $null
}

function Get-RemoteHeadBranch {
    $remoteShow = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', 'show', 'origin')
    if ($remoteShow.ExitCode -ne 0) {
        return $null
    }

    foreach ($line in $remoteShow.Output) {
        if ($line -match 'HEAD branch:\s*(\S+)') {
            return $Matches[1]
        }
    }

    return $null
}

function Set-BranchContext {
    param(
        [string]$BranchName
    )

    $currentBranchResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('branch', '--show-current')
    $currentBranch = ($currentBranchResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)

    if ($currentBranch -eq $BranchName) {
        return $true
    }

    $remoteRefCheck = Invoke-ExternalCommand -Tool 'git' -Arguments @('show-ref', '--verify', '--quiet', "refs/remotes/origin/$BranchName")
    if ($remoteRefCheck.ExitCode -ne 0) {
        $prefetch = Invoke-ExternalCommand -Tool 'git' -Arguments @('fetch', 'origin', $BranchName)
        if ($prefetch.ExitCode -ne 0) {
            $errorMsg = ($prefetch.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
            Write-WarningMessage "  Unable to fetch origin/${BranchName} to prepare local branch context: $errorMsg"
            return $false
        }
    }

    # Try to checkout existing branch first
    $checkoutResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('checkout', $BranchName)
    if ($checkoutResult.ExitCode -eq 0) {
        return $true
    }

    # Create local branch tracking origin/<branch>
    $createResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('checkout', '-B', $BranchName, "origin/$BranchName")
    if ($createResult.ExitCode -eq 0) {
        return $true
    }

    Write-WarningMessage "  Unable to switch to branch '$BranchName'."
    return $false
}

function Get-RemoteBranches {
    $result = Invoke-ExternalCommand -Tool 'git' -Arguments @('ls-remote', '--heads', 'origin')
    if ($result.ExitCode -ne 0) {
        $errorMsg = ($result.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        Write-WarningMessage "  Unable to list remote branches from origin: $errorMsg"
        Write-WarningMessage "    Full diagnostic output:"
        foreach ($line in $result.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "      $line"
            }
        }
        return @()
    }

    $branches = @()
    foreach ($line in $result.Output) {
        if (-not [string]::IsNullOrWhiteSpace($line)) {
            $parts = $line -split '\t'
            $refName = ($parts | Select-Object -Last 1).Trim()
            if ($refName -match '^refs/heads/(.+)$') {
                $branchName = $Matches[1].Trim()
                $branches += "origin/$branchName"
            }
        }
    }

    return $branches
}

function Update-From-Origin {
    param(
        [string]$BranchName
    )

    Write-Info "  Checking origin for updates..."
    
    $pullResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('pull', '--ff-only', 'origin', $BranchName)
    if ($pullResult.ExitCode -ne 0) {
        Write-ErrorMessage "  ✗ Failed to update from origin/$BranchName"
        return $false
    }

    $outputStr = ($pullResult.Output | Out-String).Trim()
    $isUpToDate = $outputStr -match 'Already up to date|Already up-to-date' -or $pullResult.Output -contains 'Already up to date.'

    if ($isUpToDate) {
        Write-Info "    ✓ Origin already up to date for branch '$BranchName'"
    }
    else {
        Write-Success "    ✓ Updated from origin/$BranchName"
    }

    return $true
}

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN SCRIPT
# ═══════════════════════════════════════════════════════════════════════════════

Write-Info "════════════════════════════════════════════════════════════"
Write-Info "PyKotor Git Submodule Update Utility"
Write-Info "════════════════════════════════════════════════════════════"

# First, reconcile git state with .gitmodules
Sync-SubmoduleState

Write-Host "git submodule sync; git submodule update --init --recursive"
Invoke-ExternalCommand -Tool 'git' -Arguments @('submodule', 'sync')
Invoke-ExternalCommand -Tool 'git' -Arguments @('submodule', 'update', '--init', '--recursive')

Write-Info "Updating all submodules..."

$ghAvailable = $null -ne (Get-Command gh -ErrorAction SilentlyContinue)
if (-not $ghAvailable) {
    Write-WarningMessage "GitHub CLI (gh) is not available; fork detection will be limited."
}

$submodules = @(Get-SubmodulePaths)
if ($submodules.Count -eq 0) {
    Write-WarningMessage "No submodules found in this repository."
    exit 0
}

Write-Info "Found $($submodules.Count) submodule(s) to process"

$updatedCount = 0
$skippedCount = 0
$failedCount = 0

foreach ($submodule in $submodules) {
    Write-Info ""
    Write-Info "Updating submodule: $submodule"

    # Initialize submodule if it doesn't exist
    if (-not (Test-Path $submodule)) {
        Write-Info "  Submodule path '$submodule' does not exist locally. Initializing..."
        
        # Get the URL from .gitmodules
        $submoduleUrl = Get-SubmoduleUrl -SubmodulePath $submodule
        if (-not $submoduleUrl) {
            Write-ErrorMessage "  ✗ FAILED: Could not find URL for submodule '$submodule' in .gitmodules"
            Write-ErrorMessage "    Config lookup: git config --file .gitmodules --get submodule.$submodule.url"
            Write-ErrorMessage "    This indicates .gitmodules may be malformed for this entry"
            $failedCount++
            continue
        }
        
        Write-Info "    Source URL: $submoduleUrl"
        
        # Create parent directory if needed
        $parentDir = Split-Path -Parent $submodule
        if ($parentDir -and -not (Test-Path $parentDir)) {
            try {
                New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
                Write-Info "    Created parent directory: $parentDir"
            }
            catch {
                Write-ErrorMessage "  ✗ FAILED: Could not create parent directory '$parentDir'"
                Write-ErrorMessage "    Error: $($_.Exception.Message)"
                $failedCount++
                continue
            }
        }
        
        # Clone directly from URL
        Write-Info "    Cloning repository..."
        $cloneResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('clone', $submoduleUrl, $submodule)
        if ($cloneResult.ExitCode -ne 0) {
            Write-ErrorMessage "  ✗ FAILED: Could not clone submodule '$submodule'"
            Write-ErrorMessage "    URL: $submoduleUrl"
            Write-ErrorMessage "    Command: git clone $submoduleUrl $submodule"
            Write-ErrorMessage "    Exit Code: $($cloneResult.ExitCode)"
            Write-ErrorMessage "    Full Output:"
            foreach ($line in $cloneResult.Output) {
                if (-not [string]::IsNullOrWhiteSpace($line)) {
                    Write-ErrorMessage "      $line"
                }
            }
            $failedCount++
            continue
        }
        Write-Success "  ✓ Cloned submodule: $submodule"
    }
    
    # Check if submodule has a corrupted .git file (pointing to wrong .git/modules path)
    $submoduleGitFile = Join-Path $submodule ".git"
    if ((Test-Path $submoduleGitFile) -and -not (Test-Path $submoduleGitFile -PathType Container)) {
        # It's a .git file (not a directory), read its contents
        try {
            $gitFileContent = Get-Content $submoduleGitFile -Raw -ErrorAction Stop
            if ($gitFileContent -match 'gitdir:\s*(.+)') {
                $gitdirPath = $Matches[1].Trim()
                $absoluteGitdirPath = Join-Path (Get-Location).Path (Join-Path $submodule $gitdirPath)
                $absoluteGitdirPath = [System.IO.Path]::GetFullPath($absoluteGitdirPath)
                
                if (-not (Test-Path $absoluteGitdirPath)) {
                    Write-WarningMessage "  ⚠ Detected corrupted .git file in submodule"
                    Write-WarningMessage "    .git file points to: $gitdirPath"
                    Write-WarningMessage "    Resolved path: $absoluteGitdirPath"
                    Write-WarningMessage "    This path does not exist (likely from old path in git config)"
                    Write-WarningMessage ""
                    Write-WarningMessage "  ✗ SKIPPING: Cannot update submodule with corrupted git linkage"
                    Write-WarningMessage "    Manual fix required:"
                    Write-WarningMessage "      1. Backup any local changes in '$submodule'"
                    Write-WarningMessage "      2. Remove the submodule: rm -rf $submodule"
                    Write-WarningMessage "      3. Remove git module cache: rm -rf .git/modules/$submodule"
                    Write-WarningMessage "      4. Re-run this script to clone fresh"
                    Write-WarningMessage ""
                    $skippedCount++
                    continue
                }
            }
        }
        catch {
            Write-WarningMessage "  ⚠ Could not validate .git file: $($_.Exception.Message)"
        }
    }

    # Enter submodule directory
    try {
        Push-Location $submodule
    }
    catch {
        Write-ErrorMessage "  ✗ FAILED: Unable to enter submodule directory '$submodule'"
        Write-ErrorMessage "    Error: $($_.Exception.Message)"
        $failedCount++
        continue
    }

    try {
        Write-Info "  Remotes (git remote -v):"
        $null = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', '-v')

        # Get origin URL
        $originUrlResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('config', '--get', 'remote.origin.url')
        $originUrl = ($originUrlResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        if (-not $originUrl) {
            Write-WarningMessage "  ✗ Unable to determine origin URL for submodule. Skipping update."
            $skippedCount++
            continue
        }

        $repoIdentifier = Get-RepoIdentifierFromUrl -Url $originUrl

        # Get remote branches
        $remoteBranches = @(Get-RemoteBranches)
        if ($remoteBranches.Count -eq 0) {
            Write-WarningMessage "  ✗ No remote branches detected on origin. Skipping update."
            Write-WarningMessage "    This may indicate the remote is unreachable or the repository is empty."
            $skippedCount++
            continue
        }

        # Determine target branch
        $currentBranchResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('branch', '--show-current')
        $currentBranch = ($currentBranchResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)

        $remoteHead = Get-RemoteHeadBranch
        $targetBranch = Resolve-TargetBranch -CurrentBranch $currentBranch -RemoteHead $remoteHead -AvailableRemoteBranches $remoteBranches

        if (-not $targetBranch) {
            Write-WarningMessage "  ✗ Unable to determine a branch to update. Available branches: $($remoteBranches -join ', ')"
            $skippedCount++
            continue
        }

        Write-Info "  Target branch: $targetBranch"

        # Switch to target branch
        if (-not (Set-BranchContext -BranchName $targetBranch)) {
            $skippedCount++
            continue
        }

        # Update from origin
        if (-not (Update-From-Origin -BranchName $targetBranch)) {
            $skippedCount++
            continue
        }

        # Check if this is a fork and setup remotes for proper pull/push workflow
        $forkInfo = Get-ForkInfo -RepoIdentifier $repoIdentifier -GhAvailable $ghAvailable -OriginUrl $originUrl

        if ($forkInfo.IsFork -and $forkInfo.UpstreamUrl) {
            Write-Info "  Detected fork of: $($forkInfo.ParentFullName)"
            
            # Configure remotes idempotently
            Write-Info "  Configuring remotes for fork workflow..."
            if (Ensure-SubmoduleRemotesConfiguration -UpstreamUrl $forkInfo.UpstreamUrl -OriginUrl $originUrl) {
                Write-Info "  ✓ Fork remotes configured"
                
                # Pull latest from upstream
                Write-Info "  Pulling latest from upstream..."
                if (Pull-From-Upstream -RemoteName 'upstream') {
                    Write-Info "  ✓ Successfully pulled from upstream"
                    
                    # Push to upstream (original)
                    Write-Info "  Pushing updates to upstream (original)..."
                    $pushUpstream = Push-To-Remote -RemoteName 'upstream' -LocalBranch 'master'
                    if ($pushUpstream.Success) {
                        if ($pushUpstream.Pushed) {
                            Write-Success "  ✓ Upstream updated (pushed $($pushUpstream.CommitCount) commit(s))"
                        }
                        else {
                            Write-Info "  ⊘ Upstream push skipped (no commits to push)"
                        }
                    }
                    else {
                        Write-WarningMessage "  ⚠ Could not push to upstream"
                    }

                    # Push to origin (fork)
                    Write-Info "  Pushing updates to fork (origin)..."
                    $pushOrigin = Push-To-Remote -RemoteName 'origin' -LocalBranch 'master'
                    if ($pushOrigin.Success) {
                        if ($pushOrigin.Pushed) {
                            Write-Success "  ✓ Fork updated (pushed $($pushOrigin.CommitCount) commit(s))"
                        }
                        else {
                            Write-Info "  ⊘ Fork push skipped (no commits to push)"
                        }
                    }
                    else {
                        Write-WarningMessage "  ⚠ Could not push to fork"
                    }
                }
                else {
                    Write-WarningMessage "  ⚠ Could not pull from upstream"
                }
            }
            else {
                Write-WarningMessage "  ⚠ Could not configure remotes"
            }
        }
        else {
            if (-not $forkInfo.IsFork) {
                Write-Info "  ⊘ Not a fork (upstream sync not applicable)."
            }
            else {
                Write-WarningMessage "  ⚠ Fork detected but upstream URL not available."
            }
        }

        $updatedCount++
    }
    catch {
        Write-ErrorMessage "  ✗ FAILED: Unexpected error while updating '$submodule'"
        Write-ErrorMessage "    Error: $($_.Exception.Message)"
        Write-ErrorMessage "    Stack Trace: $($_.StackTrace)"
        $failedCount++
    }
    finally {
        Pop-Location
    }
}

# ═══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

Write-Info ""
Write-Info "════════════════════════════════════════════════════════════"
Write-Info "Submodule Update Summary:"
Write-Info "════════════════════════════════════════════════════════════"
Write-Success "  ✓ Successfully Updated: $updatedCount"
Write-WarningMessage "  ⊘ Skipped (No Changes Needed): $skippedCount"

if ($failedCount -gt 0) {
    Write-ErrorMessage "  ✗ Failed: $failedCount"
    Write-Info "════════════════════════════════════════════════════════════"
    Write-ErrorMessage "⚠ Some submodules encountered errors. Review the output above for details."
    Write-Info ""
    exit 1
}

Write-Info "  ✗ Failed: $failedCount"
Write-Info "════════════════════════════════════════════════════════════"
Write-Success "✓ All submodule operations completed successfully!"
Write-Info ""
