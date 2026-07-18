# Majordomo — Devpost submission copy

*Qwen Cloud Global AI Hackathon · MemoryAgent track. Paste-ready. Deadline Sun Jul 20, 2:00 PM PT.*

---

## Project name
**Majordomo — the concierge that never forgets**

## Tagline (one line)
A guest-service agent with **governed** persistent memory — it dedupes, detects contradictions, and supersedes stale preferences with provenance, then *proves* its recall gets more accurate across sessions.

## Elevator pitch (≈ the "what & why" box)
Naive memory agents append everything and retrieve by similarity, so over many
sessions their store fills with duplicates and contradicted facts and recall
quality *degrades with experience* — the guest who switched from cappuccino to
matcha keeps getting cappuccino, because three stale memories outvote one
current one. **More memory makes the agent worse.**

Majordomo governs the memory lifecycle instead of just growing it. Every
remembered fact runs a Qwen-powered pipeline — **extract → dedupe/reinforce →
contradiction-supersede → hybrid recall** — and the claim is *measured, not
asserted*: a built-in eval runs returning-guest personas through Majordomo and
an append-only baseline, quizzing each with a Qwen judge after every stay.
**When a guest changes a preference mid-history, the baseline's accuracy drops
to 0.8 while Majordomo holds 1.0.**

## The problem
Memory is the difference between an assistant and a stranger who reintroduces
itself every session. But "remember everything" is a trap: unbounded append
turns recall into a popularity contest between stale and current facts.
Governance — knowing what to reinforce, retire, and supersede — is the actual
hard part, and it's where hackathon memory agents are weakest.

## How it works
1. **EXTRACT** — Qwen (`qwen3.7-plus`, JSON mode) distills atomic, durable
   guest facts from the transcript; transient chatter is dropped.
2. **DEDUPE** — embedding similarity ≥ 0.90 → reinforce the existing memory
   instead of storing a duplicate (reinforcement later boosts recall).
3. **SUPERSEDE** — same topic, changed fact (gray-zone similarity) → a Qwen
   contradiction check (`qwen3.7-max` as judge). *"always coffee"* and *"never
   coffee"* embed nearly identically, so even near-duplicates get judged.
   Contradicted memories are **retired with provenance** — kept for audit,
   excluded from recall, reason recorded. Nothing is silently deleted.
4. **RECALL** — hybrid score = `cosine × importance × recency × reinforcement`
   → the memories that are relevant, current, *and* repeatedly confirmed.

## Why it's different (the recurring differentiator)
Every entry ships a **measurable eval**, not a demo anecdote. `majordomo eval`
runs scripted personas through governed and append-only memory and plots the
governed-vs-naive accuracy curve. Judges almost never see quantified
self-evaluation — here it's the headline.

## Built with
`Qwen Cloud` · `qwen3.7-plus` · `qwen3.7-max` · `text-embedding-v4` ·
`Alibaba Cloud Model Studio (DashScope)` · `Alibaba Cloud Function Compute` ·
`Python` · `httpx` · `SQLite` · `Apache-2.0`

## Alibaba Cloud / Qwen usage (proof)
- **Inference on Alibaba Cloud Model Studio (DashScope):** all chat, judge, and
  embedding calls hit `dashscope-intl.aliyuncs.com`. Proof file:
  `src/majordomo/llm.py` (`QwenClient`).
- **Deployed on Alibaba Cloud Function Compute** (Singapore, `ap-southeast-1`)
  as a web function with a public endpoint. Proof files: `fc/index.py`,
  `fc/s.yaml`. Live: `GET /health` returns the FC region + identity; `POST
  /chat` runs a real governed-memory turn.

## Repository
`https://github.com/<org>/majordomo` — public, **Apache-2.0** (LICENSE at root).

## Disclosure of pre-existing work (Devpost rule compliance)
Majordomo was **built new during the submission period** (repo initialized Jul
13, 2026). It re-implements two architectural patterns the author developed in
his own earlier Apache-2.0 project, **NexusVenue**: (1) an LLM-as-judge
evaluation harness and (2) a deterministic offline "mock" backend for testing
without API keys. **No code was copied verbatim** — the patterns were rebuilt
for the memory-governance domain. All third-party libraries are open-source and
credited.

## What's next
ApsaraDB RDS for the memory ledger (SQLite today), multi-tenant guest
isolation, and a live reinforcement dashboard.

---

### Judging-rubric self-check (innovation 30 / tech 30 / value 25 / presentation 15)
- **Innovation:** governance (supersede-with-provenance) instead of append-only memory; contradiction detection on near-identical embeddings.
- **Technical depth:** 4-stage governed pipeline, hybrid recall scoring, dual-backend (real Qwen / deterministic mock), FC deployment, eval harness with a Qwen judge.
- **Value:** memory that *improves* with use is the unlock for any long-lived assistant; hotel concierge is the demo, the engine is domain-agnostic.
- **Presentation:** one quantified headline (1.0 vs 0.8), arch diagram, <3-min video, live endpoint.
