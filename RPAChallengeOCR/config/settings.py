import os
from dotenv import load_dotenv

load_dotenv()

TESSERACT_CMD = os.getenv("TESSERACT_PATH")
INVOICE_DIR = "temp/invoices"
CSV_FILE = "temp/invoices.csv"
TARGET_URL = "https://rpachallengeocr.azurewebsites.net/"
