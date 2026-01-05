import logging

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="[%(levelname).1s] %(name)s:%(lineno)d - %(message)s",
    )
