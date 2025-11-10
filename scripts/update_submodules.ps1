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
        } catch {
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
    } catch {
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
            } else {
                Write-Success "    ✓ Removed from git config"
            }

            # Remove from .git/modules cache
            $moduleCachePath = ".git/modules/$staleName"
            if (Test-Path $moduleCachePath) {
                Write-Info "    Removing .git/modules/$staleName cache..."
                try {
                    Remove-Item -Path $moduleCachePath -Recurse -Force -ErrorAction Stop
                    Write-Success "    ✓ Removed cache directory"
                } catch {
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
    } else {
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
    } else {
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
        IsFork             = $false
        ParentFullName     = $null
        ParentDefaultBranch = $null
        UpstreamUrl        = $null
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
    } catch {
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

    $pullResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('pull', '--ff-only', 'origin', $BranchName)
    if ($pullResult.ExitCode -ne 0) {
        $errorMsg = ($pullResult.Output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -First 1)
        Write-WarningMessage "  Unable to fast-forward with origin/${BranchName}: ${errorMsg}"
        Write-WarningMessage "    Full diagnostic output:"
        foreach ($line in $pullResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "      $line"
            }
        }
        return $false
    }

    $outputStr = ($pullResult.Output | Out-String).Trim()
    $isUpToDate = $outputStr -match 'Already up to date|Already up-to-date' -or $pullResult.Output -contains 'Already up to date.'

    if ($isUpToDate) {
        Write-Info "  ⊘ Origin already up to date for branch '$BranchName'."
    } else {
        Write-Success "  ✓ Updated from origin/$BranchName."
    }

    return $true
}

