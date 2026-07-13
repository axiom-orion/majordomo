"""Scripted guest personas for the cross-session accuracy evaluation.

Each persona is a sequence of sessions (scripted guest utterances) plus quiz
questions with ground-truth answers. `answerable_from` marks the session index
(1-based) at which the fact first appears; `updates` re-keys the expected
answer when the guest CHANGES a preference in a later session — the case that
separates governed memory from append-only memory.
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
            },
        ],
    },
]
