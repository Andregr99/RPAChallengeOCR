from playwright.sync_api import sync_playwright, Page
import os
import re
import csv
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image, ImageEnhance
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
        self.settings.INVOICE_DIR.mkdir(parents=True, exist_ok=True)
        path = self.settings.INVOICE_DIR / f"{invoice_id}.jpg"
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        with open(path, "wb") as f:
            f.write(response.content)
        return path

    def _enhance_image(self, image_path: Path) -> Image:
        img = Image.open(image_path)
        img = img.convert('L')
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        img = img.point(lambda x: 0 if x < 180 else 255, '1')
        return img

    def _extract_text_from_image(self, image_path: Path, invoice_id: str) -> str:
        pytesseract.pytesseract.tesseract_cmd = self.settings.TESSERACT_CMD
        img = self._enhance_image(image_path)
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(img, config=custom_config).strip()
        txt_debug_path = self.settings.RESULTS_DIR / f"{invoice_id}.txt"
        with open(txt_debug_path, "w", encoding="utf-8") as f:
            f.write(text)
        if not text:
            raise ValueError("OCR returned no text")
        logger.debug(f"OCR Text for {invoice_id}:\n{text}")
        return text

    def _parse_invoice_data(self, text: str, invoice_id: str) -> Dict[str, str]:
        logger.debug(f"Parsing data for invoice {invoice_id}")
        invoice_no = None
        invoice_no_patterns = [
            r"Invoice\s*(?:No\.?|Number)?\s*[:#]?\s*(\d+)",
            r"INV-\s*(\d+)",
            r"#\s*(\d+)"
        ]
        for pattern in invoice_no_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_no = match.group(1)
                break

        date_patterns = [
            r"Date\s*[:#]?\s*(\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4})",
            r"Date\s*[:#]?\s*(\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4})",
            r"Date\s*[:#]?\s*(\d{4}-\d{2}-\d{2})",
            r"(\d{1,2}[-\/]\d{1,2}[-\/]\d{2,4})"
        ]
        invoice_date = None
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_date = match.group(1)
                break

        company_name = "Unknown Company"
        company_patterns = [
            r"(Sit\s*Amet\s*Corp(?:\.|oration)?)",
            r"(Aenean\s*LLC)",
            r"Bill\s*To:\s*(.*?)\n",
            r"To:\s*(.*?)\n",
            r"Att:\s*.*?\n(.*?)\n",
            r"^(.*?Corp|.*?LLC)"
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company_name = match.group(1).strip()
                if "Sit Amet" in company_name:
                    company_name = "Sit Amet Corp"
                elif "Aenean" in company_name:
                    company_name = "Aenean LLC"
                break

        total_match = re.search(r"Total\D*([\d,.]+)\b", text, re.IGNORECASE) or \
                     re.search(r"Amount\D*([\d,.]+)\b", text, re.IGNORECASE) or \
                     re.search(r"([\d,.]+\d)\s*$", text)

        if not invoice_no:
            logger.error(f"Invoice number not found in text:\n{text}")
            raise ValueError(f"Invoice number not found for ID: {invoice_id}")
        if not invoice_date:
            logger.error(f"Invoice date not found in text:\n{text}")
            invoice_date = datetime.now().strftime("%d-%m-%Y")
            logger.warning(f"Using current date as fallback: {invoice_date}")

        date_str = invoice_date
        formatted_date = date_str
        try:
            for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %B %Y", "%B %d, %Y"):
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    formatted_date = date_obj.strftime("%d-%m-%Y")
                    break
                except ValueError:
                    continue
        except Exception as e:
            logger.error(f"Error parsing date '{date_str}': {str(e)}")
            logger.warning(f"Using raw date string: {date_str}")

        if not total_match:
            logger.error(f"Total amount not found in text:\n{text}")
            raise ValueError(f"Total amount not found for ID: {invoice_id}")

        total_value = total_match.group(1)
        try:
            total_cleaned = total_value.replace(",", "").replace(".", "")
            if len(total_cleaned) > 2:
                total_float = float(total_cleaned[:-2] + "." + total_cleaned[-2:])
            else:
                total_float = float(total_cleaned) / 100
            formatted_total = f"{total_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception as e:
            logger.error(f"Error parsing total '{total_value}': {str(e)}")
            raise ValueError(f"Invalid total amount format for ID: {invoice_id}")

        return {
            "Invoice No": invoice_no,
            "Invoice Date": formatted_date,
            "Company Name": company_name,
            "Total Due": formatted_total
        }

    def _process_invoice(self, row) -> Optional[Dict[str, str]]:
        invoice_id = row.locator("td:nth-child(2)").inner_text().strip()
        due_date_str = row.locator("td:nth-child(3)").inner_text().strip()
        logger.info(f"Processing invoice {invoice_id}")
        try:
            with self.page.expect_popup() as popup_info:
                row.get_by_role("link").click()
            popup = popup_info.value
            try:
                image_url = popup.locator("img").get_attribute("src")
                if not image_url:
                    raise ValueError("No image URL found")
                logger.debug(f"Downloading image for {invoice_id}")
                image_path = self._download_invoice_image(image_url, invoice_id)
                logger.debug(f"Extracting text from image for {invoice_id}")
                text = self._extract_text_from_image(image_path, invoice_id)
                logger.debug(f"Parsing invoice data for {invoice_id}")
                invoice_data = self._parse_invoice_data(text, invoice_id)
                return {
                    "ID": invoice_id,
                    "Due Date": due_date_str,
                    **invoice_data
                }
            except Exception as e:
                logger.error(f"Error processing popup for invoice {invoice_id}: {str(e)}")
                return None
            finally:
                popup.close()
        except Exception as e:
            logger.error(f"Error processing invoice {invoice_id}: {str(e)}")
            return None

    def _generate_csv(self, data: List[Dict[str, str]]) -> Path:
        required_columns = ["ID", "Due Date", "Invoice No", "Invoice Date", "Company Name", "Total Due"]
        self.settings.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.settings.CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=required_columns)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Generated CSV file at {self.settings.CSV_FILE}")
        return self.settings.CSV_FILE

    def run(self) -> List[Dict[str, str]]:
        results = []
        logger.info("Navigating to target URL")
        self.page.goto(self.settings.TARGET_URL)
        logger.info("Starting challenge")
        self.page.get_by_role("button", name="START").click()
        self.page.wait_for_selector("table")
        logger.info("Processing invoices")
        while True:
            rows = self.page.locator("table tbody tr").all()
            logger.info(f"Found {len(rows)} rows to process")
            for row in rows:
                result = self._process_invoice(row)
                if result:
                    results.append(result)
                    logger.info(f"Successfully processed invoice {result['ID']}")
                else:
                    logger.info("Skipped or failed to process an invoice")
            next_btn = self.page.locator(".paginate_button.next:not(.disabled)")
            if not next_btn.count():
                logger.info("No more pages to process")
                break
            logger.info("Moving to next page")
            next_btn.click()
            self.page.wait_for_load_state("networkidle")
        logger.info("Challenge completed")
        self._generate_csv(results)
        return results

if __name__ == "__main__":
    settings = Settings()
    with RPAChallengeOCR(settings) as rpa_challenge:
        rpa_challenge.run()