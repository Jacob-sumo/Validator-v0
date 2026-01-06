# Azure Functions - Data Normalization Validator (MVP)

How it works
- HTTP upload function receives a file (raw bytes) and enqueues a validation job.
- Queue worker processes the job, runs the validator (src/validator), and uploads outputs to Blob Storage.

HTTP upload contract
- URL: https://<functionapp>.azurewebsites.net/api/http_upload
- Method: POST
- Body: raw file bytes (no multipart parsing in this MVP)
- Headers:
  - X-Filename: filename.ext  (required)
  - X-Profile: A1 | TP | HSID  (optional; defaults to A1)
- Response: 202 accepted with JSON { status, blob, profile }

Queues & Containers
- Uploads go to container: uploads (configurable via UPLOAD_CONTAINER setting)
- Outputs are uploaded to container: outputs under a per-run folder (run_id/)
- Queue name: validation-jobs (configurable via QUEUE_NAME)

Local testing
- Use local.settings.json with AZURE_STORAGE_CONNECTION_STRING pointing to an accessible storage account (or Azurite during dev).
- Start Functions host locally: func start
- Upload via curl:
  curl -X POST --data-binary @sample.xlsx -H "X-Filename: sample.xlsx" -H "X-Profile: A1" http://localhost:7071/api/http_upload

Deployment
- Use the provided GitHub Actions workflow; set repository secrets:
  - AZURE_FUNCTIONAPP_NAME
  - AZURE_SUBSCRIPTION
  - AZURE_CREDENTIALS (if using azure/login)
- Or deploy via `func azure functionapp publish <APP_NAME>` from CLI.