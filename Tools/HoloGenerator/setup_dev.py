#!/usr/bin/env python3
"""
Setup script for HoloGenerator development environment.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, description=""):
    """Run a command and handle errors."""
    if description:
        print(f"📦 {description}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ Success: {' '.join(cmd)}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        return None


def setup_python_environment():
    """Set up Python development environment."""
    print("\n🐍 Setting up Python environment...")
    
    # Check if we're in a virtual environment
    if sys.prefix == sys.base_prefix:
        print("⚠️  Consider using a virtual environment for development")
    
    # Install development dependencies
    requirements = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "black>=22.0.0",
        "flake8>=5.0.0",
        "mypy>=1.0.0",
    ]
    
    for req in requirements:
        run_command([sys.executable, "-m", "pip", "install", req], 
                   description=f"Installing {req}")


def setup_web_environment():
    """Set up React/Node.js development environment."""
    print("\n⚛️  Setting up React environment...")
    
    web_dir = Path(__file__).parent / "web"
    
    # Check if Node.js is available
    node_check = run_command(["node", "--version"], description="Checking Node.js")
    if not node_check:
        print("❌ Node.js not found. Please install Node.js 16+ to continue.")
        return False
    
    npm_check = run_command(["npm", "--version"], description="Checking npm")
    if not npm_check:
        print("❌ npm not found. Please install npm to continue.")
        return False
    
    # Install dependencies
    run_command(["npm", "install"], cwd=web_dir, description="Installing React dependencies")
    
    return True


def setup_git_hooks():
    """Set up git hooks for development."""
    print("\n🔧 Setting up git hooks...")
    
    repo_root = Path(__file__).parent.parent.parent.parent
    hooks_dir = repo_root / ".git" / "hooks"
    
    if not hooks_dir.exists():
        print("⚠️  Git hooks directory not found. Are you in a git repository?")
        return
    
    # Create pre-commit hook
    pre_commit_hook = hooks_dir / "pre-commit"
    hook_content = """#!/bin/bash
# Pre-commit hook for HoloGenerator

echo "Running HoloGenerator tests before commit..."

# Change to HoloGenerator directory
cd Tools/HoloGenerator

# Run Python tests
echo "Running Python tests..."
python3 -m pytest src/hologenerator/tests/ --tb=short -q || exit 1

# Run React tests if available
if [ -d "web/node_modules" ]; then
    echo "Running React tests..."
    cd web
    npm test -- --coverage --watchAll=false --silent || exit 1
    cd ..
fi

echo "All tests passed! ✅"
"""
    
    try:
        pre_commit_hook.write_text(hook_content)
        pre_commit_hook.chmod(0o755)
        print("✅ Pre-commit hook installed")
    except Exception as e:
        print(f"❌ Failed to install pre-commit hook: {e}")


def main():
    """Main setup function."""
    print("🚀 HoloGenerator Development Setup")
    print("==================================")
    
    # Setup Python environment
    setup_python_environment()
    
    # Setup web environment
    web_success = setup_web_environment()
    
    # Setup git hooks
    setup_git_hooks()
    
    print("\n🎉 Setup Complete!")
    print("==================")
    print()
    print("Next steps:")
    print("1. Run tests: ./run_tests.sh")
    print("2. Start React dev server: cd web && npm start")
    print("3. Test CLI: python -m hologenerator --help")
    print("4. Test GUI: python -m hologenerator --gui")
    print()
    print("Happy coding! 🎯")


if __name__ == "__main__":
    main()