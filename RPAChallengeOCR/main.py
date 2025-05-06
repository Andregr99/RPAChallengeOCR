import sys
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from config.logger import logger
from config.settings import Settings
from scraper.rpa_challenge_ocr_scraper import RPAChallengeOCR

def main():
    try:
        logger.info("Iniciando aplicação RPA Challenge OCR")
        
        with RPAChallengeOCR(Settings()) as scraper:
            results = scraper.run()
            logger.info(f"✅ Processo concluído! {len(results)} faturas processadas com sucesso")
            
        return 0
    except Exception as e:
        logger.error(f"Falha na execução: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())