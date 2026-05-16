import tempfile
import datetime
import os
from pathlib import Path

from dotenv import load_dotenv
import boto3

class Cloudflare_R2_service_Access:
    def __init__(self):
        load_dotenv(verbose=True)
        dotenv_path = Path(__file__).resolve().parents[3] / 'project_ctx/.env'
        load_dotenv(dotenv_path)
        R2_ACCESS_KEY_ID = os.environ.get("CloudflareR2_access_key_id")
        R2_SECRET_ACCESS_KEY = os.environ.get("CloudflareR2_secret_access_key")
        R2_ENDPOINT_URL = os.environ.get("CloudflareR2_jurisdiction_specific_endpoints")

        try:
            self._s3_client = boto3.client(
                "s3",
                endpoint_url=R2_ENDPOINT_URL,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name="auto"
            )
        except Exception as e:
            print(f"Cloudflare R2 access error, datetime : {datetime.datetime.now()}, error: {e}")
            self._s3_client = None

    @property
    def s3_client(self):
        return self._s3_client
        