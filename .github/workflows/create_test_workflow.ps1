# Script to create TEST workflow from production workflow
# Usage: .\create_test_workflow.ps1 -ToolName "kotordiff"

param(
    [Parameter(Mandatory=$true)]
    [string]$ToolName
)

$ProductionFile = "release_${ToolName}.yml"
$TestFile = "TEST_release_${ToolName}.yml"

if (-not (Test-Path $ProductionFile)) {
    Write-Error "Production workflow file not found: $ProductionFile"
    exit 1
}

Write-Host "Creating TEST workflow from $ProductionFile → $TestFile"

# Read production workflow
$content = Get-Content $ProductionFile -Raw

# Replace name
$content = $content -replace "^name: (.+) Release$", 'name: $1 Release (TEST)' -replace "`r`n", "`n"

# Replace tag pattern in validate job
$content = $content -replace "if \[\[ `"\`$TAG`" == \*`"$ToolName`"\* \]\]; then", "if [[ `"`$TAG`" == test-*$ToolName* ]]; then"

# Replace tag pattern comment
$content = $content -replace "# For manual dispatch, find the most recent $ToolName tag", "# For manual dispatch, find the most recent test $ToolName tag"
$content = $content -replace "\`$\(git tag --list '\*$ToolName\*'", "`$(git tag --list 'test-*$ToolName*'"

# Replace version extraction to handle test- prefix
$content = $content -replace "VERSION=\`$\(echo `"\`$TAG`" \| sed 's/\^v//'", "VERSION=`$(echo `"`$TAG`" | sed 's/^test-v//' | sed 's/^test-//' | sed 's/^v//'"

# Replace master with test-release in update_version_pre_build
$content = $content -replace "ref: master`n", "ref: test-release`n"

# Add test-release branch creation step
$createBranchStep = @"

      - name: Create or update test-release branch
        run: |
          # Create test-release branch from current checkout if it doesn't exist
          git fetch origin
          if git rev-parse --verify origin/test-release >/dev/null 2>&1; then
            echo "Using existing test-release branch"
            git checkout test-release
            git merge origin/master --no-edit
          else
            echo "Creating new test-release branch"
            git checkout -b test-release
          fi
        shell: bash
"@

$content = $content -replace "(- name: Configure Git`n.*?`n.*?`n)", "`$1$createBranchStep`n"

# Replace master pushes with test-release
$content = $content -replace "git push origin master", "git push origin test-release"
$content = $content -replace "echo `"Updating .+ (pre-build|post-upload)`"`n", "echo `"⚠️  TEST MODE: Updating on test-release branch`"`n          echo `"⚠️  This will NOT affect master or production auto-updates`"`n          echo `"Updating `$CONFIG_FILE (pre-build|post-upload)`"`n"

# Add [TEST] prefix to commit messages
$content = $content -replace 'git commit -m "chore:', 'git commit -m "chore: [TEST]'

# Replace artifact retention
$content = $content -replace "retention-days: 90", "retention-days: 7  # Shorter retention for test builds"

# Add TEST suffix to artifact names
$content = $content -replace "name: (.+?)`_\`$\{\{ runner.os \}\}", 'name: $1_TEST_${{ runner.os }}'

# Replace finalize checkout to use test-release
$content = $content -replace "ref: master`n          token:", "ref: test-release`n          token:"

# Replace the final "Convert pre-release to full release" step
$finalizeStep = @"
      - name: Add TEST warning to release description
        run: |
          TAG="`${{ needs.validate.outputs.tag_name }}"
          
          # Get the release
          RELEASE_JSON=`$(curl -s -H "Authorization: token `${{ secrets.GITHUB_TOKEN }}" \
            "https://api.github.com/repos/`${{ github.repository }}/releases/tags/`$TAG")
          RELEASE_ID=`$(echo "`$RELEASE_JSON" | jq -r '.id')
          CURRENT_BODY=`$(echo "`$RELEASE_JSON" | jq -r '.body')
          
          # Prepend warning to body
          NEW_BODY="⚠️ **THIS IS A TEST RELEASE** ⚠️

This release was created using the TEST workflow and should not be used in production.
- Version updates are on test-release branch only
- Master branch is NOT modified
- Auto-update will NOT be triggered for end users

---

`$CURRENT_BODY"
          
          # Update release body
          ESCAPED_BODY=`$(echo "`$NEW_BODY" | jq -Rs .)
          curl -X PATCH \
            -H "Authorization: token `${{ secrets.GITHUB_TOKEN }}" \
            -H "Accept: application/vnd.github.v3+json" \
            "https://api.github.com/repos/`${{ github.repository }}/releases/`$RELEASE_ID" \
            -d "{\"body\": `$ESCAPED_BODY}"
          
          echo "Added TEST warning to release description"
        shell: bash

      - name: Leave as pre-release (DO NOT convert to full release in TEST mode)
        run: |
          echo "⚠️  TEST MODE: Keeping release as pre-release"
          echo "⚠️  Delete this release and tag when done testing"
          echo "⚠️  Run 'git branch -D test-release && git push origin --delete test-release' to cleanup"
        shell: bash
"@

$content = $content -replace "      - name: Convert pre-release to full release[\s\S]+?shell: bash", $finalizeStep

# Write test workflow
$content | Out-File -FilePath $TestFile -Encoding UTF8 -NoNewline

Write-Host "✅ Created $TestFile"
Write-Host ""
Write-Host "To test:"
Write-Host "  1. git tag test-v3.1.3-$ToolName"
Write-Host "  2. git push origin test-v3.1.3-$ToolName"
Write-Host "  3. Create pre-release on GitHub with tag test-v3.1.3-$ToolName"
Write-Host ""
Write-Host "To cleanup:"
Write-Host "  gh release delete test-v3.1.3-$ToolName --yes"
Write-Host "  git push origin --delete test-v3.1.3-$ToolName"
Write-Host "  git push origin --delete test-release"

