"""Offline tests — mock backend, zero API keys. Cover the three governance
paths (store / dedupe-reinforce / contradiction-supersede), recall ranking,
and the end-to-end eval harness invariant (governed >= naive at final session)."""

import os
from pathlib import Path

os.environ["LLM_BACKEND"] = "mock"

from majordomo.engine import MemoryEngine
from majordomo.evals.harness import run_persona
from majordomo.evals.personas import PERSONAS
from majordomo.llm import MockClient
from majordomo.store import MemoryStore


def make_engine(govern=True):
    return MemoryEngine(store=MemoryStore(Path(":memory:")), client=MockClient(), govern=govern)


def test_store_and_recall():
    e = make_engine()
    report = e.remember("g1", "Guest: I am allergic to peanuts, please note it.", "s1")
    assert report.stored, "should extract and store an allergy memory"
    recalled = e.recall("g1", "what dietary allergies does the guest have?")
    assert recalled and "peanut" in recalled[0]["content"].lower()


def test_dedupe_reinforces_instead_of_duplicating():
    e = make_engine()
    e.remember("g1", "Guest: I always drink oat-milk cappuccino in the morning.", "s1")
    e.remember("g1", "Guest: I always drink oat-milk cappuccino in the morning.", "s2")
    active = e.store.active("g1")
    assert len(active) == 1, "identical fact should reinforce, not duplicate"
    assert active[0]["reinforcements"] == 2


def test_contradiction_supersedes():
    e = make_engine()
    e.remember("g1", "Guest: I always drink cappuccino coffee in the morning.", "s1")
    e.remember("g1", "Guest: I never drink cappuccino coffee in the morning now.", "s2")
    history = e.store.history("g1")
    superseded = [r for r in history if r["superseded_by"]]
    active = e.store.active("g1")
    assert superseded, "contradicted memory should be superseded"
    assert len(active) == 1, "only the new fact should remain active"


def test_naive_mode_accumulates_duplicates():
    e = make_engine(govern=False)
    e.remember("g1", "Guest: I always drink oat-milk cappuccino in the morning.", "s1")
    e.remember("g1", "Guest: I always drink oat-milk cappuccino in the morning.", "s2")
    assert len(e.store.active("g1")) == 2, "naive mode should append, not dedupe"


def test_harness_governed_beats_or_ties_naive_at_end():
    persona = PERSONAS[0]
    governed = run_persona(persona, govern=True)
    naive = run_persona(persona, govern=False)
    g_final = governed["per_session"][-1]["accuracy"]
    n_final = naive["per_session"][-1]["accuracy"]
    assert g_final is not None
    assert g_final >= n_final, f"governed ({g_final}) should beat naive ({n_final}) after a preference change"
    assert governed["per_session"][-1]["superseded"] >= 1, "stay 3 contains a preference change"
