from playwright.sync_api import sync_playwright, Page
import os
import re
import csv
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
import pytesseract

from config.settings import Settings
from config.logger import logger

class RPAChallengeOCR:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.playwright = sync_playwright().start()
        self._initialize_browser()
        logger.info("OCR Challenge initialized")

    def _initialize_browser(self):
        self.browser = self.playwright.chromium.launch(
            headless=self.settings.HEADLESS,
            args=["--start-maximized"],
            channel="chrome"
        )
        self.context = self.browser.new_context(no_viewport=True)
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.settings.TIMEOUT)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.context.close()
        self.browser.close()
        self.playwright.stop()
        logger.info("Browser closed")

    def _download_invoice_image(self, image_url: str, invoice_id: str) -> Path:
        path = self.settings.INVOICE_DIR / f"{invoice_id}.jpg"
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            with open(path, "wb") as f:
                f.write(response.content)
            return path
        except Exception as e:
            logger.error(f"Failed to download invoice image: {e}")
            raise

    def _extract_text_from_image(self, image_path: Path) -> str:
        try:
            pytesseract.pytesseract.tesseract_cmd = self.settings.TESSERACT_CMD
            img = Image.open(image_path)
            img = img.convert('L')  # Convert to grayscale
            text = pytesseract.image_to_string(img).strip()
            
            if not text:
                raise ValueError("OCR não retornou texto")
                
            return text
        except Exception as e:
            logger.error(f"OCR processing failed: {e}")
            raise

    def _parse_invoice_data(self, text: str) -> Dict[str, str]:
        try:
            invoice_no = re.search(r"Invoice\s*(?:#\s*)?(\d+)", text)
            invoice_date = re.search(r"(\d{4}-\d{2}-\d{2})", text)
            company_name = re.search(r"(.*?)\s+INVOICE", text)
            total_due = re.search(r"Total\s+([\d,.]+)", text)

            if not all([invoice_no, invoice_date, company_name, total_due]):
                raise ValueError("Failed to extract invoice data")

            return {
                "invoice_no": invoice_no.group(1),
                "invoice_date": datetime.strptime(invoice_date.group(1), "%Y-%m-%d").strftime("%d-%m-%Y"),
                "company_name": company_name.group(1).strip(),
                "total_due": total_due.group(1)
            }
        except Exception as e:
            logger.error(f"Data parsing failed: {e}")
            raise

    def _process_invoice(self, row) -> Optional[Dict[str, str]]:
        invoice_id = row.locator("td:nth-child(2)").inner_text().strip()
        due_date = row.locator("td:nth-child(3)").inner_text().strip()

        try:
            if datetime.strptime(due_date, "%d-%m-%Y") > datetime.now():
                return None

            with self.page.expect_popup() as popup_info:
                row.get_by_role("link").click()
            popup = popup_info.value
            
            try:
                image_url = popup.locator("img[src*='jpg']").get_attribute("src")
                image_path = self._download_invoice_image(image_url, invoice_id)
                text = self._extract_text_from_image(image_path)
                
                invoice_data = self._parse_invoice_data(text)
                result = {
                    "invoice_id": invoice_id,
                    "due_date": due_date,
                    **invoice_data,
                    "status": "success"
                }
                logger.info(f"Invoice {invoice_id} processed successfully")
                return result
            finally:
                popup.close()
                
        except Exception as e:
            logger.error(f"Error processing invoice {invoice_id}: {e}")
            return {
                "invoice_id": invoice_id,
                "due_date": due_date,
                "status": "failed",
                "error": str(e)
            }

    def _generate_csv(self, data: List[Dict[str, str]]) -> Path:
        try:
            with open(self.settings.CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
                if not data:
                    return self.settings.CSV_FILE
                
                writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            logger.info(f"CSV generated at {self.settings.CSV_FILE}")
            return self.settings.CSV_FILE
        except Exception as e:
            logger.error(f"CSV generation failed: {e}")
            raise

    def run(self) -> List[Dict[str, str]]:
        results = []
        
        try:
            self.page.goto(self.settings.TARGET_URL)
            self.page.get_by_role("button", name="START").click()
            self.page.wait_for_selector("table")
            logger.info("Challenge started")

            while True:
                for row in self.page.locator("table tbody tr").all():
                    result = self._process_invoice(row)
                    if result:
                        results.append(result)

                next_btn = self.page.locator(".paginate_button.next")
                if "disabled" in next_btn.get_attribute("class"):
                    break
                next_btn.click()

            csv_path = self._generate_csv(results)
            self.page.locator('input[type="file"][name="csv"]').set_input_files(str(csv_path))
            logger.info("Results submitted successfully")

            if not self.settings.HEADLESS:
                screenshot_path = self.settings.RESULTS_DIR / "final.png"
                self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot saved to {screenshot_path}")

            return results
        except Exception as e:
            logger.error(f"OCR challenge failed: {e}")
            raise