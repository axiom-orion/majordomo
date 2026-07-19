# Majordomo — Devpost submission copy

*Qwen Cloud Global AI Hackathon · MemoryAgent track. Paste-ready. Deadline Sun Jul 20, 2:00 PM PT.*

---

## Project name
**Majordomo — the memory agent that forgets with receipts**

## Tagline (one line)
Persistent memory that doesn't just remember — it retires the preferences you've changed, keeps them auditable with a recorded reason, and keeps recall clean so every decision runs on current facts.

## Elevator pitch
The MemoryAgent track asks for *"efficient memory storage and retrieval, timely
forgetting of outdated information, and recalling critical memories within
limited context windows."* Most memory agents do the opposite: they append
everything and retrieve by similarity, so their store fills with duplicates and
**contradicted** facts. Ask the concierge for your morning drink after you
switched from cappuccino to matcha, and an append-only agent is still carrying
two stale "cappuccino" memories into every decision.

Majordomo governs the memory lifecycle instead of just growing it — **extract →
dedupe/reinforce → contradiction-supersede → hybrid recall** — all Qwen-powered.
And it proves the behavior honestly:

> **Verified live on Qwen** (guest switches cappuccino → matcha):
> Majordomo surfaces **0** stale memories into recall and carries **7** active rows.
> The append-only baseline surfaces **2** contradicted "cappuccino" memories and carries **14**.

An honest finding we lead with: a capable model *answers* correctly either way —
so we don't claim a fake accuracy win. The real, measurable difference is
**recall hygiene**: the append-only agent decides on a store full of
contradictions with no audit trail; Majordomo retires the stale fact with a
recorded reason and keeps the limited recall window clean.

## How it works
1. **EXTRACT** — `qwen3.7-plus` (JSON mode) distills atomic, durable guest facts.
2. **DEDUPE** — similarity ≥ 0.90 → reinforce the existing memory, don't duplicate.
3. **SUPERSEDE** — same topic, changed fact → `qwen3.7-max` judges contradiction
   (*"always coffee"* and *"never coffee"* embed nearly identically, so even
   near-duplicates get judged). The stale memory is **retired with provenance** —
   kept for audit, excluded from recall, reason recorded.
4. **RECALL** — hybrid score = `cosine × importance × recency × reinforcement`.

## It also accumulates experience, not just preferences
The `policy_learning` path lets Majordomo learn a **standing rule from a one-off
incident** — a guest complains about a 6am wake-up call, and the agent forms and
applies a "never call before 9am" policy on later stays. That's the track's
*"autonomously accumulates experience → increasingly accurate decisions across
sessions"* — and our coverage metric rises stay over stay as it learns.

## Why it's different (the differentiator judges rarely see)
Every entry ships a **measurable eval**, run honestly. `majordomo eval` reports
stale-memory-in-recall (timely forgetting), active store size (efficient
storage), and coverage accuracy (increasingly accurate) — governed vs
append-only, across sessions. It runs deterministically offline (mock backend,
zero API cost, in CI) and the same behavior is verified live on Qwen.

## Built with
`Qwen Cloud` · `qwen3.7-plus` · `qwen3.7-max` · `text-embedding-v4` ·
`Alibaba Cloud Model Studio (DashScope)` · `Alibaba Cloud Function Compute` ·
`Python` · `httpx` · `SQLite` · `Apache-2.0`

## Alibaba Cloud / Qwen usage (proof)
- **Inference on Alibaba Cloud Model Studio (DashScope):** all chat, judge, and
  embedding calls hit `dashscope-intl.aliyuncs.com`. Proof file: `src/majordomo/llm.py`.
- **Deployed on Alibaba Cloud Function Compute** (Singapore, `ap-southeast-1`).
  Proof files: `fc/index.py`, `fc/s.yaml`. Live `/health` + `/chat`.

## Repository
`https://github.com/axiom-orion/majordomo` — public, **Apache-2.0** (LICENSE at root).

## Disclosure of pre-existing work (Devpost rule compliance)
Built new during the submission period (repo initialized Jul 13, 2026). It
re-implements two patterns from the author's earlier Apache-2.0 project
**NexusVenue** — an LLM-as-judge eval harness and a deterministic offline mock
backend — rebuilt for the memory-governance domain. **No code copied verbatim.**

## What's next
ApsaraDB RDS for the ledger (SQLite today), multi-tenant guest isolation, a live
reinforcement/supersession dashboard.

---

### Judging-rubric self-check (Technical 30 / Innovation 30 / Value 25 / Presentation 15)
- **Technical depth:** governed 4-stage pipeline, contradiction detection on near-identical embeddings, hybrid recall, dual backend (real Qwen / deterministic mock), honest eval harness with a Qwen judge.
- **Innovation:** governance with a provenance/audit trail — "forgetting with receipts" — not append-and-hope.
- **Value:** memory that forgets cleanly is the unlock for any long-lived assistant; hotel concierge is the demo, the engine is domain-agnostic.
- **Presentation:** one verified headline (0 vs 2 stale in recall; 7 vs 14 rows), architecture diagram, <3-min video, live endpoint.
