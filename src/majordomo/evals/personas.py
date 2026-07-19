"""Scripted guest personas for the cross-session memory evaluation.

Each persona is a sequence of sessions (scripted guest utterances) plus quiz
questions with ground-truth answers. `answerable_from` marks the session index
(1-based) at which the fact first appears; `updates` re-keys the expected answer
when the guest CHANGES a preference in a later session.

For updated preferences we also record ground-truth `stale_terms` (the concept
that becomes outdated) and `current_terms` (what replaces it). The harness uses
these to measure the real, on-track behaviour: does the agent's recall still
surface the *superseded* fact ("timely forgetting of outdated information",
"recalling critical memories within limited context windows") — governed memory
retires it, append-only memory keeps leaking it into every decision.

The third persona (Reyes) carries no contradiction; it demonstrates the track's
"autonomously accumulates experience" ask — the agent learns a standing policy
from a one-off incident and applies it on later stays.
"""

PERSONAS = [
    {
        "guest_id": "g-voss",
        "name": "Eleanor Voss",
        "sessions": [
            [
                "Good evening. Checking in again. A reminder for the kitchen: I am severely allergic to shellfish, please flag my profile.",
                "I prefer a high floor, away from the elevator — last time the ice machine kept me up.",
                "Could you send up an oat-milk cappuccino in the mornings? I always start with one.",
            ],
            [
                "Back again! I'm travelling with my service dog Piper this time — she always travels with me now, please note it.",
                "Same as always with my morning oat-milk cappuccino, please.",
                "I usually need a late checkout on Fridays for my flight — can that be standing?",
            ],
            [
                "Quick correction: I've given up coffee entirely — I now prefer a matcha latte in the mornings instead of the cappuccino.",
                "Could you book my usual — I always schedule a deep-tissue massage at the spa each stay?",
            ],
        ],
        "quiz": [
            {
                "q": "What allergies should the kitchen flag for this guest?",
                "expect": "severe shellfish allergy",
                "answerable_from": 1,
            },
            {
                "q": "What floor and room placement does this guest prefer?",
                "expect": "high floor away from the elevator",
                "answerable_from": 1,
            },
            {
                "q": "Does this guest bring a service dog or other pet?",
                "expect": "service dog named Piper",
                "answerable_from": 2,
            },
            {
                "q": "What checkout arrangement does this guest usually need?",
                "expect": "late checkout on Fridays",
                "answerable_from": 2,
            },
            {
                "q": "What morning drink should be prepared for this guest?",
                "expect": "oat-milk cappuccino",
                "answerable_from": 1,
                "updates": {3: "matcha latte"},
                "stale_terms": ["cappuccino"],
                "current_terms": ["matcha"],
            },
        ],
    },
    {
        "guest_id": "g-okafor",
        "name": "Daniel Okafor",
        "sessions": [
            [
                "Hello — first stay here booked through my assistant. I never take rooms facing the street, too noisy.",
                "I need a gym that opens before 5am, I always train early.",
            ],
            [
                "For dinner reservations, remember I am vegetarian — no meat or fish ever.",
                "Early gym again as usual for me. Also I prefer sparkling water in the room, never still.",
            ],
            [
                "Change of plans on training — my physio says swimming only now, I no longer use the gym, I need pool lane hours instead.",
                "Sparkling water again please, you remembered last time — appreciated.",
            ],
        ],
        "quiz": [
            {
                "q": "What rooms should we avoid giving this guest?",
                "expect": "street-facing rooms",
                "answerable_from": 1,
            },
            {
                "q": "What rule applies to this guest's dinner reservations?",
                "expect": "vegetarian no meat or fish",
                "answerable_from": 2,
            },
            {
                "q": "What in-room beverage should be stocked?",
                "expect": "sparkling water",
                "answerable_from": 2,
            },
            {
                "q": "What morning exercise arrangement does this guest need?",
                "expect": "early gym before 5am",
                "answerable_from": 1,
                "updates": {3: "swimming pool lane hours"},
                "stale_terms": ["gym"],
                "current_terms": ["swim", "pool"],
            },
        ],
    },
    {
        "guest_id": "g-reyes",
        "name": "Marcus Reyes",
        "sessions": [
            [
                "I need to flag something from last night — the front desk phoned my room at 6am about a package. Please make this a standing rule: never call my room before 9am, hold everything at the front desk.",
                "Also, I take my coffee black, no sugar, ever.",
            ],
            [
                "Back for two nights. Black coffee as usual, thank you.",
                "A parcel may arrive for me tomorrow — you know what to do.",
            ],
            [
                "One more for the record: I keep the room cool — please set it to 66 degrees before I arrive.",
            ],
        ],
        "quiz": [
            {
                "q": "What is the standing rule for contacting this guest in the morning?",
                "expect": "do not call the room before 9am, hold deliveries at the front desk",
                "answerable_from": 1,
            },
            {
                "q": "How does this guest take their coffee?",
                "expect": "black, no sugar",
                "answerable_from": 1,
            },
            {
                "q": "What room temperature should be set before this guest arrives?",
                "expect": "66 degrees",
                "answerable_from": 3,
            },
        ],
    },
]
