#!/usr/bin/env python3
"""
Script to generate projects/doc_gen/files_old.json as a summary of all legacy source/header files.
Scans src/ and stored_src/ recursively for .h, .hh, .c, .cpp, .cc, .hpp files.
Outputs: projects/doc_gen/files_old.json as a JSON summary.
If the output file exists, it will be loaded and updated with any new files.
"""
import os
import pathlib
import json

ROOTS = ["src"]
EXTS = {".h", ".hh", ".hpp", ".c", ".cpp", ".cc"}
OUTPUT = "projects/doc_gen/files_old.json"

workspace = pathlib.Path(__file__).resolve().parents[2]
output_path = workspace / OUTPUT

# Load existing file if it exists
existing_data = {}
if output_path.exists():
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {OUTPUT}, creating a new file.")

# Scan for all source files
files = {}
for root in ROOTS:
    root_path = workspace / root
    for dirpath, _, filenames in os.walk(root_path):
        for fname in filenames:
            ext = pathlib.Path(fname).suffix.lower()
            if ext in EXTS:
                fpath = pathlib.Path(dirpath) / fname
                relpath = f"/{fpath.relative_to(workspace)}"
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = sum(1 for _ in f)
                except Exception:
                    lines = 0
                    print(f"Warning: Could not count lines in {relpath}")
                
                # Create or update entry
                if relpath in existing_data:
                    # Preserve existing category and summary
                    files[relpath] = {
                        "loc": lines,
                        "category": existing_data[relpath].get("category"),
                        "summary": existing_data[relpath].get("summary")
                    }
                else:
                    # New file entry
                    files[relpath] = {
                        "loc": lines,
                        "category": None,
                        "summary": None
                    }

# Write output JSON file with pretty formatting
with open(output_path, 'w', encoding='utf-8') as out:
    json.dump(files, out, indent=2)

print(f"Generated {OUTPUT} with {len(files)} files")
