#!/usr/bin/env python3

import os
import json
import subprocess
from clang import cindex
from pathlib import Path
import argparse

# Adjust this path as needed for your system
cindex.Config.set_library_file("/opt/local/libexec/llvm-20/lib/libclang.dylib")

parser = argparse.ArgumentParser(description="Debug Clang parse of a single source file.")
parser.add_argument("compile_commands", help="Path to compile_commands.json")
parser.add_argument("file", help="Path to a source file to test")
args = parser.parse_args()

compile_commands_path = Path(args.compile_commands).resolve()
file_path = Path(args.file).resolve()

with open(compile_commands_path) as f:
    compile_commands = json.load(f)

# Find the entry matching the file
entry = next((e for e in compile_commands if Path(e["file"]).resolve() == file_path), None)

if not entry:
    print(f"[!] File not found in compile_commands.json: {file_path}")
    exit(1)

# Extract arguments and clean them
args_list = entry["arguments"][1:-1]  # remove the compiler
args_list = [arg for arg in args_list if not str(file_path).endswith(str(Path(arg).resolve()))]
if "-o" in args_list:
    i = args_list.index("-o")
    del args_list[i:i+2]
if "-c" in args_list:
    args_list.remove("-c")

print(f"[+] File: {file_path}")
print(f"[+] Working directory: {entry['directory']}")
print(f"[+] Arguments:")
for arg in args_list:
    print(f"    {arg}")

# Try clang -fsyntax-only as shell sanity test
try:
    print("[+] Running clang -fsyntax-only for shell sanity check...")
    result = subprocess.run(
        ["clang++", "-fsyntax-only"] + args_list + [str(file_path)],
        cwd=entry["directory"],
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode != 0:
        print("[!] clang++ reported errors:")
        print(result.stderr)
    else:
        print("[✓] clang++ accepted the file.")
except Exception as e:
    print(f"[!] clang++ sanity check failed: {e}")

# Now try libclang parse
index = cindex.Index.create()
try:
    tu = index.parse(
        path=str(file_path),
        args=args_list,
        options=0
    )
    print("[✓] libclang successfully parsed the translation unit.")
    print("[+] Top-level declarations:")
    for c in tu.cursor.get_children():
        print(f"  - {c.kind.name}: {c.spelling} ({c.location.file}:{c.location.line})")
except Exception as e:
    print(f"[!] libclang parse failed: {e}")