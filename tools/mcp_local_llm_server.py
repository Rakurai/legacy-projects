from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("local-llm")

def _run_local_llm(prompt: str, model: str, temperature: float) -> str:
    """
    Replace this with:
      - direct Ollama HTTP call, OR
      - your existing tools/local_llm.py, OR
      - LM Studio local endpoint, etc.
    """
    # Example: call your existing script
    # Expected to print raw model text to stdout.
    cmd = [
        "python",
        "tools/local_llm.py",
        "--model",
        model,
        "--temperature",
        str(temperature),
        "--prompt",
        prompt,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"local_llm.py failed (exit {proc.returncode})\n"
            f"STDERR:\n{proc.stderr}\nSTDOUT:\n{proc.stdout}"
        )
    return proc.stdout.strip()


@mcp.tool()
def local_llm_codegen(
    prompt: str,
    model: str = "qwen2.5-coder:7b",
    temperature: float = 0.1,
    response_format: str = "unified_diff",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate code or edits using a local LLM.

    Expected usage:
    - Copilot supplies a prompt + any relevant file snippets in `context`.
    - The local model returns either a unified diff (preferred) or structured JSON.
    """

    # Build a single prompt that biases the model to produce a patch
    system_instructions = (
        "You are a code-editing tool.\n"
        "Return ONLY a unified diff patch if possible.\n"
        "No prose before or after the diff.\n"
        "If you cannot produce a diff, return JSON with keys: "
        "{'files': [{'path':..., 'content':...}], 'notes':...}.\n"
    )

    full_prompt = system_instructions + "\nUSER REQUEST:\n" + prompt

    if context:
        full_prompt += "\n\nCONTEXT (json):\n" + json.dumps(context, indent=2)

    raw = _run_local_llm(full_prompt, model=model, temperature=temperature)

    return {
        "format": response_format,
        "output": raw,
        "model": model,
    }


if __name__ == "__main__":
    mcp.run()
