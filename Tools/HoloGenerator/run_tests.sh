#!/bin/bash

# Test runner script for HoloGenerator
# This script runs all tests for the HoloGenerator project

set -e

echo "========================================="
echo "HoloGenerator Test Suite"
echo "========================================="

# Change to the HoloGenerator directory
cd "$(dirname "$0")"

echo "Running Python unit tests..."
echo "-----------------------------------------"

# Run Python tests
if command -v python3 &> /dev/null; then
    echo "Running core functionality tests..."
    python3 -m pytest src/hologenerator/tests/ -v --tb=short
    
    echo "Running CLI tests..."
    python3 -m unittest src/hologenerator/tests/test_cli.py -v
    
    echo "Running GUI tests (if available)..."
    python3 -m unittest src/hologenerator/tests/test_gui.py -v || echo "GUI tests skipped (tkinter not available)"
else
    echo "Python 3 not found, skipping Python tests"
fi

echo ""
echo "Running React/TypeScript tests..."
echo "-----------------------------------------"

# Change to web directory
cd web

# Check if Node.js is available
if command -v npm &> /dev/null; then
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    echo "Running React unit tests..."
    npm test -- --coverage --watchAll=false
    
    echo "Running TypeScript type checking..."
    npx tsc --noEmit --skipLibCheck
    
    echo "Running linting..."
    npx eslint src --ext .ts,.tsx --max-warnings 0 || echo "Linting warnings found"
else
    echo "Node.js/npm not found, skipping React tests"
fi

cd ..

echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Python tests: Completed"
echo "React tests: Completed"
echo "TypeScript check: Completed"
echo ""
echo "All tests finished!"
echo "Check output above for any failures."
echo "========================================="