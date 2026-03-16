#!/usr/bin/env python3

import subprocess
import os
import re
import json
import networkx as nx
from networkx.readwrite import json_graph
from pathlib import Path

workspace = Path(__file__).resolve().parents[2]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TAGS_FILE = PROJECT_ROOT / ".ai/context/internal/tags"
CSCOPE_WORKDIR = PROJECT_ROOT / ".ai/context/internal"
GRAPH_OUTPUT = PROJECT_ROOT / ".ai/context/internal/call_graph.json"

SOURCE_DIRS = ["src",]
EXCLUDE_DIRS = []

def run_ctags():
    print("[+] Running ctags...")
    for source_dir in SOURCE_DIRS:
        subprocess.run([
            "uctags", "-R",
            "--languages=C,C++",
            "--fields=+nks", "--extras=+q",
            "--c-kinds=+pxmstde", "--c++-kinds=+pxclmstde",
            "-f", TAGS_FILE,
            str(PROJECT_ROOT / source_dir)
        ], check=True)


def run_cscope():
    print("[+] Generating cscope.files...")
    with open(CSCOPE_WORKDIR / "cscope.files", "w") as f:
        for source_dir in SOURCE_DIRS:
            for root, dirs, files in os.walk(PROJECT_ROOT / source_dir):
                for file in files:
                    if file.endswith((".c", ".cc", ".cpp", ".h", ".hh", ".hpp")):
                        f.write(os.path.join(root, file) + "\n")
    print("[+] Running cscope...")
    subprocess.run(["cscope", "-b", "-q", "-k", "-i", str(CSCOPE_WORKDIR / "cscope.files")], check=True)

tag_pattern = re.compile(r'^(?P<name>[^\t]+)\t(?P<file>[^\t]+)\t(?P<excmd>.+?);"[\t ](?P<kind>\w)(?:\t|$)')

def parse_tags():
    raw_entities = {}
    with open(TAGS_FILE, "r") as f:
        for line in f:
            if line.startswith("!"):
                continue
            match = tag_pattern.match(line)
            if not match:
                continue
            name = match.group("name").strip()
            file = match.group("file").strip()
            excmd = match.group("excmd").strip()
            kind = match.group("kind").strip()
            line_match = re.search(r'line:(\d+)', line)
            line_num = int(line_match.group(1)) if line_match else None

            # Only include real definitions
            if kind in {"f", "s", "c", "m", "t", "e"}:
                raw_entities.setdefault(name, []).append({
                    "file": file,
                    "line": line_num,
                    "kind": kind,
                    "excmd": excmd
                })

    # Now prioritize per entity
    entities = {}

    for name, entries in raw_entities.items():
        # Prefer source file definitions
        def_score = lambda e: (
            1 if e["file"].endswith(('.c', '.cpp', '.cc', '.cxx')) else 0,  # source file gets priority
            1 if e["kind"] == "f" else 0,  # definition gets priority
        )
        best = sorted(entries, key=def_score)[-1]
        entities[name] = best

    # Save entities for manual review
    with open(PROJECT_ROOT / ".ai/context/internal/raw_entities.json", "w") as ef:
        json.dump(raw_entities, ef, indent=2)
    with open(PROJECT_ROOT / ".ai/context/internal/entities.json", "w") as ef:
        json.dump(entities, ef, indent=2)

    return entities


def build_dependency_graph(entities):
    print("[+] Building call graph with cscope lookups...")
    graph = nx.DiGraph()
    graph.add_nodes_from(entities.keys())

    calls = {}

    for func in entities:
        try:
            # Ensure cscope runs in the project root where cscope.out is generated
            result = subprocess.run(
                ["cscope", "-L", "-3", func],
                cwd=CSCOPE_WORKDIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, check=False
            )
            for line in result.stdout.strip().split("\n"):
                parts = line.strip().split(None, 3)  # Split into max 4 parts
                if len(parts) < 3:
                    continue
                file_path, caller_func, line_num = parts[:3]
                if caller_func in entities:
                    calls.setdefault(func, set()).add(caller_func)
                    graph.add_edge(caller_func, func)
        except Exception as e:
            print(f"Warning: failed cscope query for {func}: {e}")

    # Append cscope results to a file for manual review
    with open(PROJECT_ROOT / ".ai/context/internal/cscope_lookup.json", "w") as f:
        json.dump({k:list(v) for k, v in calls.items()}, f, indent=2)
    return graph


def save_graph(graph, filename):
    print(f"[+] Saving graph to {filename}")
    data = json_graph.node_link_data(graph)
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    run_ctags()
    run_cscope()
    entities = parse_tags()
    graph = build_dependency_graph(entities)
    save_graph(graph, GRAPH_OUTPUT)
    print(f"[✓] Done. Call graph saved to {GRAPH_OUTPUT}")
