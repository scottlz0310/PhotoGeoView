#!/bin/sh
# PhotoGeoView CI Simulation Pre-commit Hook Template
# This template is used by the GitHookManager to generate actual hooks

echo "🔍 Running CI simulation before commit..."

# Get list of staged files for targeted checking
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|yml|yaml|json|md)$' || true)

if [ -z "$STAGED_FILES" ]; then
    echo "ℹ️  No relevant files staged for commit. Skipping CI checks."
    exit 0
fi

echo "📁 Checking staged files: $(echo $STAGED_FILES | wc -w) files"

# Run CI simulation with specified checks
# This will be replaced with actual Python executable and simulator path
{python_executable} {simulator_path} run {checks} --quiet

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "⏰ CI simulation timed out after {timeout} seconds"
    echo "💡 Consider running checks manually: python {simulator_path} run"
    exit 1
elif [ $EXIT_CODE -ne 0 ]; then
    echo "❌ CI simulation failed. Commit aborted."
    echo "💡 Run 'python {simulator_path} run' for detailed results"
    echo "💡 Use 'git commit --no-verify' to bypass this check (not recommended)"
    exit 1
fi

echo "✅ CI simulation passed. Proceeding with commit."
exit 0
