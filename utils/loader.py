import pandas as pd
from io import BytesIO
from werkzeug.datastructures import FileStorage

ALLOWED_EXTENSIONS = {"csv","xlsx","xls"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_file(file: FileStorage) -> pd.DataFrame:
    filename = file.filename.lower()
    raw = BytesIO(file.read())

    if filename.endswith(".csv"):
        return _load_csv(raw)
    elif filename.endswith((".xlsx",".xls")):
        return _load_excel(raw, file)
    else:
        raise ValueError(
            f"Unsupported file type: {filename}."
            f"Please upload a .csv, .xlsx or .xls file." 
        )
    
def _load_csv(raw: BytesIO) -> pd.DataFrame:
    for encoding in ["utf-8", "latin-1", "cp1252", "utf-16"]:
        try:
            raw.seek(0)
            df = pd.read_csv(raw, encoding=encoding)
            if df.empty:
                raise ValueError("CSV file is empty.")
            return df
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError:
            raise ValueError("CSV file is empty or has no columns.")
        except pd.errors.ParserError as e:
            raise ValueError(f"Could not parse CSV: {e}")
    raise ValueError(
        "Cannot decode CSV file. Try re-saving it as UTF-8 in Excel or Google Sheets."
    )

def _load_excel(raw: BytesIO, file:FileStorage)-> pd.DataFrame:
    try:

        xl = pd.ExcelFile(raw)
    except Exception as e:
        raise ValueError(f"Cannot open Excel file: {e}")
    sheet = xl.sheet_names[0]
    try:
        df = x1.parse(sheet)
        if df.empty:
            raise ValueError(f"Sheet '{sheet}' is empty.")
        return df
    except Exception as e:
        raise ValueError(f"Error reading sheet '{sheet}': {e}")
    

def get_sheet_names(file: FileStorage)-> list[str]:
    raw = BytesIO(file.read())
    file.seek(0)
    xl = pd.ExcelFile(raw)
    return xl.sheet_names

def load_excel_sheet(file: FileStorage, sheet_name: str)-> pd.DataFrame:
    raw = BytesIO(file.read())
    xl = pd.ExcelFile(raw)
    if sheet_name not in xl.sheet_names:
        raise ValueError(f"Sheet '{sheet_name}' not found. Available: {xl.sheet_names}")
    return xl.parse(sheet_name)
