# Testing Release Workflows

## Overview

This guide explains how to test the automated release workflows **without** affecting production or triggering auto-updates for your end users.

## Test Workflows Available

- `TEST_release_toolset.yml` - Test workflow for HolocronToolset
- (More can be created following the same pattern)

## Key Differences: Production vs Test

| Aspect | Production Workflow | Test Workflow |
|--------|-------------------|---------------|
| **Tag Pattern** | `v3.1.3-toolset` | `test-v3.1.3-toolset` |
| **Trigger** | `prereleased` | `prereleased` |
| **Branch Modified** | `master` | `test-release` |
| **Auto-Update Triggered** | ✅ Yes | ❌ No (test branch only) |
| **Converts to Full Release** | ✅ Yes | ❌ No (stays pre-release) |
| **Artifact Retention** | 90 days | 7 days |
| **Release Notes** | As provided | Prefixed with ⚠️ WARNING |

## How to Test a Release Workflow

### Step 1: Create Test Release

1. Go to your repository on GitHub
2. Click "Releases" → "Draft a new release"
3. **Use test tag pattern**: `test-v3.1.3-toolset`
   - Note the `test-` prefix
   - Use a version number that doesn't conflict with real releases
4. Add test release notes
5. **Check "Set as a pre-release"**
6. Click "Publish release"

### Step 2: Watch the Workflow

1. Go to the **Actions** tab
2. Find the running "Toolset Release (TEST)" workflow
3. Monitor each job:
   - ✅ `validate` - Should pass and extract version
   - ✅ `update_version_pre_build` - Creates/updates test-release branch
   - ✅ `setup` - Configures matrix
   - ✅ `build` - Builds binaries (this takes 10-15 min)
   - ✅ `package` - Uploads artifacts to release
   - ✅ `finalize` - Updates test-release branch, adds warning to description

### Step 3: Verify Results

Check that:

1. **test-release branch exists** with updated `currentVersion`
2. **Release has artifacts** uploaded (Windows/Linux/macOS builds)
3. **Release description** has TEST warning prepended
4. **Release is still pre-release** (NOT converted to full)
5. **master branch is unchanged** (no commits from this test)

```bash
# Check test-release branch
git fetch origin test-release
git log origin/test-release -n 3 --oneline

# Verify master is unchanged
git log origin/master -n 3 --oneline
```

### Step 4: Cleanup After Testing

```bash
# Delete the test release on GitHub (via web UI or gh CLI)
gh release delete test-v3.1.3-toolset --yes

# Delete the test tag
git push origin --delete test-v3.1.3-toolset

# Delete the test-release branch (optional, can reuse for next test)
git push origin --delete test-release
git branch -D test-release
```

## What Gets Tested

The test workflow validates:

- ✅ Tag pattern matching and validation
- ✅ Version extraction from tags
- ✅ Two-stage version update process
- ✅ Building binaries with correct version
- ✅ Artifact compression and upload
- ✅ Config file updates (on test branch)
- ✅ Git operations (commit, push, tag force-update)
- ✅ Release source archive regeneration
- ❌ Does NOT test: Converting to full release (stays pre-release)
- ❌ Does NOT test: Auto-update triggering (test branch not monitored)

## Safety Features

### 1. Separate Branch

All updates go to `test-release` branch, never `master`:

```bash
# Test workflow creates/uses test-release
git checkout -b test-release  # Created if doesn't exist
# ... makes changes ...
git push origin test-release  # Never touches master
```

### 2. Test Tag Pattern

Only tags starting with `test-` trigger test workflows:

```bash
# Production: v3.1.3-toolset
if [[ "$TAG" == *"toolset"* ]]; then  # ✅ Matches

# Test: test-v3.1.3-toolset
if [[ "$TAG" == test-*toolset* ]]; then  # ✅ Matches test workflow only
```

### 3. Prefixed Release Notes

Test releases are clearly marked:

```
⚠️ **THIS IS A TEST RELEASE** ⚠️

This release was created using the TEST workflow and should not be used in production.
- Version updates are on test-release branch only
- Master branch is NOT modified
- Auto-update will NOT be triggered for end users

---

[Your original release notes here]
```

### 4. Stays Pre-Release

Test workflow does NOT convert to full release, so:
- Release stays marked as pre-release
- Less likely to confuse users
- Easy to identify as test

## Testing Workflow_Dispatch (Manual Trigger)

You can also test using manual workflow dispatch:

1. Go to Actions → "Toolset Release (TEST)"
2. Click "Run workflow"
3. Select branch: `master`
4. Click "Run workflow"

Note: You must first create a test tag:

```bash
git tag test-v3.1.3-toolset
git push origin test-v3.1.3-toolset

# Create the release manually via web UI or:
gh release create test-v3.1.3-toolset --prerelease --title "Test Release 3.1.3" --notes "Testing workflow"
```

## Verifying Version Updates

### Check test-release Branch

```bash
# Fetch test-release
git fetch origin test-release

# View config.py on test-release
git show origin/test-release:Tools/HolocronToolset/src/toolset/config.py | grep -A 5 "currentVersion"
```

Expected output:
```python
"currentVersion": "3.1.3",  # ← Updated by pre-build
"toolsetLatestVersion": "3.1.1",  # ← Should still be old
"toolsetLatestBetaVersion": "3.1.3",  # ← Updated by finalize
```

### Check master Branch (Should be unchanged)

