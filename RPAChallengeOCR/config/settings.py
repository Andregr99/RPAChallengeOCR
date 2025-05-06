import os
from dotenv import load_dotenv

load_dotenv()

TESSERACT_CMD = os.getenv("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
INVOICE_DIR = "temp/invoices"
CSV_FILE = "temp/invoices.csv"
TARGET_URL = "https://rpachallengeocr.azurewebsites.net/"
