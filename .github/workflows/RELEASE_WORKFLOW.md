# Automated Release Workflow

## Overview

The release workflow has been streamlined to require minimal manual intervention. You only need to create a pre-release on GitHub, and the workflow handles everything else automatically.

## Workflow for Each Tool

The following tools have automated release workflows:

- **HolocronToolset** (`*toolset*` tags)
- **KotorDiff** (`*kotordiff*` tags)
- **HoloPatcher** (`*patcher*` or `*holopatcher*` tags)
- **GuiConverter** (`*guiconverter*` tags)
- **Translator** (`*translator*` tags)

## Testing Before Production Release

⚠️ **IMPORTANT**: Before using production workflows, test them safely!

See [QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md) for complete testing instructions.

**Quick test command**:

```bash
# Create test release (uses test-release branch, never touches master)
git tag test-v3.1.99-toolset
git push origin test-v3.1.99-toolset
gh release create test-v3.1.99-toolset --prerelease --title "TEST" --notes "Testing"

# Cleanup after test
gh release delete test-v3.1.99-toolset --yes
git push origin --delete test-v3.1.99-toolset
```

Test workflows are available:

- `TEST_release_toolset.yml` - Tests toolset release process
- Use `create_test_workflow.ps1` to generate test workflows for other tools

## How to Release (Streamlined Process)

### Step 1: Create a Pre-Release on GitHub

1. Go to your repository on GitHub
2. Click on "Releases" → "Draft a new release"
3. Create a tag following the pattern: `vMAJOR.MINOR.PATCH-<tool>`
   - For Toolset: `v3.1.3-toolset`
   - For KotorDiff: `v1.0.1-kotordiff`
   - For HoloPatcher: `v1.7.1-patcher` or `v1.7.1-holopatcher`
   - For GuiConverter: `v1.0.0-guiconverter`
   - For Translator: `v1.0.0-translator`
4. Add release notes in the description (optional but recommended)
5. **Check "Set as a pre-release"**
6. Click "Publish release"

### Step 2: Wait for Automation

The workflow will automatically:

1. **Validate** that the tag matches the tool pattern
2. **Extract** the version from the tag (e.g., `v3.1.3-toolset` → `3.1.3`)
3. **Update version (pre-build)**:
   - Updates `currentVersion` in config files
   - Commits to master
   - Updates release tag to point to the new commit
   - This ensures binaries are built with the correct version
4. **Build** binaries for all platforms (Windows x86/x64, Linux x64, macOS x64)
5. **Upload** compiled artifacts to the release
6. **Update version (post-upload)**:
   - Toolset: Updates `toolsetLatestVersion` and `toolsetLatestBetaVersion`
   - HoloPatcher: Updates `holopatcherLatestVersion` and `holopatcherLatestBetaVersion`
   - Commits to master
   - Updates release tag to point to the new commit
   - This triggers release source archive regeneration
7. **Convert** the pre-release to a full release automatically

### Step 3: Done

No further action needed. The release is now live with all artifacts uploaded and version files updated.

## What Changed from the Old Workflow

### Old Workflow (Manual)

1. ❌ Manually bump `currentVersion` in config.py
2. ❌ Create a new branch for the release
3. ❌ Create the release with tag as pre-release
4. ❌ Wait for workflows to run
5. ❌ Manually bump `toolsetLatestVersion`/`toolsetLatestBetaVersion`
6. ❌ Manually update release notes
7. ❌ Manually convert pre-release to full release

### New Workflow (Automated)

1. ✅ Create pre-release with tag → **Everything else is automatic**

## Workflow Triggers

Each workflow triggers on:

```yaml
on:
  release:
    types: [prereleased]
  workflow_dispatch:
```

- **`prereleased`**: Triggers when you create a pre-release on GitHub
- **`workflow_dispatch`**: Allows manual triggering from Actions tab (for testing)

## Tag Validation

Each workflow validates that the tag matches its pattern:

```bash
# Example for toolset
TAG="${{ github.event.release.tag_name }}"
if [[ "$TAG" == *"toolset"* ]]; then
  # Proceed with workflow
else
  # Skip workflow
fi
```

This ensures that creating a `v3.1.3-toolset` release won't trigger the KotorDiff workflow.

## Version Extraction

Version is extracted from the tag automatically:

- `v3.1.3-toolset` → `3.1.3`
- `v1.0.0-kotordiff` → `1.0.0`
- `v1.7.1-holopatcher` → `1.7.1`

The workflow uses `sed` to strip the `v` prefix and tool suffix.

## Version File Updates

### HolocronToolset

Updates `Tools/HolocronToolset/src/toolset/config.py`:

```python
LOCAL_PROGRAM_INFO: dict[str, Any] = {
    "currentVersion": "3.1.3",  # ← Updated
    "toolsetLatestVersion": "3.1.2",
    "toolsetLatestBetaVersion": "3.1.3",  # ← Updated
    # ... other fields ...
    "toolsetLatestNotes": "Your release notes",  # ← Updated
    "toolsetLatestBetaNotes": "Your release notes",  # ← Updated
}
```

### KotorDiff

Updates `Tools/KotorDiff/src/kotordiff/__main__.py`:

```python
CURRENT_VERSION = "1.0.1"  # ← Updated
```

### HoloPatcher

Updates `Tools/HoloPatcher/src/holopatcher/config.py`:

```python
LOCAL_PROGRAM_INFO: dict[str, Any] = {
    "currentVersion": "1.7.1",  # ← Updated
    "holopatcherLatestVersion": "1.7.0",
    "holopatcherLatestBetaVersion": "1.7.1",  # ← Updated
    # ... other fields ...
    "holopatcherLatestNotes": "Your release notes",  # ← Updated
    "holopatcherLatestBetaNotes": "Your release notes",  # ← Updated
}
```

