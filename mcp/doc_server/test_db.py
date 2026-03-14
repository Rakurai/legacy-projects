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
        database=os.getenv("DB_NAME", "legacy_og_docs"),
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
