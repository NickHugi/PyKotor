# Release Workflow Cheat Sheet

## 🎯 Production Release (3 commands)

```bash
# 1. Tag the release
git tag v3.1.4-toolset
git push origin v3.1.4-toolset

# 2. Create pre-release on GitHub
gh release create v3.1.4-toolset \
  --prerelease \
  --title "Toolset 3.1.4" \
  --notes "Your release notes here"

# 3. Wait ~20 minutes - everything else is automatic!
```

**What happens automatically**:
1. Updates `currentVersion` → commits to master
2. Builds binaries with new version
3. Uploads artifacts to release
4. Updates `toolsetLatestVersion` → commits to master
5. Regenerates source archives
6. Converts to full release ✅

## 🧪 Test Release (4 commands)

```bash
# 1. Create test release
git tag test-v3.1.99-toolset
git push origin test-v3.1.99-toolset
gh release create test-v3.1.99-toolset --prerelease --title "TEST" --notes "Testing"

# 2. Wait ~20 minutes - workflow runs

# 3. Verify (master should be unchanged)
git show origin/master:Tools/HolocronToolset/src/toolset/config.py | grep currentVersion

# 4. Cleanup
gh release delete test-v3.1.99-toolset --yes
git push origin --delete test-v3.1.99-toolset
```

**What's different in test mode**:
- ❌ Never touches `master` (uses `test-release` branch)
- ❌ Doesn't convert to full release
- ❌ Won't trigger auto-update for users
- ✅ Adds TEST warning to description

## 📋 Tag Patterns

### Production
```
v3.1.4-toolset      → HolocronToolset
v1.0.1-kotordiff    → KotorDiff
v1.7.1-patcher      → HoloPatcher
v1.0.0-guiconverter → GuiConverter
v1.0.0-translator   → Translator
```

### Test
```
test-v3.1.99-toolset      → HolocronToolset (TEST)
test-v1.0.99-kotordiff    → KotorDiff (TEST)
test-v1.7.99-patcher      → HoloPatcher (TEST)
test-v1.0.99-guiconverter → GuiConverter (TEST)
test-v1.0.99-translator   → Translator (TEST)
```

## 📊 Workflow Timeline

```
00:00 ─ Create pre-release
00:01 ─ Validate tag
00:02 ─ Update currentVersion → commit to master → update tag
00:03 ─ Build starts (6 parallel jobs)
00:16 ─ Build complete
00:17 ─ Upload artifacts
00:19 ─ Update Latest versions → commit to master → update tag
00:20 ─ Convert to full release ✅
```

## 🔍 Validation

```powershell
# Validate workflows are set up correctly
.\.github\workflows\validate_workflows.ps1
```

## 📚 Documentation

- **RELEASE_WORKFLOW.md** - Complete guide
- **QUICK_TEST_GUIDE.md** - Safe testing  
- **TESTING_RELEASES.md** - Advanced testing
- **README.md** - Overview

## 🆘 Emergency Commands

### Cancel Running Workflow
```bash
gh run cancel <run-id>
# Or via GitHub Actions tab → Cancel workflow
```

### Revert Bad Release
```bash
# If caught before finalize completes:
gh release delete v3.1.4-toolset --yes
git push origin --delete v3.1.4-toolset

# If finalize completed:
git revert <commit-sha>  # Revert the version commit
git push origin master
gh release delete v3.1.4-toolset --yes
```

### Fix Version Manually
```bash
# Edit config.py locally
vim Tools/HolocronToolset/src/toolset/config.py

# Commit and push
git add Tools/HolocronToolset/src/toolset/config.py
git commit -m "fix: Correct version info"
git push origin master
```

## ✅ Pre-Flight Checklist

Before creating a production release:

- [ ] Version number is correct and follows semver
- [ ] Release notes are ready
- [ ] All tests pass on master
- [ ] No uncommitted changes
- [ ] Tested with TEST workflow first (recommended)
- [ ] Ready to monitor for ~20 minutes

## 🎓 First Time Setup

```bash
# 1. Validate setup
.\.github\workflows\validate_workflows.ps1

# 2. Run safe test
git tag test-v3.1.99-toolset
git push origin test-v3.1.99-toolset
gh release create test-v3.1.99-toolset --prerelease --title "TEST" --notes "First test"

# 3. Watch Actions tab (~20 min)

# 4. Verify test-release branch created (master untouched)
git fetch origin test-release
git show origin/test-release:Tools/HolocronToolset/src/toolset/config.py | grep currentVersion
git show origin/master:Tools/HolocronToolset/src/toolset/config.py | grep currentVersion

# 5. Cleanup
gh release delete test-v3.1.99-toolset --yes
git push origin --delete test-v3.1.99-toolset

# 6. Ready for production! 🎉
```

## 💡 Pro Tips

1. **Use descriptive test tags**: `test-v3.1.99-toolset` clearly indicates it's a test
2. **Test during off-hours**: Minimize risk if something unexpected happens
3. **Monitor the first run**: Watch the entire workflow the first time
4. **Keep test-release branch**: Reuse it for multiple tests, delete when done
5. **Check release artifacts**: Download and verify binaries work

## 🔗 Quick Links

- Validate: `.\.github\workflows\validate_workflows.ps1`
- Test Guide: `QUICK_TEST_GUIDE.md`
- Full Guide: `RELEASE_WORKFLOW.md`
- Create Test Workflow: `.\create_test_workflow.ps1 -ToolName "kotordiff"`

