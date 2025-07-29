#!/bin/sh
# PhotoGeoView CI Simulation Pre-push Hook Template
# This template is used by the GitHookManager to generate actual hooks

echo "🚀 Running comprehensive CI simulation before push..."

# Get information about what's being pushed
remote="$1"
url="$2"

# Read from stdin to get the refs being pushed
while read local_ref local_sha remote_ref remote_sha; do
    if [ "$local_sha" = "0000000000000000000000000000000000000000" ]; then
        # Branch is being deleted, skip checks
        continue
    fi

    if [ "$remote_sha" = "0000000000000000000000000000000000000000" ]; then
        # New branch, check all commits
        range="$local_sha"
    else
        # Existing branch, check new commits
        range="$remote_sha..$local_sha"
    fi

    # Get list of changed files in the push
    CHANGED_FILES=$(git diff --name-only "$range" | grep -E '\.(py|yml|yaml|json|md)$' || true)

    if [ -n "$CHANGED_FILES" ]; then
        echo "📁 Checking changes in push: $(echo $CHANGED_FILES | wc -w) files"
        break
    fi
done

# Run comprehensive CI simulation
echo "⏳ Running full CI simulation (timeout: {timeout}s)..."
timeout {timeout} {python_executable} {simulator_path} run {checks} --quiet

# Check exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 124 ]; then
    echo "⏰ CI simulation timed out after {timeout} seconds"
    echo "💡 Consider running checks manually: python {simulator_path} run"
    exit 1
elif [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Full CI simulation failed. Push aborted."
    echo "💡 Run 'python {simulator_path} run' for detailed results"
    echo "💡 Use 'git push --no-verify' to bypass this check (not recommended)"
    exit 1
fi

echo "✅ Full CI simulation passed. Proceeding with push."
exit 0