function Update-From-Upstream {
    param(
        [string]$TempRemoteName,
        [string]$UpstreamUrl,
        [string]$TargetBranch
    )

    $addRemote = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', 'add', $TempRemoteName, $UpstreamUrl)
    if ($addRemote.ExitCode -ne 0) {
        # Attempt to overwrite if remote already exists
        $setRemote = Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', 'set-url', $TempRemoteName, $UpstreamUrl)
        if ($setRemote.ExitCode -ne 0) {
            Write-WarningMessage "  Unable to add temporary upstream remote ($UpstreamUrl)."
            Write-WarningMessage "    Full diagnostic output:"
            foreach ($line in $setRemote.Output) {
                if (-not [string]::IsNullOrWhiteSpace($line)) {
                    Write-WarningMessage "      $line"
                }
            }
            return $false
        }
    }

    $fetchResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('fetch', $TempRemoteName, $TargetBranch)
    if ($fetchResult.ExitCode -ne 0) {
        Write-WarningMessage "  Failed to fetch $TargetBranch from upstream ($UpstreamUrl)."
        Write-WarningMessage "    Command: git fetch $TempRemoteName $TargetBranch"
        Write-WarningMessage "    Exit Code: $($fetchResult.ExitCode)"
        Write-WarningMessage "    Full Output:"
        foreach ($line in $fetchResult.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "      $line"
            }
        }
        return $false
    }

    $mergeRef = "$TempRemoteName/$TargetBranch"

    $revParse = Invoke-ExternalCommand -Tool 'git' -Arguments @('rev-parse', $mergeRef)
    if ($revParse.ExitCode -ne 0) {
        Write-WarningMessage "  Upstream branch '$TargetBranch' does not exist."
        Write-WarningMessage "    Command: git rev-parse $mergeRef"
        Write-WarningMessage "    Exit Code: $($revParse.ExitCode)"
        Write-WarningMessage "    Full Output:"
        foreach ($line in $revParse.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "      $line"
            }
        }
        return $false
    }

    $upToDateCheck = Invoke-ExternalCommand -Tool 'git' -Arguments @('merge-base', '--is-ancestor', $mergeRef, 'HEAD')
    if ($upToDateCheck.ExitCode -eq 0) {
        Write-Info "  ⊘ Upstream already up to date (all changes already present locally)."
        return $true
    }

    $canFastForward = Invoke-ExternalCommand -Tool 'git' -Arguments @('merge-base', '--is-ancestor', 'HEAD', $mergeRef)
    if ($canFastForward.ExitCode -eq 0) {
        $ffMerge = Invoke-ExternalCommand -Tool 'git' -Arguments @('merge', '--ff-only', $mergeRef)
        if ($ffMerge.ExitCode -ne 0) {
            Write-WarningMessage "  ✗ Unable to fast-forward to upstream/$TargetBranch"
            Write-WarningMessage "    Reason: Fast-forward merge failed"
            Write-WarningMessage "    Command: git merge --ff-only $mergeRef"
            Write-WarningMessage "    Exit Code: $($ffMerge.ExitCode)"
            Write-WarningMessage "    Output:"
            foreach ($line in $ffMerge.Output) {
                if (-not [string]::IsNullOrWhiteSpace($line)) {
                    Write-WarningMessage "      $line"
                }
            }
            return $false
        }

        Write-Success "  ✓ Fast-forwarded to match upstream/$TargetBranch."
        return $true
    }

    $testMerge = Invoke-ExternalCommand -Tool 'git' -Arguments @('merge', '--no-commit', '--no-ff', $mergeRef)
    if ($testMerge.ExitCode -ne 0) {
        Invoke-ExternalCommand -Tool 'git' -Arguments @('merge', '--abort') | Out-Null
        Write-WarningMessage "  ✗ Merge conflicts detected when trying to merge upstream/$TargetBranch"
        Write-WarningMessage "    Reason: Conflicting changes between local fork and upstream repository"
        Write-WarningMessage "    This usually means the upstream has diverged from the fork"
        Write-WarningMessage "    Skipping fork sync to preserve local modifications"
        Write-WarningMessage "    Command: git merge --no-commit --no-ff $mergeRef"
        Write-WarningMessage "    Exit Code: $($testMerge.ExitCode)"
        Write-WarningMessage "    Full Output:"
        foreach ($line in $testMerge.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "      $line"
            }
        }
        return $false
    }

    # Abort the dry-run merge
    Invoke-ExternalCommand -Tool 'git' -Arguments @('merge', '--abort') | Out-Null

    $fullMerge = Invoke-ExternalCommand -Tool 'git' -Arguments @('merge', '--no-ff', '--no-edit', $mergeRef)
    if ($fullMerge.ExitCode -ne 0) {
        Invoke-ExternalCommand -Tool 'git' -Arguments @('merge', '--abort') | Out-Null
        Write-WarningMessage "  ✗ Merge with upstream/$TargetBranch failed"
        Write-WarningMessage "    Command: git merge --no-ff --no-edit $mergeRef"
        Write-WarningMessage "    Exit Code: $($fullMerge.ExitCode)"
        Write-WarningMessage "    Output:"
        foreach ($line in $fullMerge.Output) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-WarningMessage "      $line"
            }
        }
        Write-WarningMessage "    Skipping fork sync for this submodule"
        return $false
    }

    Write-Success "  ✓ Merged upstream/$TargetBranch without conflicts."
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
            } catch {
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
        } catch {
            Write-WarningMessage "  ⚠ Could not validate .git file: $($_.Exception.Message)"
        }
    }

    # Enter submodule directory
    try {
        Push-Location $submodule
    } catch {
        Write-ErrorMessage "  ✗ FAILED: Unable to enter submodule directory '$submodule'"
        Write-ErrorMessage "    Error: $($_.Exception.Message)"
        $failedCount++
        continue
    }

    try {
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

        # Check if this is a fork and update from upstream
        $forkInfo = Get-ForkInfo -RepoIdentifier $repoIdentifier -GhAvailable $ghAvailable -OriginUrl $originUrl

        $upstreamUpdated = $false
        if ($forkInfo.IsFork -and $forkInfo.UpstreamUrl) {
            Write-Info "  Detected fork of: $($forkInfo.ParentFullName)"
            $upstreamBranch = if ($forkInfo.ParentDefaultBranch) { $forkInfo.ParentDefaultBranch } else { $targetBranch }
            $tempRemoteName = '__update_submodules_upstream__'

            try {
                $upstreamUpdated = Update-From-Upstream -TempRemoteName $tempRemoteName -UpstreamUrl $forkInfo.UpstreamUrl -TargetBranch $upstreamBranch
                if ($upstreamUpdated) {
                    $pushResult = Invoke-ExternalCommand -Tool 'git' -Arguments @('push', 'origin', $targetBranch)
                    if ($pushResult.ExitCode -ne 0) {
                        Write-WarningMessage "  ✗ Failed to push updates back to origin for branch '$targetBranch'."
                        Write-WarningMessage "    Command: git push origin $targetBranch"
                        Write-WarningMessage "    Exit Code: $($pushResult.ExitCode)"
                        Write-WarningMessage "    Full Output:"
                        foreach ($line in $pushResult.Output) {
                            if (-not [string]::IsNullOrWhiteSpace($line)) {
                                Write-WarningMessage "      $line"
                            }
                        }
                        $upstreamUpdated = $false
                    } else {
                        Write-Success "  ✓ Pushed fork updates to origin/$targetBranch."
                    }
                }
            } finally {
                Invoke-ExternalCommand -Tool 'git' -Arguments @('remote', 'remove', $tempRemoteName) | Out-Null
            }

            if (-not $upstreamUpdated) {
                Write-WarningMessage "  ⊘ Fork update skipped for '$submodule'."
            }
        } else {
            if (-not $forkInfo.IsFork) {
                Write-Info "  ⊘ Not a fork (upstream sync not applicable)."
            }
        }

        $updatedCount++
    } catch {
        Write-ErrorMessage "  ✗ FAILED: Unexpected error while updating '$submodule'"
        Write-ErrorMessage "    Error: $($_.Exception.Message)"
        Write-ErrorMessage "    Stack Trace: $($_.StackTrace)"
        $failedCount++
    } finally {
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
