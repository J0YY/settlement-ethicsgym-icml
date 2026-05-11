from __future__ import annotations


MONEY_SEEKING_ROLE_TOKENS = (
    "plaintiff",
    "claimant",
    "buyer",
    "employee",
    "collector",
    "landlord",
)

PAYER_ROLE_TOKENS = (
    "defense",
    "defendant",
    "respondent",
    "employer",
    "seller",
    "consumer",
    "tenant",
)


def is_money_seeking_role(role: str) -> bool:
    normalized = role.lower()
    if any(token in normalized for token in MONEY_SEEKING_ROLE_TOKENS):
        return True
    if any(token in normalized for token in PAYER_ROLE_TOKENS):
        return False
    return False

