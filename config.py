from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
DONORS_JSON = DATA_DIR / "donors.json"
DONORS_CSV = DATA_DIR / "donors.csv"
AUDIT_LOG = DATA_DIR / "audit.log"
HOST = "127.0.0.1"
PORT = 8000
APP_NAME = "BloodCare"
APP_VERSION = "1.0.0"
MAX_IMPORT_ROWS = 5000
