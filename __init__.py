import logging
import os
import json
import tempfile
from azure.storage.blob import BlobServiceClient
import azure.functions as func

# Import validator engine and IO helpers from your package
from src.validator.io import load_table, write_flags_csv, write_summary, write_flagged_xlsx, write_merged_map, write_merged_dataset
from src.validator.engine import ValidatorEngine

STORAGE_CONN = os.getenv("AZURE_STORAGE_CONNECTION_STRING") or os.getenv("AzureWebJobsStorage")
OUTPUT_CONTAINER = os.getenv("OUTPUT_CONTAINER", "outputs")
RULES_PATH = os.getenv("RULES_PATH", "config/rules.yml")

def main(msg: func.QueueMessage) -> None:
    logging.info("Queue-triggered validation worker started.")
    try:
        body = msg.get_body().decode('utf-8')
        job = json.loads(body)
        upload_container = job.get("upload_container")
        upload_blob = job.get("upload_blob")
        profile = job.get("profile", "A1")
        logging.info("Processing job for blob %s/%s profile=%s", upload_container, upload_blob, profile)

        bsc = BlobServiceClient.from_connection_string(STORAGE_CONN)
        uploads_client = bsc.get_container_client(upload_container)
        outputs_client = bsc.get_container_client(OUTPUT_CONTAINER)
        try:
            outputs_client.create_container()
        except Exception:
            pass

        # download uploaded file to temp path
        with tempfile.TemporaryDirectory() as td:
            local_input = os.path.join(td, upload_blob.replace("/", "_"))
            logging.info("Downloading blob to %s", local_input)
            blob_client = uploads_client.get_blob_client(upload_blob)
            with open(local_input, "wb") as fh:
                download_stream = blob_client.download_blob()
                fh.write(download_stream.readall())

            # load df and run validator
            logging.info("Loading table and running validator engine")
            df = load_table(local_input)

            engine = ValidatorEngine(config_path=RULES_PATH, profile=profile, mask_sensitive=False)
            flags, merged_df, merged_map, runtime_ms = engine.run(df, auto_merge=True)

            # write outputs to temp files
            flags_path = os.path.join(td, "Flags.csv")
            write_flags_csv(flags, flags_path, mask_sensitive=False)

            summary = {
                "total_rows_checked": len(df),
                "total_issues": len(flags),
                "runtime_ms": runtime_ms
            }
            summary_path = os.path.join(td, "Summary.txt")
            write_summary(summary, flags, summary_path)

            flagged_xlsx_path = os.path.join(td, "Flagged.xlsx")
            write_flagged_xlsx(df, flags, flagged_xlsx_path)

            merged_map_path = os.path.join(td, "merged_map.csv")
            write_merged_map(merged_map, merged_map_path) if merged_map else None

            merged_dataset_path = os.path.join(td, "merged_dataset.csv")
            write_merged_dataset(merged_df, merged_dataset_path)

            # upload outputs to outputs container under run_id folder
            run_id = engine.run_id
            base_prefix = f"{run_id}/"
            def upload_file(local_path, blob_name):
                target_blob = outputs_client.get_blob_client(base_prefix + blob_name)
                with open(local_path, "rb") as fh:
                    target_blob.upload_blob(fh, overwrite=True)
                logging.info("Uploaded %s to outputs/%s", local_path, base_prefix + blob_name)

            upload_file(flags_path, "Flags.csv")
            upload_file(summary_path, "Summary.txt")
            upload_file(flagged_xlsx_path, "Flagged.xlsx")
            if merged_map:
                upload_file(merged_map_path, "merged_map.csv")
            upload_file(merged_dataset_path, "merged_dataset.csv")

            logging.info("Validation job %s complete; outputs uploaded to container %s/%s", run_id, OUTPUT_CONTAINER, base_prefix)
    except Exception as e:
        logging.exception("Worker failure")
        raise