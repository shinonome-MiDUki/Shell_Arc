import tempfile
import time
import os

import boto3

class Cloudflare_R2_service_Access:
    def __init__(self):
        try:
            import streamlit as st
            R2_ACCESS_KEY_ID = st.secrets["CloudflareR2"]["access_key_id"]
            R2_SECRET_ACCESS_KEY = st.secrets["CloudflareR2"]["secret_access_key"]
            R2_ENDPOINT_URL = st.secrets["CloudflareR2"]["jurisdiction_specific_endpoints"]
        except:
            from dotenv import load_dotenv
            load_dotenv(verbose=True)
            dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
            load_dotenv(dotenv_path)
            R2_ACCESS_KEY_ID = os.environ.get("CloudflareR2_access_key_id")
            R2_SECRET_ACCESS_KEY = os.environ.get("CloudflareR2_secret_access_key")
            R2_ENDPOINT_URL = os.environ.get("CloudflareR2_jurisdiction_specific_endpoints")

        self._s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name="auto"
        )

    @property
    def s3_client(self):
        return self._s3_client
        