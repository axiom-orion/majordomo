# Majordomo — demo video script

**Hard limit: < 3:00 (target 2:45).** Public video. Name Qwen Cloud + Alibaba
Cloud on screen. Show the architecture diagram. Show one verified metric. No
third-party trademarks (Grand Meridian + fictional guests only).

> Token note: the live demo run below costs real Qwen tokens. Record it **once**
> with `demo --persist`; everything else (chart, provenance ledger) is already
> generated and costs nothing to show.

---

### [0:00–0:20] Hook + what it is  *(overview in first 20s)*
> "Most memory agents get *worse* the more they remember — they append
> everything and retrieve by similarity, so stale, contradicted facts pile up.
> This is **Majordomo**: a concierge agent on **Qwen Cloud** and **Alibaba
> Cloud** that doesn't just remember — it **forgets on purpose, and keeps the
> receipts.** When you change a preference, it retires the old one, with a
> recorded reason, and keeps its recall clean."

*On screen:* title card "Majordomo — the memory agent that forgets with receipts" + Qwen Cloud / Alibaba Cloud names.

### [0:20–0:50] The problem, concretely
> "A guest says: *I drink cappuccino.* Two stays later: *I've switched to
> matcha.* An append-only agent now carries both — and every morning it's
> deciding your coffee off a memory full of contradictions."

*On screen:* the ledger filling with duplicate/stale rows.

### [0:50–1:25] How it works  *(show the diagram)*
> "Every fact runs a Qwen pipeline. **Extract** — qwen3.7-plus pulls atomic
> facts. **Dedupe** — heard it before, reinforce, don't duplicate. **Supersede**
> — same topic, changed fact: qwen3.7-max judges the contradiction. *Always
> coffee* and *never coffee* embed almost identically, so even near-duplicates
> get judged. The stale memory is **retired with provenance** — kept for audit,
> dropped from recall. Then recall is hybrid: similarity × importance × recency
> × reinforcement."

*On screen:* `docs/architecture.svg`.

### [1:25–2:00] Live demo — real Qwen  *(`majordomo demo --persist`)*
> "Live, on Qwen. Three stays. The guest switches from cappuccino to matcha —
> watch Majordomo detect the contradiction and supersede the old preference."

*On screen:* real terminal, the `superseded: 'cappuccino' -> 'matcha'` line in yellow.

### [2:00–2:25] The receipts  *(`majordomo memory --guest g-voss`)*
> "Here's what 'with receipts' means. The ledger shows the retired cappuccino
> memory — marked superseded, with the reason and the session it happened in.
> Nothing is silently deleted; forgetting is *auditable.* And it doesn't only
> remember preferences — from a single 6am-wake-up complaint it forms a standing
> *never call before 9am* policy and applies it next stay. It accumulates
> experience."

*On screen:* the `memory` ledger output — the SUPERSEDED row with its reason.

### [2:25–2:50] The honest proof + close
> "We measured it, honestly. A capable model answers right either way — so we
> *don't* claim a fake accuracy win. What we prove is recall hygiene: verified
> live on Qwen, after the switch the append-only agent surfaces **two**
> contradicted cappuccino memories into recall and carries **14** rows.
> Majordomo surfaces **zero**, and carries **7**. Timely forgetting, clean
> limited-context recall — deployed on Alibaba Cloud Function Compute. That's
> Majordomo."

*On screen:* `data/accuracy_curve.png` (green flat at 0, red rising; store size diverging), then the live `/health` endpoint showing the Alibaba Cloud region. End card: repo URL + Apache-2.0.

---

## Recording checklist
- [ ] Terminal font large, high contrast; readable at 720p.
- [ ] `majordomo demo --persist` recorded ONCE (real Qwen — the only token spend). Space takes to avoid 429s; retry/backoff now absorbs slow calls.
- [ ] Then `majordomo memory --guest g-voss` for the provenance ledger (free — reads the db).
- [ ] Qwen Cloud + Alibaba Cloud named/shown (0:00 and 2:50). ✅
- [ ] Architecture diagram shown (0:50). ✅
- [ ] One verified metric spoken: 0 vs 2 stale in recall; 7 vs 14 rows. ✅
- [ ] Chart shown is `accuracy_curve.png`, titled "deterministic offline harness" — honest about backend. ✅
- [ ] Total < 3:00 — check the export twice.
- [ ] Upload **public** (not just unlisted).
