import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
        # Configurações do navegador
        self.HEADLESS = False
        self.TIMEOUT = 30000  # 30 segundos em ms
        
        # Configurações do Tesseract
        self.TESSERACT_CMD = os.getenv('TESSERACT_CMD', r'C:\Program Files\Tesseract-OCR\tesseract.exe')
        
        # Diretórios
        self.BASE_DIR = Path(__file__).parent.parent
        self.INVOICE_DIR = self.BASE_DIR / "data/invoices"
        self.RESULTS_DIR = self.BASE_DIR / "results"
        self.RESULTS_DIR.mkdir(exist_ok=True)
        
        # Arquivos
        self.CSV_FILE = self.RESULTS_DIR / "invoices.csv"
        
        # URLs
        self.TARGET_URL = "http://rpachallengeocr.azurewebsites.net/"