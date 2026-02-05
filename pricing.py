# token_bank/pricing.py
PRICING = {
    "thumbnail_wizard": {"analyze": 4},
    "document_wizard": {"analyze": 4},
    "prompt_wizard": {"optimize": 5},
    "script_wizard": {"generate": 3},
    "hook_wizard": {"generate": 4},
    "a11y_wizard": {"check": 0}
}

ACCOUNT_TYPES = {
    "free": {
        "tokens": 15,
        "price": 0,
        "best_for": "Testing the waters"
    },
    "student": {
        "tokens": 75,
        "price": 9.99,
        "best_for": "Students & personal brands"
    },
    "creator": {
        "tokens": 200,
        "price": 19.99,
        "best_for": "Part-time creators (3-4 pieces/week)"
    },
    "agency": {
        "tokens": 1000,
        "price": 49.99,
        "best_for": "Full-time creators & small teams"
    }
}
