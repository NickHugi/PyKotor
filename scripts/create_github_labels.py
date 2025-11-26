"""Script to create standard GitHub labels for the repository."""
from __future__ import annotations

# Standard labels that should exist in the repository
LABELS = [
    # Type labels
    {"name": "bug", "color": "d73a4a", "description": "Something isn't working"},
    {"name": "enhancement", "color": "a2eeef", "description": "New feature or request"},
    {"name": "documentation", "color": "0075ca", "description": "Documentation improvements"},
    {"name": "question", "color": "d876e3", "description": "Further information is requested"},
    {"name": "duplicate", "color": "cfd3d7", "description": "This issue or pull request already exists"},
    {"name": "invalid", "color": "e4e669", "description": "This doesn't seem right"},
    {"name": "wontfix", "color": "ffffff", "description": "This will not be worked on"},
    {"name": "help wanted", "color": "008672", "description": "Extra attention is needed"},
    {"name": "good first issue", "color": "7057ff", "description": "Good for newcomers"},
    
    # Status labels
    {"name": "needs-triage", "color": "fbca04", "description": "Needs to be triaged"},
    {"name": "in-progress", "color": "0e8a16", "description": "Work in progress"},
    {"name": "blocked", "color": "b60205", "description": "Blocked by another issue"},
    {"name": "stale", "color": "ededed", "description": "Stale issue or PR"},
    
    # Priority labels
    {"name": "priority: critical", "color": "b60205", "description": "Critical priority"},
    {"name": "priority: high", "color": "d93f0b", "description": "High priority"},
    {"name": "priority: medium", "color": "fbca04", "description": "Medium priority"},
    {"name": "priority: low", "color": "0e8a16", "description": "Low priority"},
    
    # Package labels
    {"name": "package: pykotor", "color": "1d76db", "description": "Related to PyKotor core"},
    {"name": "package: pykotorgl", "color": "1d76db", "description": "Related to PyKotorGL"},
    {"name": "package: pykotorfont", "color": "1d76db", "description": "Related to PyKotorFont"},
    {"name": "package: toolset", "color": "1d76db", "description": "Related to HolocronToolset"},
    {"name": "package: holopatcher", "color": "1d76db", "description": "Related to HoloPatcher"},
    {"name": "package: batchpatcher", "color": "1d76db", "description": "Related to BatchPatcher"},
    {"name": "package: kotordiff", "color": "1d76db", "description": "Related to KotorDiff"},
    {"name": "package: guiconverter", "color": "1d76db", "description": "Related to GuiConverter"},
    
    # Size labels (for PRs)
    {"name": "size/XS", "color": "3cbf00", "description": "Extra small PR (< 30 lines)"},
    {"name": "size/S", "color": "5d9801", "description": "Small PR (30-100 lines)"},
    {"name": "size/M", "color": "7f7203", "description": "Medium PR (100-300 lines)"},
    {"name": "size/L", "color": "a14c05", "description": "Large PR (300-500 lines)"},
    {"name": "size/XL", "color": "c32607", "description": "Extra large PR (500-1000 lines)"},
    {"name": "size/XXL", "color": "e50009", "description": "XXL PR (> 1000 lines)"},
    
    # Area labels
    {"name": "area: libraries", "color": "c2e0c6", "description": "Related to libraries"},
    {"name": "area: tools", "color": "c2e0c6", "description": "Related to tools"},
    {"name": "area: tests", "color": "c2e0c6", "description": "Related to tests"},
    {"name": "area: ci/cd", "color": "c2e0c6", "description": "Related to CI/CD"},
    {"name": "area: documentation", "color": "c2e0c6", "description": "Related to documentation"},
    {"name": "area: dependencies", "color": "c2e0c6", "description": "Related to dependencies"},
    
    # Special labels
    {"name": "security", "color": "b60205", "description": "Security related"},
    {"name": "breaking-change", "color": "b60205", "description": "Breaking change"},
    {"name": "performance", "color": "fbca04", "description": "Performance related"},
    {"name": "refactor", "color": "e99695", "description": "Code refactoring"},
    {"name": "chore", "color": "ededed", "description": "Chores and maintenance"},
    {"name": "pinned", "color": "000000", "description": "Pinned issue or discussion"},
    {"name": "work-in-progress", "color": "ededed", "description": "Work in progress"},
    {"name": "ignore-for-release", "color": "ededed", "description": "Ignore in release notes"},
]

print("GitHub Labels Configuration")
print("=" * 50)
print("\nTo create these labels, use the GitHub CLI or web interface:")
print("\nUsing GitHub CLI (gh):")
print("  gh label create <name> --color <color> --description '<description>'")
print("\nOr use the GitHub web interface:")
print("  https://github.com/th3w1zard1/PyKotor/labels")
print("\nLabels to create:")
print("-" * 50)
for label in LABELS:
    print(f"  {label['name']:30} {label['color']:8} {label['description']}")

