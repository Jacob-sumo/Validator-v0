# Data Normalization Validator — MVP

Vision
- Automate normalization checks on PII spreadsheets and produce actionable flags-only outputs.

Quick start (local CLI)
1. Create a Python 3.10+ virtualenv:
   python -m venv .venv && source .venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Run validator on a spreadsheet (Excel or CSV):
   python -m src.validator.runner --input path/to/file.xlsx --config config/rules.yml --outdir ./out

Outputs
- out/Flags.csv         (one issue per row)
- out/Summary.txt       (aggregate counts, runtime)
- out/Flagged.xlsx      (optional: flagged rows only)

MVP scope (implemented in scaffold)
- Ingest Excel or CSV
- Load YAML rule config
- Run a small set of checks (required fields, format patterns, simple SSN/email validations, duplicate detection, column presence)
- Emit Flags.csv and Summary.txt

Next steps
- Implement remaining 58 checks
- Add Azure Function trigger (HTTP + queued processing)
- Add Azure Blob storage + queue integration
- Add CI/CD and tests
- Harden for PII handling (encryption, access controls)