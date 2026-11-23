# BloodCare — Blood Donation Camp Register

A local-first Python application with a responsive web dashboard and the required menu-driven terminal interface. Built against the supplied GreenFuture Hack Project #73 brief.

## 1. Requirements covered

### Must-have
- Menu-driven Python terminal interface (`python cli.py`)
- Centralized input validation, sanitization and boundary checks
- Registration business logic and blood-group counts
- Persistent JSON and CSV storage; atomic JSON writes and recovery from malformed JSON
- Keyword, blood-group, city and status search/filtering
- Executive summary: totals, average age, status counts, donation rate, overdue and upcoming indicators

### Stretch features
- CSV, Markdown and plain-text audit exports
- Threshold warning indicators for overdue registrations
- Responsive browser GUI (HTML/CSS/JavaScript) served by Python's standard-library HTTP server
- Bulk CSV import with row-by-row validation errors
- Optional Matplotlib PNG report (install `requirements-optional.txt`); dashboard has a built-in Canvas chart without dependencies

### Additional engineering
- Modular separation: validation, storage, services, reporting, CLI and web server
- Edit/delete workflows, duplicate prevention, audit events
- JSON API, safe DOM text rendering, request-size limit, local-only binding
- Automated unit and service tests

## 2. Run the website

Python 3.10+ is recommended. No mandatory third-party packages.

```bash
python main.py
```

Open **http://127.0.0.1:8000** in your browser. Keep the terminal window open while using the website. Press `Ctrl+C` to stop.

## 3. Run the terminal application

In a second terminal:

```bash
python cli.py
```

## 4. Run automated tests

```bash
python -m unittest discover -s tests -v
```

## 5. Optional Matplotlib chart

```bash
python -m pip install -r requirements-optional.txt
```

Use **Generate reports** in the dashboard or option 5 in the CLI. The report generator creates CSV, Markdown, audit text and (when Matplotlib is installed) a PNG blood-group chart in `reports/`.

## 6. Demo data

The project includes 40 synthetic demo records in:
- `data/demo_donors.json`
- `data/demo_donors.csv`

The live application starts with an empty register so the evaluator can demonstrate a clean registration flow. To load the demo set, copy `data/demo_donors.json` over `data/donors.json` before launching, or import `data/demo_donors.csv` through the dashboard. Demo phone numbers are synthetic placeholders, not contact details.

## 7. Data model

Each record contains:
`id, name, age, gender, phone, blood_group, city, camp_date, registered_at, status`

Allowed blood groups: A+, A-, B+, B-, AB+, AB-, O+, O-.
Statuses: Registered, Contacted, Donated, Cancelled.
The prototype enforces an age range of 18–65 for data quality; this is an administrative validation rule for the demonstration, not a medical eligibility decision.

## 8. Storage and recovery

`data/donors.json` is the canonical application store. Every successful mutation updates the JSON store and a CSV mirror. JSON writes use a temporary file and atomic replacement. If the JSON file is malformed, it is preserved as `donors.corrupt.json` and a clean store is initialized. `data/audit.log` records create, update, delete and import actions.

## 9. Demo walkthrough (suggested)
1. Start `python main.py`; open the local dashboard.
2. Register a donor with valid data.
3. Try an invalid age, malformed mobile number or missing field to show validation.
4. Search by donor name and filter by blood group/status.
5. Edit the status to `Donated`; observe the dashboard metrics and chart update.
6. Import `data/demo_donors.csv` to show bulk import and row-level validation.
7. Generate reports; inspect the `reports/` directory.
8. Stop and restart the app; verify registrations persist.
9. Run `python cli.py` to demonstrate the required terminal workflow.
10. Run automated tests with the command above.

## 10. API overview
- `GET /api/health`
- `GET /api/donors?q=&blood_group=&status=&city=`
- `GET /api/summary`
- `GET /api/reports`
- `POST /api/donors`
- `PUT /api/donors/{id}`
- `DELETE /api/donors/{id}`
- `POST /api/import` (JSON body with `csv` text)

## 11. Important scope note
This is a local academic prototype, not a production medical system. It does not assess donor fitness, match recipients, store clinical records or provide medical advice. It binds to `127.0.0.1` and is not intended to be exposed to a public network without authentication, HTTPS, CSRF protection, access controls and a security review.
