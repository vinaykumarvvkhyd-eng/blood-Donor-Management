"""Fault-tolerant local JSON/CSV persistence."""
import csv, json, os, tempfile
from pathlib import Path
from .config import DATA_DIR, DONORS_JSON, DONORS_CSV, AUDIT_LOG

FIELDS = ["id", "name", "age", "gender", "phone", "blood_group", "city",
          "camp_date", "registered_at", "status"]

def ensure_storage():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DONORS_JSON.exists():
        atomic_json_write(DONORS_JSON, [])
    if not DONORS_CSV.exists():
        write_csv([])

def atomic_json_write(path, records):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="bloodcare_", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(records, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try: os.unlink(temp_name)
        except OSError: pass
        raise

def load_records():
    ensure_storage()
    try:
        with DONORS_JSON.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, list):
            raise ValueError("JSON root must be a list.")
        return [r for r in data if isinstance(r, dict) and all(k in r for k in FIELDS)]
    except (json.JSONDecodeError, OSError, ValueError):
        # Preserve damaged content for inspection, then recover with a clean store.
        if DONORS_JSON.exists():
            backup = DONORS_JSON.with_suffix(".corrupt.json")
            try: os.replace(DONORS_JSON, backup)
            except OSError: pass
        atomic_json_write(DONORS_JSON, [])
        return []

def save_records(records):
    atomic_json_write(DONORS_JSON, records)
    write_csv(records)

def write_csv(records, path=DONORS_CSV):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("CSV file is empty or has no header.")
        required = set(FIELDS) - {"id", "registered_at"}
        missing = required - set(reader.fieldnames)
        if missing:
            raise ValueError("Missing CSV columns: " + ", ".join(sorted(missing)))
        return list(reader)

def append_audit(action, record_id, details=""):
    AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
    safe = str(details).replace("\n", " ").replace("\r", " ")[:180]
    with AUDIT_LOG.open("a", encoding="utf-8") as handle:
        from datetime import datetime
        handle.write(f"{datetime.now().astimezone().isoformat()} | {action} | {record_id} | {safe}\n")
