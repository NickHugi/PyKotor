"""Script to create GitHub Actions workflow files."""
from __future__ import annotations

from pathlib import Path

WORKFLOWS_DIR = Path(".github/workflows")
WORKFLOWS_DIR.mkdir(parents=True, exist_ok=True)

# CI Workflow
ci_workflow = """name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

jobs:
  test:
    name: Test Python ${{ matrix.python-version }} on ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
        exclude:
          - os: macos-latest
            python-version: "3.8"
          - os: macos-latest
            python-version: "3.9"
          - os: windows-latest
            python-version: "3.8"
          - os: windows-latest
            python-version: "3.9"

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install dependencies
        run: |
          uv pip install --upgrade pip setuptools wheel build
          uv pip install -e Libraries/PyKotor
          uv pip install -e Libraries/PyKotorGL
          uv pip install -e Libraries/PyKotorFont
          uv pip install -e .[dev]

      - name: Verify imports
        run: |
          python -c "import pykotor; print('PyKotor imported successfully')"
          python -c "import pykotor.gl; print('PyKotorGL imported successfully')"
          python -c "import pykotor.font; print('PyKotorFont imported successfully')"

      - name: Run tests
        run: |
          pytest tests/ -v --tb=short --maxfail=5
        continue-on-error: ${{ matrix.python-version == '3.8' || matrix.python-version == '3.9' }}

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results-${{ matrix.os }}-py${{ matrix.python-version }}
          path: |
            pytest.log
            .pytest_cache/
          retention-days: 7

  build:
    name: Build packages
    runs-on: ubuntu-latest
    needs: test
    strategy:
      matrix:
        package:
          - Libraries/PyKotor
          - Libraries/PyKotorGL
          - Libraries/PyKotorFont
          - Tools/HolocronToolset
          - Tools/HoloPatcher
          - Tools/BatchPatcher
          - Tools/KotorDiff
          - Tools/GuiConverter

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip setuptools wheel build

      - name: Build ${{ matrix.package }}
        working-directory: ${{ matrix.package }}
        run: |
          python -m build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist-${{ matrix.package }}
          path: ${{ matrix.package }}/dist/*
          retention-days: 30
"""

# Lint Workflow
lint_workflow = """name: Lint and Type Check

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

jobs:
  ruff:
    name: Ruff Linting
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install dependencies
        run: |
          uv pip install ruff

      - name: Run ruff check
        run: |
          ruff check . --output-format=github

      - name: Check formatting
        run: |
          ruff format --check .

  mypy:
    name: MyPy Type Checking
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install dependencies
        run: |
          uv pip install -e Libraries/PyKotor
          uv pip install -e Libraries/PyKotorGL
          uv pip install -e Libraries/PyKotorFont
          uv pip install mypy types-all

      - name: Run mypy
        run: |
          mypy Libraries/PyKotor/src Libraries/PyKotorGL/src Libraries/PyKotorFont/src --config-file pyproject.toml || true
        continue-on-error: true
"""

# Test Workflow
test_workflow = """name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  workflow_dispatch:

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Install dependencies
        run: |
          uv pip install --upgrade pip setuptools wheel
          uv pip install -e Libraries/PyKotor
          uv pip install -e Libraries/PyKotorGL
          uv pip install -e Libraries/PyKotorFont
          uv pip install pytest pytest-cov pytest-xdist pytest-html

      - name: Run tests with coverage
        run: |
          pytest tests/ \\
            --cov=Libraries/PyKotor/src/pykotor \\
            --cov=Libraries/PyKotorGL/src/pykotor \\
            --cov=Libraries/PyKotorFont/src/pykotor \\
            --cov-report=xml \\
            --cov-report=html \\
            --cov-report=term \\
            --junit-xml=junit.xml \\
            -v

      - name: Upload coverage reports
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
          fail_ci_if_error: false

      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results-py${{ matrix.python-version }}
          path: |
            coverage.xml
            htmlcov/
            junit.xml
          retention-days: 30

      - name: Upload HTML coverage report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: coverage-html-py${{ matrix.python-version }}
          path: htmlcov/
          retention-days: 7
"""

