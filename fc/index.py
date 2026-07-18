"""Alibaba Cloud Function Compute (FC 3.0) web function.

═══════════════════════════════════════════════════════════════════════════
PROOF OF ALIBABA CLOUD USAGE — Qwen Cloud Global AI Hackathon requirement
═══════════════════════════════════════════════════════════════════════════
This file is the linked "code file demonstrating use of Alibaba Cloud services
and APIs." It uses Alibaba Cloud two independent ways:

  1. DEPLOY  — it is deployed as an Alibaba Cloud Function Compute *web
     function* (custom runtime, HTTP-triggered; see s.yaml). FC injects the
     Alibaba Cloud identity (ALIBABA_CLOUD_ACCESS_KEY_ID / _SECRET /
     _SECURITY_TOKEN, FC_REGION) into this process's environment.
  2. INFERENCE — every chat/judge/embedding call runs on **Alibaba Cloud
     Model Studio (DashScope)** at dashscope-intl.aliyuncs.com. That happens
     inside Majordomo's own client — see ../src/majordomo/llm.py (QwenClient),
     the second proof file.

The endpoints below wrap Majordomo's real governed-memory engine unchanged —
this is the actual product running on Alibaba Cloud, not a demo shim.
"""

import os

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from majordomo.agent import Session
from majordomo.engine import MemoryEngine

# One governed engine for the process. LLM_BACKEND=qwen -> QwenClient, which
# talks to Alibaba Cloud Model Studio (DashScope). Set via FC env (see s.yaml).
_engine = MemoryEngine()
_sessions: dict[str, Session] = {}

app = FastAPI(title="Majordomo on Alibaba Cloud Function Compute")


class ChatIn(BaseModel):
    guest_id: str
    session_id: str
    message: str


class RememberIn(BaseModel):
    guest_id: str
    session_id: str
    transcript: str


@app.get("/health")
def health():
    """Surfaces the FC-injected Alibaba Cloud identity as live, clickable proof."""
    return {
        "ok": True,
        "platform": "alibaba-cloud-function-compute",
        "region": os.environ.get("FC_REGION", "ap-southeast-1"),
        "inference": "alibaba-cloud-model-studio (dashscope-intl.aliyuncs.com)",
        "has_alibaba_cloud_creds": bool(os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")),
    }


@app.post("/chat")
def chat(body: ChatIn):
    """One guest turn: recall governed memory, respond grounded in it.

    The reply is produced by a Qwen model on Alibaba Cloud Model Studio."""
    sess = _sessions.setdefault(
        body.session_id, Session(body.guest_id, body.session_id, _engine)
    )
    reply, recalled = sess.ask(body.message)
    return {"reply": reply, "recalled": [m["content"] for m in recalled]}


@app.post("/remember")
def remember(body: RememberIn):
    """Distill a transcript into governed memory (extract -> dedupe ->
    supersede -> store), returning what changed."""
    report = _engine.remember(body.guest_id, body.transcript, body.session_id)
    return {
        "stored": report.stored,
        "reinforced": report.reinforced,
        "superseded": report.superseded,
    }


if __name__ == "__main__":
    # FC web functions must listen on 0.0.0.0:9000.
    uvicorn.run(app, host="0.0.0.0", port=9000)
