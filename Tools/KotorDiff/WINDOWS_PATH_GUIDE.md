# Windows Path Handling Guide for KotorDiff

## The Problem

Windows PowerShell has special handling for quotes and backslashes that can cause issues when passing paths as command-line arguments. Specifically, a trailing backslash before a closing quote (`\"`) is interpreted as an **escaped quote**, not as a path separator followed by a quote.

### Example

```powershell
# This is BROKEN - PowerShell interprets \" as an escaped quote
--path1="C:\Program Files\Steam\"

# PowerShell sees this as: --path1="C:\Program Files\Steam" (with the quote escaped)
# The string continues past where you expect it to end!
```

## Solutions

KotorDiff now includes automatic path normalization that attempts to fix common Windows quoting issues, but you can also avoid the problem entirely by using one of these approaches:

### Option 1: Remove Trailing Backslash (Recommended)

```powershell
--path1="C:\Program Files\Steam"
--path2="C:\Other Path"
```

### Option 2: Use Forward Slashes

Windows accepts forward slashes in paths:

```powershell
--path1="C:/Program Files/Steam/"
--path2="C:/Other Path/"
```

### Option 3: Double the Trailing Backslash

```powershell
--path1="C:\Program Files\Steam\\"
--path2="C:\Other Path\\"
```

### Option 4: No Quotes (if no spaces)

```powershell
--path1=C:\Windows\System32
--path2=C:\OtherFolder
```

## Usage Examples

### Named Arguments (Explicit)

```powershell
# Works
uv run kotordiff --path1="C:\Program Files\KOTOR" --path2="C:\Program Files\KOTOR Modded"

# Also works
uv run kotordiff --path1 "C:\Program Files\KOTOR" --path2 "C:\Program Files\KOTOR Modded"

# Also works with forward slashes
uv run kotordiff --path1="C:/Program Files/KOTOR/" --path2="C:/Program Files/KOTOR Modded/"
```

### Positional Arguments

```powershell
# Works
uv run kotordiff "C:\Program Files\KOTOR" "C:\Program Files\KOTOR Modded"
```

### No Arguments (Interactive)

```powershell
# Prompts you for each path
uv run kotordiff
Path to the first K1/TSL install, file, or directory to diff.: C:\Program Files\KOTOR
Path to the second K1/TSL install, file, or directory to diff.: C:\Program Files\KOTOR Modded
```

## Automatic Path Normalization

KotorDiff now automatically:

- Strips leading/trailing whitespace
- Removes surrounding quotes
- Detects and fixes mangled paths from PowerShell quote escaping
- Removes embedded quotes
- Strips unnecessary trailing slashes
- Handles both Windows and Unix-style path separators

This means even if you make a mistake with quoting, KotorDiff will try its best to understand what you meant.

## Error Messages

If you encounter a path error, KotorDiff will now provide helpful hints:

```
Invalid path: C:\Program Files\Steam" C:\Program

Note: If using paths with spaces and trailing backslashes in PowerShell:
  - Remove trailing backslash: --path1="C:\Program Files\folder"
  - Or double the backslash: --path1="C:\Program Files\folder\\"
  - Or use forward slashes: --path1="C:/Program Files/folder/"
```

## Best Practice

**For maximum compatibility**: Remove trailing backslashes from quoted paths, or use forward slashes throughout.

```powershell
# Best
--path1="C:/Program Files/KOTOR"

# Also good
--path1="C:\Program Files\KOTOR"

# Avoid
--path1="C:\Program Files\KOTOR\"
```
