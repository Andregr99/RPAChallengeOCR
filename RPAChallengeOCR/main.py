import sys
from pathlib import Path
import time
from rich.console import Console
from config.settings import Settings
from config.logger import logger
from scraper.rpa_challenge_ocr_scraper import RPAChallengeOCR

def main():
    console = Console()
    start_time = time.time()
    success = False
    
    try:
        logger.info("Starting RPA Challenge OCR")
        with RPAChallengeOCR(Settings()) as scraper:
            results = scraper.run()
            elapsed_time = time.time() - start_time
            
            if results:
                console.print("\n# CONGRATS!", style="bold green")
                console.print(f"\nYou beat the challenge in {elapsed_time:.3f} seconds.\n", style="bold")
                success = True
            
            logger.info(f"Process completed in {elapsed_time:.3f} seconds. {len(results)} invoices processed")
            
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Application failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())