import os
import re
import requests
from datetime import datetime
from PIL import Image
import pytesseract
from playwright.sync_api import Page, sync_playwright

from config.settings import TESSERACT_CMD, INVOICE_DIR, CSV_FILE, TARGET_URL
from config.logger import logger
from modules.database.db_handler import save_to_csv
from scraper.exceptions import InvoiceProcessingError

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
os.makedirs(INVOICE_DIR, exist_ok=True)

def extract_text_from_image(image_url: str, invoice_id: str) -> str:
    path = os.path.join(INVOICE_DIR, f"{invoice_id}.jpg")
    response = requests.get(image_url)
    with open(path, "wb") as f:
        f.write(response.content)
    return pytesseract.image_to_string(Image.open(path)).strip()

def parse_invoice_data(text: str) -> tuple[str, str, str, str]:
    invoice_no = re.search(r"Invoice\s*(?:#\s*)?(\d+)", text)
    invoice_date = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    company_name = re.search(r"(.*?)\s+INVOICE", text)
    total_due = re.search(r"Total\s+([\d,.]+)", text)

    if not all([invoice_no, invoice_date, company_name, total_due]):
        raise InvoiceProcessingError("Falha ao extrair dados do OCR")

    return (
        invoice_no.group(1),
        datetime.strptime(invoice_date.group(1), "%Y-%m-%d").strftime("%d-%m-%Y"),
        company_name.group(1).strip(),
        total_due.group(1),
    )

def run_scraper() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(TARGET_URL)
        page.get_by_role("button", name="START").click()
        page.wait_for_selector("table")

        data = []

        while True:
            for row in page.locator("table tbody tr").all():
                columns = row.locator("td").all()
                invoice_id = columns[1].inner_text().strip()
                due_date_str = columns[2].inner_text().strip()
                due_date = datetime.strptime(due_date_str, "%d-%m-%Y")

                if due_date <= datetime.today():
                    with page.expect_popup() as popup_info:
                        row.get_by_role("link").click()
                    popup = popup_info.value

                    image_url = popup.locator("img[src*='jpg']").get_attribute("src")
                    text = extract_text_from_image(image_url, invoice_id)
                    popup.close()

                    try:
                        invoice_no, invoice_date, company, total = parse_invoice_data(text)
                        data.append([invoice_id, due_date_str, invoice_no, invoice_date, company, total])
                        logger.info(f"Fatura {invoice_id} processada com sucesso.")
                    except InvoiceProcessingError as e:
                        logger.error(f"Erro na fatura {invoice_id}: {e}")

            next_btn = page.locator(".paginate_button.next")
            if "disabled" in next_btn.get_attribute("class"):
                break
            next_btn.click()

        save_to_csv(data)
        page.locator('input[type="file"][name="csv"]').set_input_files(CSV_FILE)
        logger.info(f"Arquivo {CSV_FILE} enviado com sucesso.")
        browser.close()
