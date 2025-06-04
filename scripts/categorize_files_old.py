import os
import json
import glob
import re

DOCS_DIR = ".ai/docs/components"
FILES_OLD_JSON = ".ai/context/files_old.json"
OUTPUT_MD = ".ai/context/files_old.md"

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_docs():
    docs = {}
    for path in glob.glob(os.path.join(DOCS_DIR, "*.md")):
        with open(path, "r", encoding="utf-8") as f:
            docs[path] = f.read()
    return docs

def find_category_for_file(filepath, docs):
    filename = os.path.basename(filepath)
    found = []
    for doc_path, content in docs.items():
        if filename in content:
            found.append(doc_path)
    return found

def main():
    files = load_json(FILES_OLD_JSON)
    docs = load_docs()
    print(f"Loaded {len(files)} files from {FILES_OLD_JSON}")
    print(f"Loaded {len(docs)} documentation files from {DOCS_DIR}")
    errors = []
    categorized = {}

    for path in files:
        entry = files[path]
        entry['path'] = path  # Store the original path
        found = find_category_for_file(path, docs)
        if len(found) == 0:
            errors.append(f"Not found: {path}")
            continue
        if len(found) > 1:
            errors.append(f"Ambiguous: {path} found in {found}")
            continue
        # Assign category based on doc filename
        doc_filename = os.path.splitext(os.path.basename(found[0]))[0]
        entry["category"] = doc_filename
        categorized.setdefault(doc_filename, []).append(entry)

    # Output errors
    if errors:
        print("ERRORS:")
        for e in errors:
            print(e)
        print("----")

    # Output markdown
    with open(OUTPUT_MD, "w", encoding="utf-8") as out:
        out.write("# Legacy C/C++ File Directory\n")
        out.write("This directory lists all legacy source/header files, grouped by system component. Each file is categorized based on references in the component documentation.\n")
        out.write("---\n")
        # Order categories for readability
        order = [
            "character_system", "object_system", "world_system", "game_mechanics",
            "interaction_systems", "user_experience", "admin_systems", "help_system", "infrastructure"
        ]
        for cat in order:
            entries = categorized.get(cat, [])
            if not entries:
                continue
            # Title
            title = cat.replace("_", " ").title()
            doc_link = f".ai/docs/components/{cat}.md"
            out.write(f"## {title} System [link]({doc_link})\n")
            # Group by header/implementation/resource
            headers = [e for e in entries if e["path"].endswith(".hh") or e["path"].endswith(".h")]
            impls = [e for e in entries if e["path"].endswith(".cc") or e["path"].endswith(".cpp") or e["path"].endswith(".c")]
            others = [e for e in entries if e not in headers and e not in impls]
            if headers:
                out.write("### Header Files\n")
                for e in headers:
                    out.write(f"- `{e['path']}` - {e.get('summary','')}\n")
            if impls:
                out.write("### Implementation Files\n")
                for e in impls:
                    out.write(f"- `{e['path']}` - {e.get('summary','')}\n")
            if others:
                out.write("### Resources\n")
                for e in others:
                    out.write(f"- `{e['path']}` - {e.get('summary','')}\n")
            out.write("\n")

if __name__ == "__main__":
    main()
