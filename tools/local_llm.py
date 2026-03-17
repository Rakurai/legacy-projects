#!/usr/bin/env python3
"""
local_llm.py - tiny CLI wrapper around Ollama for "micro-agent" tasks.

Usage examples:
  echo "Summarize this diff:" | python tools/local_llm.py --model qwen2.5-coder:7b
  python tools/local_llm.py --model qwen2.5-coder:7b --prompt "Generate a regex for ISO dates"
  python tools/local_llm.py --stdin --system "You are a terse coding assistant." --temperature 0.2
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Optional


def run_ollama(model: str, prompt: str, *, system: Optional[str], temperature: Optional[float]) -> str:
    """
    Prefer `ollama run` for broad compatibility. We pass a composed prompt that includes system guidance.
    """
    # Compose a single prompt; Ollama CLI doesn't have a universal --system flag across versions.
    if system:
        full_prompt = f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}\n"
    else:
        full_prompt = prompt

    cmd = ["ollama", "run", model]

    # Environment knobs (some Ollama builds respect these; harmless if ignored)
    env = os.environ.copy()
    if temperature is not None:
        env["OLLAMA_TEMPERATURE"] = str(temperature)

    try:
        proc = subprocess.run(
            cmd,
            input=full_prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
    except FileNotFoundError:
        raise RuntimeError("Could not find `ollama` on PATH. Install Ollama or fix PATH.") from None

    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"ollama failed (code {proc.returncode}): {err}")

    return proc.stdout.decode("utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5-coder:7b", help="Ollama model name, e.g. qwen2.5-coder:7b")
    ap.add_argument("--prompt", default=None, help="Prompt text (if omitted, use --stdin or remaining args)")
    ap.add_argument("--stdin", action="store_true", help="Read prompt from stdin")
    ap.add_argument("--system", default="You are a concise coding assistant. Output only what is asked.",
                    help="System-style instruction to prepend.")
    ap.add_argument("--temperature", type=float, default=0.2, help="Sampling temperature (if supported).")
    ap.add_argument("--json", action="store_true",
                    help="Wrap output as JSON: {\"model\":..., \"output\":...} (useful for scripts).")

    # Allow: local_llm.py ... "prompt words here"
    ap.add_argument("rest", nargs="*", help="Prompt (alternative to --prompt)")

    args = ap.parse_args()

    if args.prompt is not None:
        prompt = args.prompt
    elif args.stdin:
        prompt = sys.stdin.read()
    elif args.rest:
        prompt = " ".join(args.rest)
    else:
        ap.error("Provide --prompt, or --stdin, or trailing prompt text.")

    prompt = prompt.strip()
    if not prompt:
        ap.error("Prompt is empty.")

    try:
        out = run_ollama(args.model, prompt, system=args.system, temperature=args.temperature)
    except Exception as e:
        print(str(e), file=sys.stderr)
        return 2

    out = out.strip()
    if args.json:
        print(json.dumps({"model": args.model, "output": out}, ensure_ascii=False))
    else:
        print(out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
