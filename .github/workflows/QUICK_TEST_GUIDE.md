# Quick Test Guide - Release Workflows

## 🚀 Safe Testing Without Affecting Users

This guide shows you how to test the automated release workflow **without triggering auto-updates** for your end users.

## Method 1: Use TEST Workflow (Recommended)

### ✅ What Makes This Safe

- Uses `test-release` branch (never touches `master`)
- Requires `test-` tag prefix (e.g., `test-v3.1.3-toolset`)
- Does NOT convert to full release (stays pre-release)
- Adds big warning to release description
- Shorter artifact retention (7 days vs 90)

### 📋 Step-by-Step

#### 1. Create Test Release on GitHub

```bash
# On GitHub web UI:
1. Go to Releases → "Draft a new release"
2. Tag: test-v3.1.4-toolset
3. Title: "TEST: Toolset 3.1.4"
4. Description: "Testing automated workflow"
5. ✅ Check "Set as a pre-release"
6. Click "Publish release"
```

Or via CLI:

```bash
git tag test-v3.1.4-toolset
git push origin test-v3.1.4-toolset

gh release create test-v3.1.4-toolset \
  --prerelease \
  --title "TEST: Toolset 3.1.4" \
  --notes "Testing automated release workflow"
```

#### 2. Watch It Run

1. Go to **Actions** tab
2. Find "Toolset Release (TEST)" workflow
3. Watch the jobs execute (~15-20 minutes):
   ```
   ✅ validate (30 sec)
   ✅ update_version_pre_build (1 min)
   ✅ setup (30 sec)
   ✅ build (12-15 min) - 6 parallel jobs
   ✅ package (2-3 min)
   ✅ finalize (1 min)
   ```

#### 3. Verify Results

Check the release page:

- ✅ Has uploaded artifacts (6 .zip files)
- ✅ Has TEST warning in description
- ✅ Still shows as "Pre-release"
- ✅ Source code archives regenerated

Check test-release branch:

```bash
git fetch origin test-release
git show origin/test-release:Tools/HolocronToolset/src/toolset/config.py | grep -C 3 currentVersion
```

Should show:
```python
"currentVersion": "3.1.4",  # ← Updated
"toolsetLatestVersion": "3.1.1",  # ← Old (master unchanged!)
"toolsetLatestBetaVersion": "3.1.4",  # ← Updated
```

Check master is unchanged:

```bash
git show origin/master:Tools/HolocronToolset/src/toolset/config.py | grep currentVersion
# Should still show old version like "3.1.2"
```

#### 4. Cleanup

```bash
# Delete the test release
gh release delete test-v3.1.4-toolset --yes

# Delete the test tag
git push origin --delete test-v3.1.4-toolset

# Optional: Keep test-release branch for next test
# Or delete it:
git push origin --delete test-release
```

### 🎯 What You Verified

By running through this test, you confirmed:

1. ✅ Tag triggers workflow correctly
2. ✅ Version extracted from tag
3. ✅ test-release branch created/updated
4. ✅ currentVersion updated before build
5. ✅ Binaries built with correct version
6. ✅ Artifacts uploaded to release
7. ✅ Latest versions updated after upload
8. ✅ Release source archives regenerated
9. ✅ master branch NOT modified
10. ✅ Auto-update NOT triggered

## Method 2: Fork Testing (Most Realistic)

### 📋 Step-by-Step

#### 1. Create a Fork

```bash
# On GitHub: Click "Fork" button
# Or via CLI:
gh repo fork NickHugi/PyKotor --clone=false
```

#### 2. Enable Actions

1. Go to fork's Settings → Actions
2. Enable "Allow all actions and reusable workflows"

#### 3. Create Real Release on Fork

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/PyKotor.git
cd PyKotor

# Create real release (no test- prefix)
git tag v3.1.4-toolset
git push origin v3.1.4-toolset

gh release create v3.1.4-toolset \
  --prerelease \
  --title "Test Release 3.1.4" \
  --notes "Testing full production workflow on fork"
```

#### 4. Watch Full Production Flow

The workflow will:
- ✅ Update master on YOUR fork
- ✅ Build and upload artifacts
- ✅ Convert to full release
- ✅ Trigger auto-update (but only affects YOUR fork)

#### 5. Verify on Fork

```bash
# Check master was updated
git pull origin master
grep currentVersion Tools/HolocronToolset/src/toolset/config.py

# Check release is now full release (not pre-release)
gh release view v3.1.4-toolset
```

#### 6. Delete Fork

Once verified, delete the fork:
- GitHub Settings → Danger Zone → Delete this repository

### 🎯 What You Verified

This tests the **complete production workflow**:

1. ✅ master branch updates (stage 1)
2. ✅ Builds with correct version
3. ✅ Artifact upload
4. ✅ master branch updates (stage 2)
5. ✅ Release conversion to full release
6. ✅ Source archive regeneration
7. ✅ Auto-update would trigger (on fork only)

## Method 3: Quick Validation (Workflow Syntax Only)

### Test Without Creating Release

#### 1. Use GitHub Actions Linter

```bash
# Install actionlint
# On Windows with Chocolatey:
choco install actionlint

# On macOS:
brew install actionlint

