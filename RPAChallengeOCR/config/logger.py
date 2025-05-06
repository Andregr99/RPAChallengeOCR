import logging
import os
from rich.logging import RichHandler

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("scraper")
logger.setLevel(logging.DEBUG)

# Log para arquivo
file_handler = logging.FileHandler("logs/scraper.log", encoding="utf-8")
file_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_format)

# Log para terminal com Rich
console_handler = RichHandler()
console_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
