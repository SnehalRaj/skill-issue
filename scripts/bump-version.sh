#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.4.0"
    exit 1
fi

VERSION="$1"
ROOT="$(git rev-parse --show-toplevel)"

# Validate semver format
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: version must be semver (e.g. 1.4.0)"
    exit 1
fi

# Update pyproject.toml
sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" "$ROOT/pyproject.toml"

# Update .claude-plugin/plugin.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" "$ROOT/.claude-plugin/plugin.json"

echo "Bumped to $VERSION in:"
echo "  pyproject.toml"
echo "  .claude-plugin/plugin.json"