```bash
git show origin/master:Tools/HolocronToolset/src/toolset/config.py | grep -A 5 "currentVersion"
```

Expected output:
```python
"currentVersion": "3.1.2",  # ← Still old version (untouched)
"toolsetLatestVersion": "3.1.1",  # ← Still old version (untouched)
"toolsetLatestBetaVersion": "3.1.1",  # ← Still old version (untouched)
```

## Testing the Full Production Workflow

Once you've verified the test workflow works correctly:

### Option 1: Test on a Fork

1. Fork your repository
2. Enable Actions on the fork
3. Create a real release (without `test-` prefix) on the fork
4. Watch it run through the full production workflow
5. Verify master is updated correctly
6. Delete the fork when done

### Option 2: Use a Throwaway Version

1. Create a pre-release with a fake version: `v3.1.2.1-toolset`
2. Let it run through the full production workflow
3. Immediately create another release `v3.1.2.2-toolset` to override
4. This minimizes user exposure to the test version

### Option 3: Test in Off-Peak Hours

1. Create a real pre-release during off-peak hours (e.g., 2 AM)
2. If something goes wrong, you can quickly:
   - Delete the release
   - Revert master commits
   - Issue a new release

## Common Test Scenarios

### Scenario 1: Testing Tag Validation

```bash
# Should NOT trigger toolset workflow
gh release create test-v1.0.0-kotordiff --prerelease --notes "Test"

# Should trigger toolset TEST workflow
gh release create test-v3.1.3-toolset --prerelease --notes "Test"
```

### Scenario 2: Testing Version Extraction

```bash
# Different version formats
test-v3.1.3-toolset     → 3.1.3
test-v1.0.0-kotordiff   → 1.0.0
test-v2.5.1-patcher     → 2.5.1
```

### Scenario 3: Testing Build Matrix

The test workflow builds the same matrix as production:
- 3 Operating Systems (Windows, Linux, macOS)
- 2 Architectures (x86, x64)
- 1 Python version (3.8)
- 1 Qt version (PyQt5)

Total: 6 build jobs (3 OS × 2 architectures, excluding x86 on Unix)

### Scenario 4: Testing Failure Handling

Introduce an intentional error to test failure handling:

1. Temporarily modify `compile_toolset.ps1` to fail
2. Create test release
3. Watch build job fail
4. Verify finalize job does NOT run
5. Verify release stays as pre-release
6. Revert the intentional error

## Creating Test Workflows for Other Tools

To create a test workflow for KotorDiff, HoloPatcher, etc.:

1. Copy `TEST_release_toolset.yml` to `TEST_release_kotordiff.yml`
2. Replace all instances of:
   - `toolset` → `kotordiff`
   - `HolocronToolset` → `KotorDiff`
   - `Tools/HolocronToolset/src/toolset/config.py` → `Tools/KotorDiff/src/kotordiff/__main__.py`
   - `currentVersion` → `CURRENT_VERSION`
   - `toolsetLatestVersion` → (remove, KotorDiff doesn't have this)
3. Adjust the build steps to match the tool's build process

## Troubleshooting Test Workflows

### Test workflow doesn't trigger

- Ensure tag starts with `test-` (e.g., `test-v3.1.3-toolset`)
- Verify it's marked as pre-release
- Check Actions tab for workflow runs

### Build succeeds but version is wrong

- Check test-release branch was created
- Verify pre-build job ran before build
- Check the compiled binary's version string

### test-release branch conflicts

```bash
# Reset test-release to current master
git fetch origin
git checkout test-release
git reset --hard origin/master
git push origin test-release --force
```

### Artifacts not uploading

- Check artifact name pattern in package job
- Verify retention-days is set (7 for test)
- Check upload-artifact step logs

## Quick Reference

### Create Test Release (Toolset)

```bash
git tag test-v3.1.3-toolset
git push origin test-v3.1.3-toolset
gh release create test-v3.1.3-toolset \
  --prerelease \
  --title "TEST: Toolset 3.1.3" \
  --notes "Testing automated release workflow"
```

### Cleanup Test Release

```bash
# Delete release
gh release delete test-v3.1.3-toolset --yes

# Delete tag
git push origin --delete test-v3.1.3-toolset

# Delete test-release branch (optional)
git push origin --delete test-release
```

### Monitor Test Workflow

```bash
# Watch workflow runs
gh run list --workflow="TEST_release_toolset.yml"

# View specific run
gh run view <run-id> --log
```

## Benefits of Test Workflows

1. ✅ **Safe Testing**: No impact on production or end users
2. ✅ **Realistic**: Tests actual build and release process
3. ✅ **Isolated**: Uses separate branch and tag pattern
4. ✅ **Reversible**: Easy cleanup with no lasting effects
5. ✅ **Visible**: Clearly marked as TEST in all outputs

## When to Use Test vs Production

### Use TEST Workflow When:

- First time setting up the automated workflow
- Testing changes to the workflow file
- Validating new version numbering scheme
- Testing after major infrastructure changes
- Training new team members

### Use Production Workflow When:

- Ready to release to end users
- All testing completed successfully
- Version number is finalized
- Release notes are ready
- During regular release cadence

## Notes

- Test workflows use the same build process as production
- The only differences are branch targets and final steps
- You can run multiple test releases in parallel
- Test releases don't count toward GitHub storage limits (7-day retention)
- Always cleanup test releases to avoid confusion