# On Linux:
go install github.com/rhysd/actionlint/cmd/actionlint@latest
```

#### 2. Lint All Workflows

```bash
cd .github/workflows
actionlint *.yml

# Check specific workflow
actionlint release_toolset.yml
```

#### 3. Validate YAML Syntax

```bash
# Using Python
python -c "import yaml; yaml.safe_load(open('release_toolset.yml'))"

# Using PowerShell
Get-Content release_toolset.yml | ConvertFrom-Yaml
```

## Comparison Matrix

| Method | Safety | Realism | Time | Cleanup | Best For |
|--------|--------|---------|------|---------|----------|
| TEST Workflow | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 20 min | Easy | First-time testing |
| Fork Testing | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 25 min | Medium | Full validation |
| Syntax Validation | ⭐⭐⭐⭐⭐ | ⭐ | 1 min | None | Quick checks |

## Recommended Testing Sequence

### First Time Setup

1. **Syntax Validation** (1 min)
   ```bash
   actionlint .github/workflows/release_toolset.yml
   ```

2. **TEST Workflow** (20 min)
   ```bash
   # Create test release with test-v3.1.4-toolset tag
   # Verify test-release branch updated
   # Verify master unchanged
   # Cleanup
   ```

3. **Fork Testing** (25 min)
   ```bash
   # Test full production flow on fork
   # Verify everything works
   # Delete fork
   ```

### Regular Workflow Changes

When you modify a workflow file:

1. **Syntax Validation** (1 min)
2. **TEST Workflow** (20 min)
3. If major changes: **Fork Testing** (25 min)

## Emergency Rollback Plan

If a production release goes wrong:

### If Builds Are Running

```bash
# Cancel the workflow run via Actions tab
# Or:
gh run cancel <run-id>
```

### If Build Completed But Not Finalized

- The release stays as pre-release
- No auto-update triggered yet
- Simply delete the release and tag

### If Finalized Incorrectly

```bash
# 1. Immediately create new release with correct version
git tag v3.1.5-toolset
git push origin v3.1.5-toolset
# Create pre-release on GitHub

# 2. Revert master commits if needed
git revert <commit-sha>
git push origin master

# 3. Delete bad release
gh release delete v3.1.4-toolset --yes
git push origin --delete v3.1.4-toolset
```

## Creating TEST Workflows for Other Tools

Use the provided script:

```powershell
# In .github/workflows directory
.\create_test_workflow.ps1 -ToolName "kotordiff"
.\create_test_workflow.ps1 -ToolName "holopatcher"
.\create_test_workflow.ps1 -ToolName "guiconverter"
.\create_test_workflow.ps1 -ToolName "translator"
```

Or manually follow TEST_release_toolset.yml pattern.

## Tips for Safe Testing

### 1. Use Consistent Test Tags

```bash
# Good (clearly test tags)
test-v3.1.4-toolset
test-v1.0.1-kotordiff
test-v2.0.0-patcher

# Bad (might confuse with production)
v3.1.4-toolset-test
v3.1.4-test-toolset
```

### 2. Use Non-Production Versions

```bash
# Use a version that won't conflict
# If current is 3.1.2, test with:
test-v3.1.99-toolset  # Clearly not production
test-v99.0.0-toolset  # Obviously test
```

### 3. Test During Off-Hours

- Run tests when users are least active
- Minimizes risk if something goes wrong
- Easier to monitor without distractions

### 4. Monitor the Entire Run

- Don't walk away during test
- Watch each job complete
- Check logs if anything seems off

### 5. Cleanup Immediately

- Don't leave test releases hanging
- Delete test tags to avoid confusion
- Keep test-release branch or delete it

## Example: Complete Test Session

```bash
# === SETUP ===
echo "Starting safe workflow test..."

# === CREATE TEST RELEASE ===
git tag test-v3.1.99-toolset
git push origin test-v3.1.99-toolset

gh release create test-v3.1.99-toolset \
  --prerelease \
  --title "TEST: Workflow Validation 3.1.99" \
  --notes "Testing automated release workflow changes"

# === MONITOR ===
echo "Watching workflow... (this takes ~20 minutes)"
gh run watch

# === VERIFY ===
echo "Checking results..."

# Verify test-release branch
git fetch origin test-release
git show origin/test-release:Tools/HolocronToolset/src/toolset/config.py | grep currentVersion

# Verify master unchanged
git show origin/master:Tools/HolocronToolset/src/toolset/config.py | grep currentVersion

# Check release
gh release view test-v3.1.99-toolset

# === CLEANUP ===
echo "Cleaning up test artifacts..."

gh release delete test-v3.1.99-toolset --yes
git push origin --delete test-v3.1.99-toolset
# Optionally: git push origin --delete test-release

echo "✅ Test complete and cleaned up!"
```

## Summary

**For Testing Workflows Safely**:
- ✅ Use TEST workflows with `test-` tag prefix
- ✅ Updates go to `test-release` branch only
- ✅ Master branch is never touched
- ✅ Auto-update is never triggered
- ✅ Easy cleanup

**When Ready for Production**:
- Use real tags without `test-` prefix (e.g., `v3.1.4-toolset`)
- Production workflows update master automatically
- Release converts to full release
- Auto-update triggers for users

