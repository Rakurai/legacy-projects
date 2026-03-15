# Legacy MUD Documentation Server - PostgreSQL Setup

This guide covers setting up PostgreSQL 18 with pgvector extension for the MCP Documentation Server. The build script will create tables; this README focuses on database and user setup.

---

## Prerequisites

- Docker (recommended) OR PostgreSQL 18+ installed locally
- `psql` command-line tool (included with PostgreSQL)

---

## Option 1: Docker Setup (Recommended)

### 1.1 Create Docker Compose File

Create `docker-compose.yml` in `.ai/mcp/doc_server/`:

```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg17
    container_name: mcp-postgres
    environment:
      POSTGRES_DB: legacy_docs
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
    driver: local
```

**Note**: Using `pgvector/pgvector:pg17` image which includes PostgreSQL 17 + pgvector extension pre-installed.

### 1.2 Start Container

```bash
cd .ai/mcp/doc_server/
docker-compose up -d
```

Expected output:
```
[+] Running 2/2
 ✔ Network doc_server_default    Created
 ✔ Container mcp-postgres         Started
```

### 1.3 Verify Container

```bash
# Check container status
docker ps | grep mcp-postgres

# Expected output:
# CONTAINER ID   IMAGE                    STATUS        PORTS
# abc123def456   pgvector/pgvector:pg17   Up 10 seconds 0.0.0.0:5432->5432/tcp

# Check logs
docker logs mcp-postgres

# Should see:
# PostgreSQL init process complete; ready for start up.
# database system is ready to accept connections
```

### 1.4 Connect and Verify

```bash
# Connect to database
docker exec -it mcp-postgres psql -U postgres -d legacy_docs

# You should see:
# psql (17.x)
# Type "help" for help.
#
# legacy_docs=#
```

### 1.5 Verify pgvector Extension

```sql
-- In psql prompt:
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
\dx

-- Expected output should include:
--   Name   | Version |   Schema   |         Description
-- ---------+---------+------------+------------------------------
--  vector  | 0.7.x   | public     | vector data type and ivfflat access method

-- Test vector type
CREATE TABLE vector_test (id serial, embedding vector(3));
INSERT INTO vector_test (embedding) VALUES ('[1,2,3]');
SELECT * FROM vector_test;

-- Clean up test
DROP TABLE vector_test;

-- Exit psql
\q
```

### 1.6 Stop/Start Container

```bash
# Stop
docker-compose down

# Start again (data persists in volume)
docker-compose up -d

# Remove everything (including data volume)
docker-compose down -v
```

---

## Option 2: Local PostgreSQL Installation

### 2.1 Install PostgreSQL 18+

**macOS (Homebrew):**
```bash
brew install postgresql@18
brew services start postgresql@18

# Add to PATH
echo 'export PATH="/opt/homebrew/opt/postgresql@18/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Ubuntu/Debian:**
```bash
# Add PostgreSQL apt repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt-get update

# Install PostgreSQL 18
sudo apt-get install postgresql-18
```

**Verify Installation:**
```bash
psql --version
# Expected: psql (PostgreSQL) 18.x
```

### 2.2 Install pgvector Extension

**From Source (all platforms):**
```bash
# Install build dependencies (macOS)
brew install cmake

# Install build dependencies (Ubuntu)
sudo apt-get install build-essential postgresql-server-dev-18

# Clone and build pgvector
git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
cd pgvector
make
make install  # May require sudo

# Verify installation
psql -c "CREATE EXTENSION vector;" postgres
```

**Or via Package Manager:**
```bash
# macOS
brew install pgvector

# Ubuntu (if available in repo)
sudo apt-get install postgresql-18-pgvector
```

### 2.3 Create Database and User

```bash
# Connect as superuser (usually your OS user on macOS, postgres on Linux)
psql postgres

# Or on Linux:
sudo -u postgres psql
```

**In psql prompt:**
```sql
-- Create user (if not using default postgres user)
CREATE USER mcp_user WITH PASSWORD 'your_secure_password_here';

-- Create database
CREATE DATABASE legacy_docs OWNER mcp_user;

-- Connect to new database
\c legacy_docs

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE legacy_docs TO mcp_user;
GRANT ALL ON SCHEMA public TO mcp_user;

-- Verify
\dx
\l legacy_docs

-- Exit
\q
```

### 2.4 Configure Authentication (if needed)

**Edit `pg_hba.conf`:**

```bash
# Find config file
psql -c "SHOW hba_file;" postgres

