"""Application use-cases and analytics, independent of the UI."""
from collections import Counter
from datetime import datetime, date
from uuid import uuid4
from .storage import load_records, save_records, append_audit
from .validation import validate_donor, validate_date

def all_donors():
    return sorted(load_records(), key=lambda x: x.get("registered_at", ""), reverse=True)

def add_donor(payload):
    donor = validate_donor(payload)
    records = load_records()
    # Prevent duplicate registrations for the same phone and camp date.
    if any(r["phone"] == donor["phone"] and r["camp_date"] == donor["camp_date"] for r in records):
        raise ValueError("This mobile number is already registered for that camp date.")
    donor["id"] = "BC-" + uuid4().hex[:8].upper()
    donor["registered_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    records.append(donor)
    save_records(records)
    append_audit("CREATE", donor["id"], donor["blood_group"])
    return donor

def update_donor(record_id, payload):
    donor = validate_donor(payload)
    records = load_records()
    for index, old in enumerate(records):
        if old["id"] == record_id:
            if any(r["id"] != record_id and r["phone"] == donor["phone"] and r["camp_date"] == donor["camp_date"] for r in records):
                raise ValueError("Another registration already uses this mobile number for that camp date.")
            donor["id"] = record_id
            donor["registered_at"] = old.get("registered_at", datetime.now().astimezone().isoformat())
            records[index] = donor
            save_records(records)
            append_audit("UPDATE", record_id, donor["status"])
            return donor
    raise KeyError("Registration not found.")

def delete_donor(record_id):
    records = load_records()
    updated = [r for r in records if r["id"] != record_id]
    if len(updated) == len(records):
        raise KeyError("Registration not found.")
    save_records(updated)
    append_audit("DELETE", record_id)
    return True

def search_donors(query="", blood_group="", status="", city=""):
    records = all_donors()
    q = str(query or "").strip().casefold()
    return [r for r in records
            if (not q or q in " ".join(str(r.get(k, "")) for k in ("id","name","phone","city","blood_group")).casefold())
            and (not blood_group or r["blood_group"] == blood_group)
            and (not status or r["status"] == status)
            and (not city or city.casefold() in r["city"].casefold())]

def summary():
    records = load_records()
    groups = Counter(r["blood_group"] for r in records)
    statuses = Counter(r["status"] for r in records)
    ages = [int(r["age"]) for r in records if str(r.get("age", "")).isdigit()]
    today = date.today()
    overdue = [r for r in records if r.get("status") == "Registered"
               and date.fromisoformat(r["camp_date"]) < today]
    total = len(records)
    return {
        "total": total,
        "average_age": round(sum(ages) / len(ages), 1) if ages else 0,
        "blood_groups": {g: groups.get(g, 0) for g in ("A+","A-","B+","B-","AB+","AB-","O+","O-")},
        "statuses": {s: statuses.get(s, 0) for s in ("Registered","Contacted","Donated","Cancelled")},
        "donated": statuses.get("Donated", 0),
        "donation_rate": round(statuses.get("Donated", 0) / total * 100, 1) if total else 0,
        "overdue": len(overdue),
        "upcoming": sum(1 for r in records if date.fromisoformat(r["camp_date"]) >= today and r["status"] != "Cancelled"),
        "cities": len(set(r["city"].casefold() for r in records)),
    }

def import_csv(path):
    from .config import MAX_IMPORT_ROWS
    from .storage import read_csv
    from .validation import validate_donor
    from uuid import uuid4
    rows = read_csv(path)
    if len(rows) > MAX_IMPORT_ROWS:
        raise ValueError(f"Import is limited to {MAX_IMPORT_ROWS} rows.")
    existing = load_records()
    existing_keys = {(r["phone"], r["camp_date"]) for r in existing}
    imported, errors = [], []
    for line, row in enumerate(rows, start=2):
        try:
            clean = validate_donor(row)
            key = (clean["phone"], clean["camp_date"])
            if key in existing_keys:
                raise ValueError("Duplicate phone and camp date.")
            clean["id"] = "BC-" + uuid4().hex[:8].upper()
            clean["registered_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
            imported.append(clean)
            existing_keys.add(key)
        except (ValueError, TypeError) as exc:
            errors.append({"row": line, "error": str(exc)})
    existing.extend(imported)
    save_records(existing)
    append_audit("IMPORT", "BULK", f"{len(imported)} imported; {len(errors)} rejected")
    return {"imported": len(imported), "errors": errors}

def threshold_warnings():
    stats = summary()
    warnings = []
    if stats["overdue"]:
        warnings.append({"level":"warning","message":f'{stats["overdue"]} registered record(s) have a past camp date. Review their status.'})
    if stats["total"] == 0:
        warnings.append({"level":"info","message":"No registrations yet. Add a donor or load the clearly labelled demo dataset."})
    return warnings
