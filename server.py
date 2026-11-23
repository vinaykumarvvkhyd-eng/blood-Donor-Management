"""Zero-dependency local HTTP API and static website server."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import json, mimetypes, shutil, tempfile
from .config import BASE_DIR, HOST, PORT, APP_NAME, APP_VERSION
from .storage import ensure_storage
from .services import (all_donors, add_donor, update_donor, delete_donor,
                       search_donors, summary, threshold_warnings, import_csv)
from .reports import export_all, create_matplotlib_chart

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "static"), **kwargs)

    def log_message(self, fmt, *args):
        # Keep console logs concise; avoid logging request bodies/PII.
        print("[BloodCare]", fmt % args)

    def send_json(self, status, data):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self'")
        self.end_headers()
        self.wfile.write(raw)

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2_000_000:
            raise ValueError("Request body exceeds 2 MB.")
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8")) if raw else {}

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/health":
                return self.send_json(200, {"app": APP_NAME, "version": APP_VERSION, "status": "ok"})
            if path == "/api/donors":
                params = parse_qs(parsed.query)
                return self.send_json(200, search_donors(
                    params.get("q", [""])[0], params.get("blood_group", [""])[0],
                    params.get("status", [""])[0], params.get("city", [""])[0]))
            if path == "/api/summary":
                return self.send_json(200, {"summary": summary(), "warnings": threshold_warnings()})
            if path == "/api/reports":
                files = export_all()
                chart = create_matplotlib_chart()
                names = [Path(item).name for item in files]
                return self.send_json(200, {"files": names, "chart": Path(chart).name if chart else None})
            if path.startswith("/download/"):
                name = Path(path.rsplit("/", 1)[-1]).name
                target = (BASE_DIR / "reports" / name).resolve()
                reports_root = (BASE_DIR / "reports").resolve()
                if target.parent != reports_root or not target.is_file():
                    return self.send_json(404, {"error": "Report not found."})
                raw = target.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
                self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(raw)
                return
            if path == "/":
                self.path = "/index.html"
            return super().do_GET()
        except Exception as exc:
            return self.send_json(500, {"error": str(exc)})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/donors":
                donor = add_donor(self.read_body())
                return self.send_json(201, donor)
            if path == "/api/import":
                form = self.read_body()
                content = form.get("csv", "")
                if not isinstance(content, str) or len(content) > 2_000_000:
                    raise ValueError("Invalid CSV upload.")
                temp = tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", suffix=".csv", delete=False)
                try:
                    temp.write(content); temp.close()
                    result = import_csv(temp.name)
                finally:
                    Path(temp.name).unlink(missing_ok=True)
                return self.send_json(200, result)
            return self.send_json(404, {"error": "Endpoint not found."})
        except ValueError as exc:
            return self.send_json(400, {"error": str(exc)})
        except Exception as exc:
            return self.send_json(500, {"error": "The request could not be completed."})

    def do_PUT(self):
        try:
            path = urlparse(self.path).path
            if path.startswith("/api/donors/"):
                record_id = path.rsplit("/", 1)[-1]
                return self.send_json(200, update_donor(record_id, self.read_body()))
            return self.send_json(404, {"error": "Endpoint not found."})
        except ValueError as exc: return self.send_json(400, {"error": str(exc)})
        except KeyError as exc: return self.send_json(404, {"error": str(exc)})
        except Exception: return self.send_json(500, {"error": "The request could not be completed."})

    def do_DELETE(self):
        try:
            path = urlparse(self.path).path
            if path.startswith("/api/donors/"):
                delete_donor(path.rsplit("/", 1)[-1])
                return self.send_json(200, {"deleted": True})
            return self.send_json(404, {"error": "Endpoint not found."})
        except KeyError as exc: return self.send_json(404, {"error": str(exc)})
        except Exception: return self.send_json(500, {"error": "The request could not be completed."})

def main():
    ensure_storage()
    print(f"\n{APP_NAME} {APP_VERSION} is running at http://{HOST}:{PORT}")
    print("Local-only server. Press Ctrl+C to stop.")
    try:
        ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nBloodCare server stopped.")

if __name__ == "__main__":
    main()
