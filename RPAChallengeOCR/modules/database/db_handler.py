import pandas as pd
from config.settings import CSV_FILE

def save_to_csv(data: list[list[str]]) -> None:
    df = pd.DataFrame(data, columns=["ID", "DueDate", "InvoiceNo", "InvoiceDate", "CompanyName", "TotalDue"])
    df.to_csv(CSV_FILE, index=False)
