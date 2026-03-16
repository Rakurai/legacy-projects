#!/usr/bin/env python3
"""Regenerate embeddings_cache.pkl using OpenAI text-embedding-3-large."""
import sys
import pickle
from pathlib import Path

CLUSTERING_DIR = Path(__file__).resolve().parent / "clustering"
sys.path.insert(0, str(CLUSTERING_DIR))

import clustering.doc_db as ddb
import openai_embeddings as oai_emb

EMBEDDING_CACHE = CLUSTERING_DIR / "embeddings_cache.pkl"

# Load doc_db
db = ddb.DocumentDB()
db.load(ddb.DOC_DB_PATH)
print(f"DocumentDB: {db.count()} entities")

# Collect texts
texts: list[str] = []
keys: list[str] = []
for cid, sig, doc in db.items():
    text = doc.to_doxygen()
    if text:
        texts.append(text)
        keys.append(doc.mid)

print(f"Encoding {len(texts)} entities with {oai_emb.MODEL}...")
vectors = oai_emb.embed_texts(texts, show_progress=True)
all_embeddings = {k: v for k, v in zip(keys, vectors)}

with open(EMBEDDING_CACHE, "wb") as f:
    pickle.dump(all_embeddings, f)
print(f"Cached {len(all_embeddings)} embeddings ({vectors.shape[1]}d) to {EMBEDDING_CACHE}")
print(f"File size: {EMBEDDING_CACHE.stat().st_size / 1024 / 1024:.1f} MB")
