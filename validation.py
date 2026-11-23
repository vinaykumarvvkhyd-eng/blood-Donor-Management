"""Centralized validation. All interfaces use the same rules."""
import re
from datetime import datetime, date

BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
STATUSES = ("Registered", "Contacted", "Donated", "Cancelled")

def clean_text(value, field, minimum=1, maximum=80):
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text.")
    value = " ".join(value.strip().split())
    if not minimum <= len(value) <= maximum:
        raise ValueError(f"{field} must contain {minimum}–{maximum} characters.")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{field} contains unsupported characters.")
    return value

def validate_name(value):
    value = clean_text(value, "Name", 2, 70)
    if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", value):
        raise ValueError("Name may contain letters, spaces, apostrophes, dots and hyphens only.")
    return value

def validate_age(value):
    try:
        age = int(value)
    except (TypeError, ValueError):
        raise ValueError("Age must be a whole number.")
    if not 18 <= age <= 65:
        raise ValueError("Age must be between 18 and 65 for this demo register.")
    return age

def validate_phone(value):
    digits = re.sub(r"\D", "", str(value or ""))
    if not re.fullmatch(r"[6-9]\d{9}", digits):
        raise ValueError("Enter a valid 10-digit Indian mobile number.")
    return digits

def validate_blood_group(value):
    value = str(value or "").strip().upper()
    if value not in BLOOD_GROUPS:
        raise ValueError("Select a valid blood group.")
    return value

def validate_gender(value):
    value = str(value or "").strip().title()
    if value not in ("Female", "Male", "Other", "Prefer not to say"):
        raise ValueError("Select a valid gender option.")
    return value

def validate_date(value, field="Camp date"):
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError(f"{field} must use YYYY-MM-DD format.")
    if parsed < date(2000, 1, 1) or parsed > date(2100, 12, 31):
        raise ValueError(f"{field} is outside the supported date range.")
    return parsed.isoformat()

def validate_status(value):
    value = str(value or "Registered").strip().title()
    if value not in STATUSES:
        raise ValueError("Select a valid registration status.")
    return value

def validate_donor(payload):
    if not isinstance(payload, dict):
        raise ValueError("A donor record must be an object.")
    return {
        "name": validate_name(payload.get("name", "")),
        "age": validate_age(payload.get("age", "")),
        "gender": validate_gender(payload.get("gender", "")),
        "phone": validate_phone(payload.get("phone", "")),
        "blood_group": validate_blood_group(payload.get("blood_group", "")),
        "city": clean_text(payload.get("city", ""), "City", 2, 60),
        "camp_date": validate_date(payload.get("camp_date", "")),
        "status": validate_status(payload.get("status", "Registered")),
    }
