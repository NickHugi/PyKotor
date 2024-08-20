#!/usr/bin/env pwsh
Set-Location -Path $PSScriptRoot

$sevenZipPath = "C:\Program Files\7-Zip\7z.exe"  # Path to 7zip executable
$gitBashLocation = "C:\Program Files\Git\bin\bash.exe"
$sourceFolderStrPath = "..$([System.IO.Path]::DirectorySeparatorChar)dist"
$sourceFolder = Get-ChildItem -LiteralPath $sourceFolderStrPath

trap {
    Write-Host -ForegroundColor Red "$($_.InvocationInfo.PositionMessage)`n$($_.Exception.Message)"
    Write-Host "Press any key to continue regardless..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    continue
}

function Convert-WindowsPathToWSL {
    param(
        [string]$path
    )
    $unixPath = $path -replace '\\', '/' -replace ' ', '\ '
    if ($null -ne (Get-Command "wsl" -ErrorAction SilentlyContinue)) {
        $unixPath = $unixPath -replace 'C:', '/mnt/c'
    } else {
        $unixPath = $unixPath -replace 'C:', '/c'  # git bash
    }
    return $unixPath
}

function Initialize-MacOSAppBundle {
    param(
        [string]$path
    )
    $appFolder = Join-Path -Path $path -ChildPath "HoloPatcher.app"
    $contentsFolder = Join-Path -Path $appFolder -ChildPath "Contents"
    $macOSFolder = Join-Path -Path $contentsFolder -ChildPath "MacOS"

    New-Item -Path $macOSFolder -ItemType Directory -Force > $null

    Get-ChildItem -LiteralPath $path | Where-Object { $_.FullName -ne $appFolder } | ForEach-Object {
        Move-Item -LiteralPath $_.FullName -Destination $macOSFolder
    }

    $oldResourcesFolder = Join-Path -Path $macOSFolder -ChildPath "Resources"
    Move-Item -LiteralPath $oldResourcesFolder -Destination $appFolder

    Copy-Item -LiteralPath "./Info.plist" -Destination $contentsFolder

    return $appFolder
}

function Set-UnixFilePermissions {
    param(
        [string]$path,
        [string]$permissions
    )
    $unixArchiveSource = Convert-WindowsPathToWSL -path $path
    if ($null -ne (Get-Command "wsl" -ErrorAction SilentlyContinue)) {
        $command = "& wsl chmod $permissions -Rc $unixArchiveSource"
        Write-Host $command
        Invoke-Expression $command
    } elseif ($null -ne (Get-Command "chmod" -ErrorAction SilentlyContinue)) {
        $command = "& chmod $permissions -Rc '$path'"
        Write-Host $command
        Invoke-Expression $command
    } else {
        $command = "& `"$gitBashLocation`" -c 'find $unixArchiveSource -type d -exec chmod $permissions {} \;'"
        Write-Host $command
        Invoke-Expression $command
        $command = "& `"$gitBashLocation`" -c 'find $unixArchiveSource -type f -exec chmod $permissions {} \;'"
        Write-Host $command
        Invoke-Expression $command
    }
}

