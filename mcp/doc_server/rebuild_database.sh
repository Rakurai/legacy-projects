#!/bin/bash
# rebuild_database.sh - Drop and recreate database for fresh build

set -e  # Exit on error

echo "==> Dropping database legacy_og_docs..."
docker exec mcp-legacy-og-docs psql -U postgres -c "DROP DATABASE IF EXISTS legacy_og_docs;"

echo "==> Creating fresh database..."
docker exec mcp-legacy-og-docs psql -U postgres -c "CREATE DATABASE legacy_og_docs;"

echo "==> Installing pgvector extension..."
docker exec mcp-legacy-og-docs psql -U postgres -d legacy_og_docs -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "==> Clearing Python bytecode cache..."
find server -name "*.pyc" -delete 2>/dev/null || true
find server -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find build_helpers -name "*.pyc" -delete 2>/dev/null || true
find build_helpers -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "==> Database ready for build!"
echo ""
echo "Run: uv run python build_mcp_db.py"
