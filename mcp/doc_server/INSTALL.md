# Installation & Database Setup

This guide covers setting up the PostgreSQL database and building the data for
the MCP Documentation Server. For what the server does and how to use it, see
[README.md](README.md).

---

## Prerequisites

- **uv** for Python dependency management
- **Docker** (recommended) or PostgreSQL 17+ installed locally (with pgvector and pg_trgm extensions)
- Legacy MUD source tree on disk (for source code extraction during build)
- Pre-computed artifacts in `../../artifacts/`

---

## 1. PostgreSQL Setup

### Option A: Docker (Recommended)

The included `docker-compose.yml` uses the `pgvector/pgvector:pg17` image with
pgvector pre-installed.

```bash
cd mcp/doc_server/
docker-compose up -d
```

Verify:

```bash
docker exec -it mcp-postgres psql -U postgres -d legacy_docs -c "SELECT version();"
docker exec -it mcp-postgres psql -U postgres -d legacy_docs -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec -it mcp-postgres psql -U postgres -d legacy_docs -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

Container management:

```bash
docker-compose down        # stop (data persists in volume)
docker-compose down -v     # stop and delete data
docker-compose up -d       # start again
```

### Option B: Local PostgreSQL

**macOS (Homebrew):**

```bash
brew install postgresql@17
brew services start postgresql@17
brew install pgvector
```

**Ubuntu/Debian:**

```bash
sudo apt-get install postgresql-17 postgresql-17-pgvector
sudo systemctl start postgresql
```

Create the database:

```bash
psql postgres <<SQL
CREATE DATABASE legacy_docs;
\c legacy_docs
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SQL
```

---

## 2. Environment Configuration

```bash
cd mcp/doc_server/
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432          # or 4010, whatever your instance uses
DB_NAME=legacy_docs
DB_USER=postgres
DB_PASSWORD=postgres

# Paths
PROJECT_ROOT=/path/to/legacy/cpp/repo    # for source code extraction
ARTIFACTS_DIR=/path/to/artifacts          # usually ../../artifacts

# Embedding (required)
EMBEDDING_PROVIDER=local                  # "local" or "hosted"
EMBEDDING_DIMENSION=768
EMBEDDING_LOCAL_MODEL=BAAI/bge-base-en-v1.5

# Cross-encoder (optional — defaults to Xenova/ms-marco-MiniLM-L-6-v2)
# CROSS_ENCODER_MODEL=Xenova/ms-marco-MiniLM-L-6-v2
```

---

## 3. Build the Database

```bash
cd mcp/doc_server/
uv sync
uv run python -m build_mcp_db
```

The build script:
- Drops and recreates all tables
- Ingests entities from `code_graph.json` (~5,300 entities)
- Loads the dependency graph from `code_graph.gml` (~25K edges)
- Merges LLM-generated documentation from `generated_docs/*.json`
- Assigns capabilities from `capability_defs.json` and `capability_graph.json`
- Extracts source code from disk using `PROJECT_ROOT`
- Generates dual embeddings (doc + symbol) for multi-view search
- Computes ts_rank ceilings for corpus-calibrated score normalization
- Creates all indexes

Expected time: 1–3 minutes (including local embedding generation).

---

## 4. Verify

Test the database connection:

```bash
psql -h localhost -p 5432 -U postgres -d legacy_docs \
  -c "SELECT count(*) FROM entities;"
# Should return ~5,300
```

Start the server:

```bash
cd mcp/doc_server/
uv run python -m server.server
```

Or test with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector -- \
  uv run --directory mcp/doc_server python -m server.server
```

---

## Troubleshooting

### Connection Refused

```bash
# Docker
docker ps | grep postgres

# Local (macOS)
brew services list | grep postgresql

# Local (Linux)
sudo systemctl status postgresql
```

### Authentication Failed

Verify password in `.env` matches the database user's password. Docker default
is `postgres`/`postgres`. Reset if needed:

```sql
ALTER USER postgres WITH PASSWORD 'new_password';
```

### pgvector Not Found

Docker: ensure you're using the `pgvector/pgvector` image, not plain `postgres`.
Local: install via `brew install pgvector` or build from source.

### Port Conflict

```bash
lsof -i :5432
# Change port in docker-compose.yml and .env if needed
```

### Build Fails on Source Extraction

`PROJECT_ROOT` must point to the legacy C++ repository root. The build raises
`BuildError` if body-located entities exist but zero source texts are extracted.

---

## Rebuilding

After updating artifacts or source code, rebuild:

```bash
cd mcp/doc_server/
uv run python -m build_mcp_db
```

The build is idempotent — it drops and recreates all tables from scratch.