## Workflow Jobs

Each workflow consists of 6 jobs:

### 1. `validate`

- Checks if the tag matches the tool pattern
- Extracts version from tag
- Outputs `should_run`, `version`, and `tag_name` for subsequent jobs

### 2. `update_version_pre_build`

- **First version update** (before build)
- Checks out master branch
- Updates `currentVersion` in config files
- Commits to master
- Force-updates release tag to point to this commit
- **Purpose**: Ensures binaries are built with correct version

### 3. `setup`

- Sets up the build matrix (OS, Python versions, architectures)
- Only runs if validation passes

### 4. `build`

- Builds binaries for all platform combinations
- Uses the updated version from pre-build step
- Uploads artifacts
- Only runs if validation passes

### 5. `package`

- Downloads all build artifacts
- Compresses into release archives
- Uploads to the GitHub release
- Only runs if validation passes

### 6. `finalize`

- **Second version update** (after upload)
- Checks out master branch
- Updates `toolsetLatestVersion`/`toolsetLatestBetaVersion` (Toolset)
- Updates `holopatcherLatestVersion`/`holopatcherLatestBetaVersion` (HoloPatcher)
- Updates release notes
- Commits to master
- Force-updates release tag to point to this commit
- **Triggers GitHub to regenerate source archives**
- Converts pre-release to full release via GitHub API
- Only runs if all previous jobs succeeded

## Pre-Release to Release Conversion

The workflow uses the GitHub API to convert the pre-release:

```bash
curl -X PATCH \
  -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/${{ github.repository }}/releases/$RELEASE_ID" \
  -d '{"prerelease": false}'
```

This happens automatically after all artifacts are uploaded and version files are updated.

## Manual Workflow Dispatch

You can also trigger workflows manually from the GitHub Actions tab:

1. Go to Actions → Select the workflow
2. Click "Run workflow"
3. Select the branch
4. Click "Run workflow"

Note: For manual dispatch, you'll need to ensure a matching tag exists.

## Troubleshooting

### Workflow doesn't trigger

- Ensure you created a **pre-release** (not a full release)
- Check that the tag matches the pattern (e.g., contains `toolset`)
- Verify the workflow file exists in `.github/workflows/`

### Build fails

- Check the Actions tab for detailed logs
- Common issues: dependency installation, PyInstaller errors
- The workflow will attempt fallback upload if the primary method fails

### Version not updated

- Check that the version file path is correct
- Verify the workflow has write permissions (`permissions: contents: write`)
- Check Git configuration in the finalize job

### Release not converting to full release

- Check that all previous jobs succeeded
- Verify the GitHub API call in the finalize job logs
- Ensure the GITHUB_TOKEN has sufficient permissions

## Best Practices

1. **Use semantic versioning**: `MAJOR.MINOR.PATCH`
2. **Add release notes**: They'll be automatically added to config files
3. **Test on a fork first**: Before using in production
4. **Monitor the Actions tab**: Watch for any failures
5. **Keep tag patterns consistent**: Don't mix naming conventions

## Example Release Timeline

```
00:00 - You create pre-release v3.1.3-toolset
00:01 - Validate job runs (extracts version: 3.1.3)
00:02 - Update_version_pre_build job runs:
        - Updates currentVersion to 3.1.3
        - Commits to master
        - Updates tag to point to new commit
00:03 - Setup job runs (configures build matrix)
00:04 - Build jobs start (6 parallel jobs: 3 OS × 2 architectures)
        - Binaries now contain version 3.1.3
00:16 - Build jobs complete
00:17 - Package job runs (compresses and uploads artifacts)
00:19 - Finalize job runs:
        - Updates toolsetLatestVersion to 3.1.3
        - Updates toolsetLatestBetaVersion to 3.1.3
        - Updates release notes
        - Commits to master
        - Updates tag to point to new commit
        - GitHub regenerates source archives
        - Converts pre-release to full release
00:20 - ✅ Release is now live with all artifacts and updated source!
```

## Migration from Old Workflow

No action needed on your part! The old manual steps are now automated:

| Old Manual Step | New Automated Step |
|-----------------|-------------------|
| Bump currentVersion | Finalize job updates automatically |
| Create release branch | Not needed (commits directly to tag) |
| Create pre-release | You still do this (only manual step) |
| Wait for workflows | Workflows trigger automatically |
| Bump toolsetLatestVersion | Finalize job updates automatically |
| Convert to full release | Finalize job does this via API |

## Two-Stage Version Update Strategy

The workflow uses a **two-stage update** approach:

### Stage 1: Pre-Build (update_version_pre_build job)

**Updates**: `currentVersion`

**Purpose**: Ensures the built binaries report the correct version

**Pushes to**:

- ✅ master branch
- ✅ Release tag (force-updated to master)

### Stage 2: Post-Upload (finalize job)

**Updates**: `toolsetLatestVersion`, `toolsetLatestBetaVersion`, release notes

**Purpose**: Activates auto-update functionality in the application

**Pushes to**:

- ✅ master branch
- ✅ Release tag (force-updated to master)
- ✅ Triggers GitHub to regenerate source archives

**Why two stages?**

- Stage 1 ensures binaries contain correct version strings
- Stage 2 updates auto-update metadata only after artifacts are confirmed uploaded
- Both stages push to master to keep it synchronized
- Release tag is force-updated twice to include all changes in source archives

## Additional Notes

- The workflow commits to **both master and the release tag**
- Version files are updated in **two stages** (pre-build and post-upload)
- If any job fails, the finalize job won't run (release stays as pre-release)
- You can still manually edit releases if needed
- The workflow respects the tag pattern to avoid cross-triggering
- Source archives are automatically regenerated when the tag is updated
- The tag always points to the same commit as master after finalize completes