# Release Workflow
release_workflow = """name: Release

on:
  release:
    types: [published]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release (e.g., 1.8.0)'
        required: true
        type: string

jobs:
  build-and-publish:
    name: Build and Publish to PyPI
    runs-on: ubuntu-latest
    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: 'pip'

      - name: Install build dependencies
        run: |
          python -m pip install --upgrade pip setuptools wheel build twine

      - name: Build PyKotor
        working-directory: Libraries/PyKotor
        run: |
          python -m build

      - name: Build PyKotorGL
        working-directory: Libraries/PyKotorGL
        run: |
          python -m build

      - name: Build PyKotorFont
        working-directory: Libraries/PyKotorFont
        run: |
          python -m build

      - name: Build HolocronToolset
        working-directory: Tools/HolocronToolset
        run: |
          python -m build

      - name: Build HoloPatcher
        working-directory: Tools/HoloPatcher
        run: |
          python -m build

      - name: Build BatchPatcher
        working-directory: Tools/BatchPatcher
        run: |
          python -m build

      - name: Build KotorDiff
        working-directory: Tools/KotorDiff
        run: |
          python -m build

      - name: Build GuiConverter
        working-directory: Tools/GuiConverter
        run: |
          python -m build

      - name: Publish PyKotor to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: Libraries/PyKotor/dist/
          print-hash: true

      - name: Publish PyKotorGL to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: Libraries/PyKotorGL/dist/
          print-hash: true

      - name: Publish PyKotorFont to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: Libraries/PyKotorFont/dist/
          print-hash: true

      - name: Upload release artifacts
        uses: actions/upload-artifact@v4
        with:
          name: release-packages
          path: |
            Libraries/*/dist/*
            Tools/*/dist/*
          retention-days: 90
"""

# CodeQL Workflow
codeql_workflow = """name: CodeQL Security Analysis

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 0 * * 0'
  workflow_dispatch:

jobs:
  analyze:
    name: Analyze
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write

    strategy:
      fail-fast: false
      matrix:
        language: [ 'python' ]

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: +security-and-quality

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
"""

# Dependency Review Workflow
dependency_review_workflow = """name: Dependency Review

on:
  pull_request:
    branches: [ main, develop ]

permissions:
  contents: read

jobs:
  dependency-review:
    name: Review Dependencies
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Dependency Review
        uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: moderate
          deny-licenses: GPL-2.0, GPL-3.0
          allow-licenses: LGPL-3.0, MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause
"""

# Dependabot Config
dependabot_config = """version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    commit-message:
      prefix: "chore"
      include: "scope"

  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    commit-message:
      prefix: "chore"
      include: "scope"
    ignore:
      - dependency-name: "ply"
        update-types: ["version-update:semver-major"]
      - dependency-name: "numpy"
        update-types: ["version-update:semver-major"]
      - dependency-name: "PyOpenGL"
        update-types: ["version-update:semver-major"]

  - package-ecosystem: "pip"
    directory: "/Libraries/PyKotor"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(pykotor)"
      include: "scope"

  - package-ecosystem: "pip"
    directory: "/Libraries/PyKotorGL"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(pykotorgl)"
      include: "scope"

  - package-ecosystem: "pip"
    directory: "/Libraries/PyKotorFont"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(pykotorfont)"
      include: "scope"

  - package-ecosystem: "pip"
    directory: "/Tools/HolocronToolset"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(toolset)"
      include: "scope"

  - package-ecosystem: "pip"
    directory: "/Tools/HoloPatcher"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(holopatcher)"
      include: "scope"

  - package-ecosystem: "pip"
    directory: "/Tools/BatchPatcher"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(batchpatcher)"
      include: "scope"

  - package-ecosystem: "pip"
    directory: "/Tools/KotorDiff"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(kotordiff)"
      include: "scope"

  - package-ecosystem: "pip"
    directory: "/Tools/GuiConverter"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    commit-message:
      prefix: "chore(guiconverter)"
      include: "scope"
"""

