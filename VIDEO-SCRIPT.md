# Majordomo — demo video script

**Hard limit: < 3:00 (2:59 max — 3:00 is a violation).** Target **2:40** to leave
margin. Public video. 60/40 explain-to-demo. Name the sponsor tech on screen.
One quantified metric. Show the architecture diagram. Record in a clean terminal
+ the arch diagram; no third-party trademarks on screen.

Timecodes below sum to ~2:40. Read at a calm pace; cut dead air in editing.

---

### [0:00–0:20] Hook + what it is  *(overview in first 20s — required)*
> "Most memory agents get *worse* the more they remember. They append everything,
> retrieve by similarity — so stale facts outvote current ones. This is
> **Majordomo**: a concierge agent with *governed* memory, running on **Qwen Cloud**
> and **Alibaba Cloud**. It doesn't just store what you tell it — it dedupes,
> catches contradictions, and retires stale preferences, and it **proves** its
> recall gets more accurate over time."

*On screen:* title card "Majordomo — the concierge that never forgets" + the
Qwen Cloud / Alibaba Cloud logos or names.

### [0:20–0:50] The problem, concretely
> "A guest tells the hotel: *I drink cappuccino.* Three stays later: *I've
> switched to matcha.* A naive agent now holds three cappuccino memories and one
> matcha — so it recommends cappuccino. More memory, worse answer."

*On screen:* two-column "naive vs governed" text, or the memory ledger filling up.

### [0:50–1:30] How it works  *(show the diagram)*
> "Every fact runs a Qwen-powered pipeline. **Extract** — qwen3.7-plus pulls
> atomic, durable facts. **Dedupe** — if we've heard it, we reinforce, not
> duplicate. **Supersede** — same topic, changed fact: qwen3.7-max judges whether
> it's a contradiction. *Always coffee* and *never coffee* embed almost
> identically — so even near-duplicates get judged. The stale memory is
> **retired with provenance** — kept for audit, dropped from recall. Then recall
> is hybrid: similarity times importance, recency, and reinforcement."

*On screen:* `docs/architecture.svg` — walk the boxes as you say them.

### [1:30–2:10] Live demo  *(the real payoff)*
> "Watch it happen." *(run `majordomo demo`)* — "Guest switches from cappuccino
> to matcha. Majordomo detects the contradiction, supersedes the old preference
> with a recorded reason…" *(run `majordomo memory --guest ...`)* — "…here's the
> ledger: active memories, and the superseded one with *why*. Nothing is
> silently deleted."

*On screen:* real terminal. Keep it snappy; pre-seed state so no waiting on API.

### [2:10–2:40] The proof + close  *(the metric — required)*
> "And we don't just claim it — we measure it." *(run/show `majordomo eval` +
> the accuracy chart)* — "Same personas, governed memory versus append-only.
> When the guest changes a preference, the naive baseline drops to **0.8**.
> Majordomo holds **1.0**. Memory that improves with experience — deployed on
> Alibaba Cloud Function Compute, judged by Qwen. That's Majordomo."

*On screen:* `data/accuracy_curve.png` (1.0 vs 0.8), then the live `/health`
endpoint showing the Alibaba Cloud region. End card: repo URL + Apache-2.0.

---

## Recording checklist
- [ ] Terminal font large enough to read at 720p; light-on-dark, high contrast.
- [ ] Pre-seed the demo guest so no live API latency mid-take (space takes to avoid 429s).
- [ ] Qwen Cloud + Alibaba Cloud named/shown on screen at least once (they are — 0:00 and 2:40).
- [ ] Architecture diagram shown (1:30 block).
- [ ] Exactly one quantified metric spoken (1.0 vs 0.8).
- [ ] Total runtime < 3:00 — check the export twice.
- [ ] No third-party trademarks visible (use the Grand Meridian / fictional guests only).
- [ ] Upload public (YouTube unlisted is NOT public enough for some rules — use public).
