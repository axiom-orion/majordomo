"""Live Qwen Cloud smoke test — run the SECOND QWEN_API_KEY lands in .env.

Exercises the real QwenClient path (not mock): plain chat, JSON-mode chat, and
embeddings with the configured dimension. Catches the three things most likely
to break a real submission:

  1. Wrong model ID / endpoint / auth  -> HTTP 4xx, printed verbatim.
  2. Reasoning-model quirks on the OpenAI-compat endpoint (qwen3.7-* may emit
     <think> content or reject non-streaming) -> we see the raw content.
  3. Embedding dimension mismatch -> asserts len == settings.embed_dim (1024),
     which the memory store depends on.

Usage (from D:\\majordomo, with LLM_BACKEND=qwen and QWEN_API_KEY set):
    .\\.venv\\Scripts\\python.exe smoke_qwen.py
"""

import json
import sys

from majordomo.config import settings
from majordomo.llm import QwenClient


def line(s: str = "") -> None:
    print(s, flush=True)


def main() -> int:
    line("=== Majordomo · Qwen Cloud live smoke test ===")
    line(f"backend     : {settings.llm_backend}")
    line(f"base_url    : {settings.qwen_base_url}")
    line(f"chat_model  : {settings.chat_model}")
    line(f"judge_model : {settings.judge_model}")
    line(f"embed_model : {settings.embed_model}  (dim={settings.embed_dim})")
    line(f"key present : {bool(settings.qwen_api_key)}")
    line()

    if not settings.qwen_api_key:
        line("FAIL: QWEN_API_KEY is empty. Add it to .env, set LLM_BACKEND=qwen.")
        return 1

    try:
        client = QwenClient()
    except Exception as e:  # noqa: BLE001
        line(f"FAIL: could not build QwenClient: {e}")
        return 1

    failures = 0

    # 1. Plain chat -------------------------------------------------------
    try:
        out = client.chat(
            system="You are a concise assistant. Reply in one short sentence.",
            user="Say the single word: ready",
        )
        line("[1] chat OK")
        line(f"    -> {out!r}")
        if "<think>" in out.lower():
            line("    WARN: response contains <think> — reasoning model is leaking "
                 "chain-of-thought. May need enable_thinking:false or a non-reasoning model.")
    except Exception as e:  # noqa: BLE001
        failures += 1
        line(f"[1] chat FAIL: {e}")

    # 2. JSON-mode chat (governance pipeline relies on this) --------------
    try:
        out = client.chat(
            system="Return ONLY valid JSON.",
            user='Return {"ok": true} exactly.',
            json_mode=True,
        )
        parsed = json.loads(out)
        line(f"[2] json_mode OK -> {parsed}")
    except Exception as e:  # noqa: BLE001
        failures += 1
        line(f"[2] json_mode FAIL: {e}")
        line("    (If this 400s, DashScope may not honor response_format:json_object "
             "for this model — fall back to prompt-enforced JSON + json.loads.)")

    # 3. Judge model reachable -------------------------------------------
    try:
        out = client.chat(
            system="Reply with one word.",
            user="Say: judge",
            model=settings.judge_model,
        )
        line(f"[3] judge model OK -> {out!r}")
    except Exception as e:  # noqa: BLE001
        failures += 1
        line(f"[3] judge model FAIL: {e}")

    # 4. Embeddings + dimension contract ---------------------------------
    try:
        vecs = client.embed(["matcha not cappuccino", "window seat, quiet floor"])
        got = len(vecs[0])
        if got == settings.embed_dim:
            line(f"[4] embed OK -> {len(vecs)} vectors, dim={got} (matches config)")
        else:
            failures += 1
            line(f"[4] embed DIM MISMATCH -> got {got}, expected {settings.embed_dim}. "
                 f"Set EMBED_DIM={got} in .env (store depends on this).")
    except Exception as e:  # noqa: BLE001
        failures += 1
        line(f"[4] embed FAIL: {e}")

    line()
    if failures:
        line(f"RESULT: {failures} check(s) FAILED — fix before deploy/record.")
        return 1
    line("RESULT: ALL GREEN — Qwen path is live. Safe to run `demo`, `eval`, deploy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
