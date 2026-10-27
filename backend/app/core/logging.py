import logging
import sys

_MARK = "_yokai_handler"


def configure_logging() -> None:
    """Make INFO logs of the ``app.*`` tree visible; safe to call repeatedly.

    Only the ``app`` logger is touched so uvicorn's and pytest's root handlers survive.
    """
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    if any(getattr(h, _MARK, False) for h in logger.handlers):
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    setattr(handler, _MARK, True)
    logger.addHandler(handler)
