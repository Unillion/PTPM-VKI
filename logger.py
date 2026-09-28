import logging
import os
import sys


def setup_logging(log_dir: str = "logs", log_file: str = "file_txt.log") -> None:
    os.makedirs(log_dir, exist_ok=True)

    log_format = "%(asctime)s | [%(levelname)-7s] | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)

    logging.basicConfig(
        level=logging.ERROR,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(log_dir, log_file), encoding="utf-8"),
        ],
    )

    logging.info("Логгер работ")