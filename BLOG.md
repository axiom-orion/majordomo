# Building Majordomo: memory that gets *more* accurate with use

*Build journal for the Qwen Cloud Global AI Hackathon — MemoryAgent track.*

## The bug in "just remember everything"

The default recipe for a memory agent is embarrassingly simple: extract facts
from each conversation, embed them, and at recall time return the most similar
ones. It demos beautifully on day one. It rots by day thirty.

Here's the failure I kept hitting. A guest tells the concierge, *"I drink
cappuccino."* Three visits later: *"I've switched to matcha."* A pure
append-and-retrieve store now holds **three** cappuccino memories and **one**
matcha memory. Ask it what to prepare, and similarity search hands back the
majority — cappuccino. The agent is confidently, provably wrong, and it got
*worse* precisely because it remembered *more*.

That's the thing worth solving. Not storage — **governance.**

## The four-stage pipeline

Majordomo runs every candidate memory through a Qwen-powered lifecycle before it
ever influences recall:

1. **Extract** (`qwen3.7-plus`, JSON mode) — pull atomic, durable facts out of
   the transcript; drop the transient chatter.
2. **Dedupe** — if a new fact embeds within 0.90 cosine of an existing one, we
   *reinforce* that memory instead of storing a near-duplicate. Reinforcement
   later becomes a recall signal.
3. **Supersede** — this is the interesting one. *"always coffee"* and *"never
   coffee"* embed almost identically; similarity alone can't tell an update from
   a repeat. So in the gray zone we ask `qwen3.7-max` a single question: *do
   these contradict?* If yes, the stale memory is **retired with provenance** —
   kept for audit, excluded from recall, with the reason recorded. Nothing is
   silently deleted.
4. **Recall** — hybrid score = `cosine × importance × recency × reinforcement`,
   so what surfaces is relevant, current, *and* repeatedly confirmed.

## Prove it, don't claim it

The part I'm proudest of isn't a feature — it's the eval. `majordomo eval` runs
scripted returning-guest personas through two agents: Majordomo, and an
append-only baseline that skips governance. After every simulated stay, a Qwen
judge quizzes each on what it should know. The result is a curve, not a vibe:

```
governed  accuracy by stay: [1.0, 1.0, 1.0]
naive     accuracy by stay: [1.0, 1.0, 0.8]   <- recalls the superseded preference
```

The two agents are identical until a guest *changes their mind* — and that's
exactly where governance earns its keep.

## Running on Qwen Cloud and Alibaba Cloud

Inference is entirely on **Alibaba Cloud Model Studio (DashScope)** through the
OpenAI-compatible endpoint — one `httpx` client, no SDK shim, three model roles
(agent, judge, embeddings). The backend deploys to **Alibaba Cloud Function
Compute** as a web function in Singapore, exposing a public `/chat` endpoint
that runs the real governed engine.

A design choice that paid off: a deterministic **mock backend**. It reproduces
every prompt kind with rule-based logic, so the entire pipeline — governance,
recall, *and the eval harness* — runs and passes tests with zero API keys. CI
stays free, the architecture is verifiable offline, and flipping one env var
(`LLM_BACKEND=qwen`) swaps in the real Qwen Cloud path.

## What I'd build next

The memory ledger is SQLite today; the natural next step is ApsaraDB RDS with
per-guest isolation, plus a small dashboard that shows reinforcement and
supersession happening live. But the core claim is already the whole point:
**an assistant whose memory improves with experience instead of decaying under
it.**

*Code: `github.com/<org>/majordomo` (Apache-2.0). Built new for this hackathon;
reuses eval-harness and mock-backend patterns from my earlier NexusVenue project.*