# Stale Issues Workflow
stale_workflow = """name: Mark Stale Issues and PRs

on:
  schedule:
    - cron: '0 0 * * *'
  workflow_dispatch:

permissions:
  issues: write
  pull-requests: write

jobs:
  stale:
    runs-on: ubuntu-latest
    steps:
      - name: Mark stale issues and PRs
        uses: actions/stale@v9
        with:
          repo-token: ${{ secrets.GITHUB_TOKEN }}
          stale-issue-message: |
            This issue has been automatically marked as stale because it has not had recent activity.
            It will be closed if no further activity occurs within 7 days. Thank you for your contributions.
          stale-pr-message: |
            This pull request has been automatically marked as stale because it has not had recent activity.
            It will be closed if no further activity occurs within 7 days. Thank you for your contributions.
          close-issue-message: |
            This issue was automatically closed due to inactivity. If you believe this was done in error,
            please reopen the issue or create a new one.
          close-pr-message: |
            This pull request was automatically closed due to inactivity. If you believe this was done in error,
            please reopen the pull request or create a new one.
          stale-issue-label: 'stale'
          stale-pr-label: 'stale'
          days-before-issue-stale: 60
          days-before-pr-stale: 30
          days-before-issue-close: 7
          days-before-pr-close: 7
          exempt-issue-labels: 'pinned,security,bug,enhancement'
          exempt-pr-labels: 'pinned,security,work-in-progress'
          operations-per-run: 30
"""

# PR Check Workflow
pr_check_workflow = """name: PR Checks

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  pr-size:
    name: Check PR Size
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Check PR size
        uses: actions/github-script@v7
        with:
          script: |
            const { data: files } = await github.rest.pulls.listFiles({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
            });

            const additions = files.reduce((acc, file) => acc + file.additions, 0);
            const deletions = files.reduce((acc, file) => acc + file.deletions, 0);
            const changes = additions + deletions;

            let label = 'size/XS';
            let comment = '';

            if (changes > 1000) {
              label = 'size/XXL';
              comment = '⚠️ This PR is very large (>1000 lines changed). Consider breaking it into smaller PRs if possible.';
            } else if (changes > 500) {
              label = 'size/XL';
              comment = '📦 This PR is large (>500 lines changed).';
            } else if (changes > 300) {
              label = 'size/L';
            } else if (changes > 100) {
              label = 'size/M';
            } else if (changes > 30) {
              label = 'size/S';
            }

            await github.rest.issues.addLabels({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: context.issue.number,
              labels: [label],
            });

            if (comment) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: comment,
              });
            }

  check-description:
    name: Check PR Description
    runs-on: ubuntu-latest
    steps:
      - name: Check PR description
        uses: actions/github-script@v7
        with:
          script: |
            const { data: pr } = await github.rest.pulls.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
            });

            const minLength = 50;
            if (!pr.body || pr.body.length < minLength) {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: `⚠️ Please add a more detailed description to your PR (minimum ${minLength} characters). This helps reviewers understand your changes.`,
              });
            }
"""

# Labeler Config
labeler_config = """# Auto-label PRs based on changed files
libraries:
  - Libraries/**/*
  
tools:
  - Tools/**/*
  
tests:
  - tests/**/*
  
docs:
  - docs/**/*
  - README.md
  - CONTRIBUTING.md
  - *.md

ci:
  - .github/**/*
  - .github/workflows/**/*

dependencies:
  - pyproject.toml
  - requirements*.txt
  - **/requirements.txt
  - **/pyproject.toml

python:
  - '**/*.py'
"""

# Label Workflow
label_workflow = """name: Auto Label PRs

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - name: Label PR based on files changed
        uses: actions/labeler@v5
        with:
          repo-token: "${{ secrets.GITHUB_TOKEN }}"
          sync-labels: true
"""

# Write all files
workflows = {
    "ci.yml": ci_workflow,
    "lint.yml": lint_workflow,
    "test.yml": test_workflow,
    "release.yml": release_workflow,
    "codeql.yml": codeql_workflow,
    "dependency-review.yml": dependency_review_workflow,
    "stale.yml": stale_workflow,
    "pr-check.yml": pr_check_workflow,
    "label.yml": label_workflow,
}

for filename, content in workflows.items():
    filepath = WORKFLOWS_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(f"Created {filepath}")

# Write dependabot config
dependabot_path = Path(".github/dependabot.yml")
dependabot_path.parent.mkdir(parents=True, exist_ok=True)
dependabot_path.write_text(dependabot_config, encoding="utf-8")
print(f"Created {dependabot_path}")

# Write labeler config
labeler_path = Path(".github/labeler.yml")
labeler_path.write_text(labeler_config, encoding="utf-8")
print(f"Created {labeler_path}")

print("\nAll workflow files created successfully!")

