"""Transactional corporate-action accounting; caller owns commit/rollback."""


class ActionHeld(Exception):
    """Fixed safe refusal; never provider text."""


async def persist_action_batch(db, batch, authority):
    return ()


async def apply_due_actions(db, coin_id, now=None):
    return ()


async def derive_dividend_entitlements(db, event_id):
    return ()