function Compress-TarGz {
    param(
        [string]$archiveFile,
        [string]$archiveSource
    )
    $unixArchivePath = Convert-WindowsPathToWSL -path $archiveFile
    $unixArchiveSource = Convert-WindowsPathToWSL -path $archiveSource
    $folderName = [System.IO.Path]::GetFileName($archiveSource)
    $parentDir = [System.IO.Path]::GetDirectoryName($archiveSource)
    $unixParentDir = Convert-WindowsPathToWSL -path $parentDir
    if ($null -ne (Get-Command "wsl" -ErrorAction SilentlyContinue)) {
        $command = "& wsl tar -czvf $unixArchivePath -C $unixParentDir '$folderName'"
        Write-Host $command
        Invoke-Expression $command
    } elseif ($null -ne (Get-Command "tar" -ErrorAction SilentlyContinue)) {
        $command = "& tar -czvf $archivePath -C $parentDir '$folderName'"
        Write-Host $command
        Invoke-Expression $command
    } elseif ($null -ne (Get-Command "7z" -ErrorAction SilentlyContinue)) {
        $tarArchive = $archiveFile -replace '\.gz$', ''
        & '7z' a -ttar -mx=9 $tarArchive $archiveSource
        & '7z' a -tgzip -mx=9 $archiveFile $tarArchive
        Remove-Item -Path $tarArchive
    } elseif (Test-Path -Path $sevenZipPath) {
        $tarArchive = $archiveFile -replace '\.gz$', ''
        & $sevenZipPath a -ttar -mx=9 $tarArchive $archiveSource
        & $sevenZipPath a -tgzip -mx=9 $archiveFile $tarArchive
        Remove-Item -Path $tarArchive
    } elseif (Test-Path -Path $gitBashLocation) {
        $command = "& `"$gitBashLocation`" -c 'tar czf $unixArchivePath $unixArchiveSource'"
        Write-Host $command
        Invoke-Expression $command
    } else {
        Write-Error "No available method for archive creation found."
        return
    }
}

function Compress-Zip {
    param(
        [string]$archiveFile,
        [string]$archiveSource
    )
    if ($null -ne (Get-Command "wsl" -ErrorAction SilentlyContinue)) {
        $parentDir = [System.IO.Path]::GetDirectoryName($archiveSource)
        $originalDir = Get-Location
        $unixArchivePath = Convert-WindowsPathToWSL -path $archiveFile
        $command = "cd '$parentDir'; & wsl zip -q -r -9 '$unixArchivePath' '$([System.IO.Path]::GetFileName($archiveSource))'; cd '$originalDir'"
        Write-Host $command
        Invoke-Expression $command
    } elseif ($null -ne (Get-Command "zip" -ErrorAction SilentlyContinue)) {
        $parentDir = [System.IO.Path]::GetDirectoryName($archiveSource)
        $originalDir = Get-Location
        $archiveFile = [System.IO.Path]::GetFullPath((Join-Path $originalDir $archiveFile))
        $command = "cd '$parentDir'; & zip -q -r -9 '$archiveFile' '$([System.IO.Path]::GetFileName($archiveSource))'; cd '$originalDir'"
        Write-Host $command
        Invoke-Expression $command
    } elseif ($null -ne (Get-Command "7z" -ErrorAction SilentlyContinue)) {
        $command = "& '7z' a -tzip -mx=9 `"$archiveFile`" `"$archiveSource`""
        Write-Host $command
        Invoke-Expression $command
    } elseif (Test-Path -Path $sevenZipPath) {
        $command = "& `"$sevenZipPath`" a -tzip -mx=9 `"$archiveFile`" `"$archiveSource`""
        Write-Host $command
        Invoke-Expression $command
    } else {
        $parentDir = Split-Path -Parent $archiveSource
        $newParentFolder = Join-Path $parentDir ("TempParent_" + (Get-Date).Ticks)
        New-Item -Path $newParentFolder -ItemType Directory -Force
        Move-Item -Path $archiveSource -Destination $newParentFolder
        Compress-Archive -Path "$newParentFolder\*" -DestinationPath $archiveFile -Force
        Remove-Item -Path $newParentFolder -Recurse -Force
    }
}


try {
    
    New-Item -Name "publish" -ItemType Directory -ErrorAction SilentlyContinue
    $publishDir = Resolve-Path -LiteralPath "./publish"
    foreach ($item in $sourceFolder) {
        $fileExtension = $item.Extension
        if (($fileExtension.ToLower() -eq ".zip") -or ($fileExtension.ToLower() -eq ".tar.gz")) {
            Write-Host "Skipping prepackaged $($item.Name)"
            continue
        }
        Write-Host ""
        Write-Host "Zipping '$item' for release..."
        Write-Host "Source path: '$($item.FullName)'"

        # Fix file permissions before archiving
        Set-UnixFilePermissions -path $item.FullName -permissions "777"
        $baseName = $item.BaseName
        $index = $baseName.ToLower().IndexOf(".app")
        if ($index -ge 0) {
            $baseName = $baseName.Substring(0, $index) + $baseName.Substring($index + 4)
        }
        if ($fileExtension.ToLower() -eq ".app") {
            $suffix = "_Mac"
        } elseif ($fileExtension.ToLower() -eq ".exe") {
            $suffix = "_Windows"
        } else {
            $suffix = "_Unix"
        }

        # Determine compression method
        if ($null -ne (Get-Command "wsl" -ErrorAction SilentlyContinue)) {
            $destinationPath = Join-Path -Path $publishDir -ChildPath "$baseName$suffix.zip"
            Write-Host "Destination path: '$destinationPath'"
            Compress-Zip -archiveFile $destinationPath -archiveSource $item.FullName
        } else {
            Write-Warning "Creating .tar.gz instead of .zip archives to preserve file attributes, please run on unix or wsl if you want zips."
            $destinationPath = Join-Path -Path $publishDir -ChildPath "$baseName$suffix.tar.gz"
            Write-Host "Destination path: '$destinationPath'"
            Compress-TarGz -archiveFile $destinationPath -archiveSource $item.FullName
        }

        Write-Host "Publishing '$item' to '$destinationPath' completed."
    }

    Write-Host "Zipped all dists successfully."
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} catch {
    Write-Host -ForegroundColor Red "$($_.InvocationInfo.PositionMessage)`n$($_.Exception.Message)"
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    continue
}
