#!/bin/bash
# Disable CI hooks temporarily

echo "🔧 Disabling CI hooks temporarily..."

# Set environment variable to disable hooks
export SKIP_CI_HOOKS=true

# Also create a temporary marker file
touch .skip_ci_hooks

echo "✅ CI hooks disabled"
echo "💡 To re-enable: rm .skip_ci_hooks && unset SKIP_CI_HOOKS"
echo "💡 Or run: scripts/enable_ci_hooks.sh"
