"""The governed memory engine — Majordomo's core contribution.

Naive memory agents append everything and retrieve by similarity; over
sessions the store fills with duplicates and stale, contradicted facts, and
recall quality *degrades* with experience. Majordomo governs the lifecycle:

  remember():
    1. EXTRACT   candidate memories from the conversation (Qwen, JSON mode)
    2. DEDUPE    embedding similarity >= DEDUPE_T -> reinforce, don't re-store
    3. SUPERSEDE similarity in the gray zone -> Qwen contradiction check;
                 contradicting old memories are superseded (kept for audit,
                 excluded from recall) with the reason recorded
    4. STORE     with importance, provenance (session, timestamps)

  recall():
    hybrid score = cosine(query, memory)
                 * importance weighting
                 * recency decay
                 * reinforcement boost
    -> the memories that are relevant, current, and repeatedly confirmed.
"""

import json
import math
import time
from dataclasses import dataclass

from majordomo.llm import cosine, get_client
from majordomo.store import MemoryStore

DEDUPE_T = 0.90        # >= this: same fact, reinforce
# >= this (and < DEDUPE_T): same topic, run the LLM contradiction check.
# Deliberately broad — it is only a prefilter; the verdict is the LLM's.
CONTRADICTION_T = 0.22
HALF_LIFE_DAYS = 90.0

EXTRACT_SYSTEM = """[extract] You extract durable guest memories from a hotel
conversation transcript. Return JSON: {"memories": [{"content": str,
"kind": "preference"|"fact"|"incident"|"policy_learning", "importance": 1-5}]}.
Only extract things worth remembering across future stays: preferences,
allergies, recurring requests, complaints, corrections, learned procedures.
Write each content as a short standalone third-person statement.
No transient chatter. Empty list if nothing durable."""

CONTRADICTION_SYSTEM = """[contradiction] Two guest memory statements follow.
Do they contradict — would acting on the old one violate the new one?
Return JSON: {"contradicts": true|false}. Preference *changes* contradict;
unrelated or compatible facts do not."""


@dataclass
class RememberReport:
    stored: list[str]
    reinforced: list[str]
    superseded: list[tuple[str, str]]  # (old content, new content)


class MemoryEngine:
    def __init__(self, store: MemoryStore | None = None, client=None, govern: bool = True):
        # govern=False disables dedupe + supersede (append-only memory) — the
        # naive baseline the eval harness compares against.
        self.store = store or MemoryStore()
        self.client = client or get_client()
        self.govern = govern

    # ---------------- remember ----------------

    def remember(self, guest_id: str, transcript: str, session_id: str) -> RememberReport:
        raw = self.client.chat(EXTRACT_SYSTEM, transcript, json_mode=True)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        # Real Qwen returns either {"memories": [...]} or a bare [...] array
        # (the mock always used the wrapped form, so this only bites live).
        if isinstance(parsed, dict):
            candidates = parsed.get("memories", [])
        elif isinstance(parsed, list):
            candidates = parsed
        else:
            candidates = []
        # Drop malformed entries so downstream cand["content"] is always safe.
        candidates = [c for c in candidates if isinstance(c, dict) and c.get("content")]
        report = RememberReport([], [], [])
        if not candidates:
            return report

        vectors = self.client.embed([c["content"] for c in candidates])
        for cand, vec in zip(candidates, vectors):
            existing = self.store.active(guest_id)
            match, best = None, 0.0
            for mem in existing:
                sim = cosine(vec, mem["embedding"])
                if sim > best:
                    match, best = mem, sim

            if self.govern and match and best >= DEDUPE_T:
                # High similarity = same TOPIC, not necessarily same fact —
                # "always drinks coffee" vs "never drinks coffee" embed nearly
                # identically. The LLM decides: reinforce or supersede.
                if not self._contradicts(match["content"], cand["content"]):
                    self.store.reinforce(match["id"])
                    report.reinforced.append(match["content"])
                    continue
                new_id = self.store.add(
                    guest_id, cand["content"], vec, cand.get("kind", "preference"),
                    float(cand.get("importance", 3)), session_id,
                )
                self.store.supersede(match["id"], new_id,
                                     f"contradicted in session {session_id}")
                report.stored.append(cand["content"])
                report.superseded.append((match["content"], cand["content"]))
                continue

            new_id = self.store.add(
                guest_id, cand["content"], vec, cand.get("kind", "preference"),
                float(cand.get("importance", 3)), session_id,
            )
            report.stored.append(cand["content"])

            if not self.govern:
                continue
            # Gray zone: same topic, different statement -> contradiction check.
            for mem in existing:
                sim = cosine(vec, mem["embedding"])
                if CONTRADICTION_T <= sim < DEDUPE_T:
                    if self._contradicts(mem["content"], cand["content"]):
                        self.store.supersede(
                            mem["id"], new_id,
                            f"contradicted in session {session_id}")
                        report.superseded.append((mem["content"], cand["content"]))
        return report

    def _contradicts(self, old: str, new: str) -> bool:
        verdict = self.client.chat(
            CONTRADICTION_SYSTEM, f'OLD: "{old}"\nNEW: "{new}"', json_mode=True)
        try:
            parsed = json.loads(verdict)
        except json.JSONDecodeError:
            return False
        if isinstance(parsed, dict):
            return bool(parsed.get("contradicts", False))
        if isinstance(parsed, bool):  # real Qwen may answer with a bare true/false
            return parsed
        return False

    # ---------------- recall ----------------

    def recall(self, guest_id: str, query: str, k: int = 6) -> list[dict]:
        memories = self.store.active(guest_id)
        if not memories:
            return []
        qvec = self.client.embed([query])[0]
        now = time.time()
        scored = []
        for m in memories:
            sim = cosine(qvec, m["embedding"])
            if sim <= 0:
                continue
            age_days = (now - m["last_seen_at"]) / 86400
            recency = math.pow(0.5, age_days / HALF_LIFE_DAYS)
            importance = 0.5 + m["importance"] / 10.0        # 0.6..1.0
            reinforcement = 1.0 + math.log1p(m["reinforcements"]) / 4.0
            scored.append((sim * recency * importance * reinforcement, m))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [
            {"content": m["content"], "kind": m["kind"], "score": round(s, 4),
             "reinforcements": m["reinforcements"], "source_session": m["source_session"]}
            for s, m in scored[:k]
        ]
