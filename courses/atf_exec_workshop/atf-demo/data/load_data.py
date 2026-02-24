"""Load CSV data files into plain Python lists of dicts."""

import csv
import os

DATA_DIR = os.path.dirname(__file__)


def load_companies():
    """Load company.csv and return a list of dicts with typed fields."""
    rows = []
    with open(os.path.join(DATA_DIR, "company.csv")) as f:
        for row in csv.DictReader(f):
            rows.append({
                "company_id": int(row["company_id"]),
                "name": row["name"],
                "segment": row["segment"],
                "industry": row["industry"],
                "total_employees": int(row["total_employees"]),
                "in_office_employees": int(row["in_office_employees"]),
                "total_conf_rooms": int(row["total_conf_rooms"]),
                "purchased_boxes": int(row["purchased_boxes"]),
                "licensed_users": int(row["licensed_users"]),
                "annual_contract_value": int(row["annual_contract_value"]),
                "contract_start_year": row.get("contract_start_year", ""),
                "mdm_system": row.get("mdm_system", ""),
            })
    return rows


def load_contacts():
    """Load contact.csv and return a list of dicts."""
    rows = []
    with open(os.path.join(DATA_DIR, "contact.csv")) as f:
        for row in csv.DictReader(f):
            rows.append({
                "contact_id": int(row["contact_id"]),
                "company_id": int(row["company_id"]),
                "full_name": row["full_name"],
                "role": row["role"],
                "is_primary": row["is_primary"].strip() == "True",
            })
    return rows


def load_activities():
    """Load activity.csv and return a list of dicts."""
    rows = []
    with open(os.path.join(DATA_DIR, "activity.csv")) as f:
        for row in csv.DictReader(f):
            rows.append({
                "activity_id": int(row["activity_id"]),
                "company_id": int(row["company_id"]),
                "activity_date": row["activity_date"],
                "type": row["type"],
                "note": row["note"],
            })
    return rows