# Example location: /opt/homebrew/var/postgresql@18/pg_hba.conf
# Edit with your favorite editor
nano $(psql -t -c "SHOW hba_file;" postgres)
```

**Add/modify line for local connections:**
```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    legacy_docs     mcp_user        127.0.0.1/32            md5
```

**Reload configuration:**
```bash
# macOS
brew services restart postgresql@18

# Linux
sudo systemctl reload postgresql
```

---

## Configuration File Setup

### Create `.env` File

```bash
cd .ai/mcp/doc_server/

# Copy example
cp .env.example .env

# Edit with your settings
nano .env
```

**For Docker setup:**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=legacy_docs
DB_USER=postgres
DB_PASSWORD=postgres
```

**For local PostgreSQL:**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=legacy_docs
DB_USER=mcp_user
DB_PASSWORD=your_secure_password_here
```

---

## Verify Database Connection

### Test from Command Line

```bash
# Using connection string from .env
psql -h localhost -p 5432 -U postgres -d legacy_docs

# Or with environment variables
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=legacy_docs
export PGUSER=postgres
export PGPASSWORD=postgres

psql
```

### Test from Python

Create `test_connection.py`:

```python
import asyncio
import asyncpg
from pathlib import Path
from dotenv import load_dotenv
import os

async def test_connection():
    # Load .env
    load_dotenv()

    # Connect
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "legacy_docs"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )

    # Test query
    version = await conn.fetchval("SELECT version();")
    print(f"Connected! PostgreSQL version:\n{version}")

    # Test pgvector
    try:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        result = await conn.fetchval("SELECT '[1,2,3]'::vector;")
        print(f"\npgvector working: {result}")
    except Exception as e:
        print(f"\npgvector error: {e}")

    await conn.close()
    print("\nConnection test successful!")

if __name__ == "__main__":
    asyncio.run(test_connection())
```

Run test:
```bash
uv run python test_connection.py
```

Expected output:
```
Connected! PostgreSQL version:
PostgreSQL 17.x on x86_64-pc-linux-gnu, compiled by gcc ...

pgvector working: [1,2,3]

Connection test successful!
```

---

## Troubleshooting

### Connection Refused

**Error**: `psql: error: connection to server at "localhost" (127.0.0.1), port 5432 failed: Connection refused`

**Solutions**:
```bash
# Check if PostgreSQL is running (Docker)
docker ps | grep postgres

# Check if PostgreSQL is running (local)
brew services list | grep postgresql
# or
sudo systemctl status postgresql

# Start service
docker-compose up -d
# or
brew services start postgresql@18
# or
sudo systemctl start postgresql
```

### Authentication Failed

**Error**: `psql: error: FATAL: password authentication failed for user "postgres"`

**Solutions**:
1. Verify password in `.env` matches database password
2. Check `pg_hba.conf` authentication method (should be `md5` or `scram-sha-256`)
3. For Docker: default password is `postgres` (set in docker-compose.yml)
4. Reset password if needed:
   ```sql
   ALTER USER postgres WITH PASSWORD 'new_password';
   ```

### pgvector Extension Not Found

**Error**: `ERROR: could not open extension control file ".../vector.control": No such file or directory`

**Solutions**:
1. Verify pgvector is installed: `psql -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';" postgres`
2. For Docker: Use `pgvector/pgvector` image (not plain `postgres`)
3. For local: Reinstall pgvector from source or package manager

### Port Already in Use

**Error**: `bind: address already in use` or `port 5432 is already allocated`

**Solutions**:
```bash
# Find process using port 5432
lsof -i :5432

# Stop conflicting PostgreSQL instance
brew services stop postgresql@15  # if older version running
# or kill the process

# Or change port in docker-compose.yml:
# ports:
#   - "5433:5432"  # External:Internal
# (and update DB_PORT in .env to 5433)
```

### Disk Space Issues

**Error**: `could not extend file ... No space left on device`

**Solutions**:
```bash
# Check disk usage
df -h

# For Docker, clean up old volumes
docker volume prune

# Remove unused containers/images
docker system prune -a
```

---

## Performance Tuning (Optional)

For large datasets (5000+ entities), consider these PostgreSQL settings:

**Edit `postgresql.conf`:**
```bash
# Find config file
psql -c "SHOW config_file;" postgres

# Edit
nano $(psql -t -c "SHOW config_file;" postgres)
```

**Recommended settings for development:**
```ini
# Memory settings (adjust based on available RAM)
shared_buffers = 256MB              # Default: 128MB
effective_cache_size = 1GB          # Default: 4GB (set to ~1/2 of RAM)
work_mem = 16MB                     # Default: 4MB
maintenance_work_mem = 128MB        # Default: 64MB

# Checkpoint settings
checkpoint_timeout = 15min          # Default: 5min
max_wal_size = 1GB                  # Default: 1GB

# Query planner
random_page_cost = 1.1              # Default: 4.0 (for SSD)
effective_io_concurrency = 200      # Default: 1 (for SSD)

# Logging (for debugging)
log_min_duration_statement = 1000   # Log queries > 1 second
```

