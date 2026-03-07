import logging
import sys


def setup_logger():
    logger = logging.getLogger("ticket_ai_api")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = setup_logger()