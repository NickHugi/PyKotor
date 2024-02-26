$branchName = "test-status-badge"
$repository_owner = "th3w1zard1"
$repository_name = "PyKotor"

$uniqueTempBranchName = "temp-branch"

git fetch
git checkout -b $uniqueTempBranchName

$testsResultsPath = "tests/results"
Remove-Item -Path $testsResultsPath -Recurse -Force
New-Item -ItemType Directory -Force -Path $testsResultsPath

$OS_NAMES = @("windows-2019", "ubuntu-20.04", "macos-12")
$PYTHON_VERSIONS = @('3.7', '3.8', '3.9', '3.10', '3.11', '3.12', '3.13.0-alpha.4')
$ARCHITECTURES = @('x86', 'x64')

$extractedReportsPath = "tests/results"
New-Item -ItemType Directory -Force -Path $extractedReportsPath

Get-ChildItem "./all_pytest_reports" -Filter *.zip | ForEach-Object {
    Expand-Archive -Path $_.FullName -DestinationPath $(Join-Path -Path $extractedReportsPath -ChildPath $_.BaseName) -Force
}

git add -A
git commit -am "Upload test results"

$commitSHA = git rev-parse HEAD

$testResults = @{}

Get-ChildItem $extractedReportsPath -Recurse -Filter pytest_report.xml | ForEach-Object {
    [xml]$TestResultsXml = Get-Content $_.FullName
    $totalTests = [int]$TestResultsXml.testsuites.testsuite.tests
    $failedTests = [int]$TestResultsXml.testsuites.testsuite.failures
    $errors = [int]$TestResultsXml.testsuites.testsuite.errors

    $passedTests = $totalTests - $failedTests - $errors

    $resultFilePathHtml = $_.FullName -replace '\.xml$', '.html'
    $DetailsURL = "https://github.com/$repository_owner/$repository_name/blob/$commitSHA/$resultFilePathHtml"
    $key = $_.Directory.Name.Replace('pytest_report_', '').Replace('_', '-')

    $testResults[$key] = @{
        Passed = $passedTests
        Failed = $failedTests + $errors
        Total  = $totalTests
        DetailsURL = $DetailsURL
    }
}

$ReadmePath = "./README.md"
$ReadmeContent = Get-Content $ReadmePath -Raw

$WindowsBadgeContent = ""
$LinuxBadgeContent = ""
$MacOSBadgeContent = ""

$windowsBadgesStartPlaceholder = "<!-- WINDOWS-BADGES-START -->"
$windowsBadgesEndPlaceholder = "<!-- WINDOWS-BADGES-END -->"
$linuxBadgesStartPlaceholder = "<!-- LINUX-BADGES-START -->"
$linuxBadgesEndPlaceholder = "<!-- LINUX-BADGES-END -->"
$macosBadgesStartPlaceholder = "<!-- MACOS-BADGES-START -->"
$macosBadgesEndPlaceholder = "<!-- MACOS-BADGES-END -->"

function Replace-BadgeContent {
    param (
        [string]$readmeContent,
        [string]$badgeContent,
        [string]$startPlaceholder,
        [string]$endPlaceholder
    )

    $pattern = [regex]::Escape($startPlaceholder) + "(.|\n)*?" + [regex]::Escape($endPlaceholder)
    $replacement = $startPlaceholder + "`n" + $badgeContent + "`n" + $endPlaceholder
    return $readmeContent -replace $pattern, $replacement
}

foreach ($OS in $OS_NAMES) {
    foreach ($PYTHON_VERSION in $PYTHON_VERSIONS) {
        foreach ($ARCH in $ARCHITECTURES) {
        $key = "$OS-$PYTHON_VERSION-$ARCH"
        if ($testResults.ContainsKey($key)) {
            $passedTests = $testResults[$key]['Passed']
            $failedTests = $testResults[$key]['Failed']
            $DetailsURL = $testResults[$key]['DetailsURL']
            # Encode the label to replace spaces with underscores and URI-encode other special characters
            $encodedKey = [System.Web.HttpUtility]::UrlEncode($key.Replace(' ', '_').Replace('-', '--'))
            $BadgeURLPassed = "https://img.shields.io/badge/${encodedKey}_Passed-${passedTests}-brightgreen"
            $BadgeURLFailed = "https://img.shields.io/badge/${encodedKey}_Failed-${failedTests}-red"
            $BadgeMarkdown = "[![$key-Passing]($BadgeURLPassed)]($DetailsURL) [![$key-Failing]($BadgeURLFailed)]($DetailsURL)"

        } else {
            Write-Host "No test results for $key, must have failed, generating 'Build Failed' badge..."
            $encodedKey = [System.Web.HttpUtility]::UrlEncode($key.Replace(' ', '_').Replace('-', '--'))
            $BadgeURLBuildFailed = "https://img.shields.io/badge/${encodedKey}_Build_Failed-lightgrey"
            $DetailsURL = "https://github.com/$repository_owner/$repository_name/blob/$commitSHA/$testsResultsPath/$key-Build_Failed.xml"
            $BadgeMarkdown = "[![$key-Build_Failed]($BadgeURLBuildFailed)]($DetailsURL)"
        }

            switch ($OS) {
                "windows-2019" { $WindowsBadgeContent += $BadgeMarkdown + " " }
                "ubuntu-20.04" { $LinuxBadgeContent += $BadgeMarkdown + " " }
                "macos-12" { $MacOSBadgeContent += $BadgeMarkdown + " " }
            }
        }
    }
}

$ReadmeContent = Replace-BadgeContent -readmeContent $ReadmeContent -badgeContent $WindowsBadgeContent.TrimEnd() -startPlaceholder $windowsBadgesStartPlaceholder -endPlaceholder $windowsBadgesEndPlaceholder
$ReadmeContent = Replace-BadgeContent -readmeContent $ReadmeContent -badgeContent $LinuxBadgeContent.TrimEnd() -startPlaceholder $linuxBadgesStartPlaceholder -endPlaceholder $linuxBadgesEndPlaceholder
$ReadmeContent = Replace-BadgeContent -readmeContent $ReadmeContent -badgeContent $MacOSBadgeContent.TrimEnd() -startPlaceholder $macosBadgesStartPlaceholder -endPlaceholder $macosBadgesEndPlaceholder

Set-Content -Path $ReadmePath -Value $ReadmeContent

git commit -am "Update README with custom test status badges"
git checkout $branchName
git merge --no-ff $uniqueTempBranchName
git branch -d $uniqueTempBranchName
git push origin $branchName