**Restart PostgreSQL after changes:**
```bash
# Docker
docker-compose restart

# Local (macOS)
brew services restart postgresql@18

# Local (Linux)
sudo systemctl restart postgresql
```

---

## Next Steps

1. ✅ PostgreSQL 18 installed and running
2. ✅ Database `legacy_docs` created
3. ✅ pgvector extension enabled
4. ✅ Connection verified
5. ⏭️ **Next**: Run build script to create tables and populate data
   ```bash
   uv run python -m build_script.build_mcp_db
   ```

---

## Summary Commands

**Quick Setup (Docker)**:
```bash
cd .ai/mcp/doc_server/
docker-compose up -d
docker exec -it mcp-postgres psql -U postgres -d legacy_docs -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo "✓ PostgreSQL ready for build script"
```

**Quick Test**:
```bash
psql -h localhost -U postgres -d legacy_docs -c "SELECT version();"
psql -h localhost -U postgres -d legacy_docs -c "SELECT '[1,2,3]'::vector;"
```

**Clean Slate** (remove all data):
```bash
docker-compose down -v
docker-compose up -d
docker exec -it mcp-postgres psql -U postgres -d legacy_docs -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/18/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- Docker Compose Reference: [docker-compose.yml](docker-compose.yml)

---

## MCP Server

### Running the Server

```bash
cd .ai/mcp/doc_server/
uv run python -m server.server
```

The server runs over stdio and communicates via the MCP JSON-RPC protocol.

### Available Tools (20)

**Entity Resolution & Lookup (5)**
| Tool | Description |
|------|-------------|
| `resolve_entity` | Resolve entity name to ranked candidates via multi-stage pipeline |
| `get_entity` | Fetch full entity details by ID or signature |
| `get_source_code` | Retrieve source code with optional context lines |
| `list_file_entities` | List all entities defined in a source file |
| `get_file_summary` | Get file-level statistics and top entities |

**Search (1)**
| Tool | Description |
|------|-------------|
| `search` | Hybrid semantic + keyword search with exact match boost |

**Graph Navigation (6)**
| Tool | Description |
|------|-------------|
| `get_callers` | Get functions that call this entity (backward traversal) |
| `get_callees` | Get functions called by this entity (forward traversal) |
| `get_dependencies` | Get filtered dependencies by relationship type and direction |
| `get_class_hierarchy` | Get base classes and derived classes |
| `get_related_entities` | Get all direct neighbors grouped by relationship type |
| `get_related_files` | Find related files via include relationships |

**Behavioral Analysis (3)**
| Tool | Description |
|------|-------------|
| `get_behavior_slice` | Compute transitive call cone with capabilities touched, globals, side effects |
| `get_state_touches` | Analyze direct and transitive global variable usage |
| `get_hotspots` | Find architectural hotspots ranked by metric (fan_in, fan_out, bridge, underdocumented) |

**Capability System (5)**
| Tool | Description |
|------|-------------|
| `list_capabilities` | List all 30 capability groups with metadata |
| `get_capability_detail` | Get detailed capability info with dependencies and entry points |
| `compare_capabilities` | Compare capabilities: shared/unique dependencies, bridge entities |
| `list_entry_points` | List entry points (do_*, spell_*, spec_*) filterable by capability |
| `get_entry_point_info` | Analyze which capabilities an entry point exercises |

### Available Resources (5)

| URI | Description |
|-----|-------------|
| `legacy://capabilities` | List all capability groups |
| `legacy://capability/{name}` | Get capability detail |
| `legacy://entity/{entity_id}` | Get full entity details |
| `legacy://file/{path}` | List entities in a file |
| `legacy://stats` | Server statistics |

### Available Prompts (4)

| Prompt | Description |
|--------|-------------|
| `explain_entity` | Comprehensive entity explanation workflow |
| `analyze_behavior` | Behavioral analysis with call cone and side effects |
| `compare_entry_points` | Compare entry points for shared dependencies |
| `explore_capability` | Explore a capability group's architecture |

### Running Tests

```bash
# Contract tests (no live DB required)
uv run pytest tests/test_tools.py -v

# Integration tests (requires running PostgreSQL)
uv run python integration_test_phase678.py

# MCP protocol test (requires running PostgreSQL)
uv run python test_mcp_protocol.py
```
