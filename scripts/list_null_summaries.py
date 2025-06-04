#!/usr/bin/env python3

import json
import os
import sys
from pathlib import Path

def main():
    # Get the root directory of the project
    script_path = Path(__file__)
    ai_dir = script_path.parent.parent
    files_old_path = ai_dir / "context" / "files_old.json"
    
    # Check if the file exists
    if not files_old_path.exists():
        print(f"Error: {files_old_path} not found.")
        sys.exit(1)
    
    # Read the JSON file
    try:
        with open(files_old_path, "r") as f:
            files_old = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Find entries with null summaries
    null_summaries = []
    
    for filepath, info in files_old.items():
        if info.get("summary") is None:
            null_summaries.append((filepath, info.get("loc", "?"), info.get("category", "None")))
    
    # Display results
    if null_summaries:
        print(f"Found {len(null_summaries)} files with null summary:")
        print("=" * 40)
        
        for filepath, loc, category in sorted(null_summaries):
            print(f"{filepath}")
        
        print("\nTotal: {0} files with null summary".format(len(null_summaries)))
    else:
        print("No files with null summary found!")

if __name__ == "__main__":
    main()
