#!/bin/bash
# Re-enable CI hooks

echo "🔧 Re-enabling CI hooks..."

# Remove marker file
if [ -f .skip_ci_hooks ]; then
    rm .skip_ci_hooks
    echo "✅ Removed .skip_ci_hooks marker file"
fi

# Unset environment variable
unset SKIP_CI_HOOKS

echo "✅ CI hooks re-enabled"
echo "💡 Next commit/push will run CI simulation"
