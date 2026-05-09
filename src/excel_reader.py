import openpyxl


def load_vendors(filepath: str) -> tuple[list[dict], str]:
    """
    Read an Excel file and return a list of vendor dicts with 'name' and 'email' keys.
    Returns (vendors, error_message). On success error_message is empty string.
    Auto-detects columns named Name/Email (case-insensitive).
    """
    try:
        wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        ws = wb.active
    except Exception as e:
        return [], f"Could not open file: {e}"

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return [], "Excel file is empty."

    # Find header row — first row with at least 2 non-empty cells
    header = [str(c).strip() if c is not None else "" for c in rows[0]]

    name_col = _find_column(header, ["name", "vendor name", "company", "vendor"])
    email_col = _find_column(header, ["email", "email id", "email address", "mail"])

    if name_col is None:
        return [], "Could not find a 'Name' column. Please name it: Name, Vendor Name, or Company."
    if email_col is None:
        return [], "Could not find an 'Email' column. Please name it: Email, Email ID, or Email Address."

    vendors = []
    for row in rows[1:]:
        name = str(row[name_col]).strip() if row[name_col] is not None else ""
        email = str(row[email_col]).strip() if row[email_col] is not None else ""
        if name and email and "@" in email:
            vendors.append({"name": name, "email": email, "status": "Pending"})

    wb.close()

    if not vendors:
        return [], "No valid vendor rows found. Ensure Name and Email columns have data."

    return vendors, ""


def _find_column(header: list[str], candidates: list[str]) -> int | None:
    for i, cell in enumerate(header):
        if cell.lower() in candidates:
            return i
    return None
