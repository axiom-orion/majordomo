# Security policy

## Supported versions

Only the `main` branch is supported. There are no maintained release branches; fixes land on `main`.

## Reporting a vulnerability

Please report security issues privately, not in public issues or pull requests:

- Use GitHub's private vulnerability reporting on this repository (**Security → Report a vulnerability**), or
- Email **security@vorion.org**.

Include what you found, how to reproduce it, and the impact you expect. We aim to reply within 7 days.

## Scope

Majordomo is a concierge agent with persistent guest memory. It calls Qwen models over HTTP, stores memories in SQLite, can start the BAI events MCP server as a subprocess, and has an optional Function Compute deployment (`fc/`). Relevant reports include:

- **API keys and credentials** — anything that leaks `QWEN_API_KEY` or the Function Compute credentials (for example into logs, error messages, responses or the memory store), or a key committed to the repo. Keys belong in `.env` (git-ignored) or the deployment's environment, never in code.
- **Prompt injection** — guest messages are sent to the LLM and extracted into long-lived memories that are recalled into later prompts. Input that makes the agent ignore its instructions, leak other guests' memories, or plant memories that change later behaviour is in scope.
- **Memory integrity** — bypassing the governance rules (supersede with a recorded reason, nothing deleted), or reading or writing another guest's memories.
- **The deployed HTTP endpoints** — `/chat` and `/remember` in `fc/index.py` take a caller-supplied `guest_id`; access-control and input-validation issues there.
- **File writes and subprocesses** — writes outside the configured database and `data/` directory, and anything that lets untrusted input influence the MCP subprocess command (`BAI_MCP_CMD` / `BAI_MCP_ARGS` / `BAI_MCP_CWD`).

Out of scope: the Qwen / Alibaba Cloud services themselves, and the separate bai-mcp server (report those to their own maintainers).
