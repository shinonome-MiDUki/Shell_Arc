import tempfile
import time
import os

import boto3
import streamlit as st

class Cloudflare_R2_service:
    def __init__(self):
        R2_ACCESS_KEY_ID = st.secrets["CloudflareR2"]["access_key_id"]
        R2_SECRET_ACCESS_KEY = st.secrets["CloudflareR2"]["secret_access_key"]
        R2_ENDPOINT_URL = st.secrets["CloudflareR2"]["jurisdiction_specific_endpoints"]
        self.R2_BUCKET = "null-portal"

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name="auto"
        )

    def upload_file(self, uploaded_file, file_path):
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploaded_file.read())
                tmp_file_path = tmp_file.name
            
            try:
                self.s3_client.upload_file(
                    tmp_file_path,
                    self.R2_BUCKET,
                    file_path
                )
            except Exception as e:
                print(e)
                st.write("s3 client config error")
            finally:
                os.unlink(tmp_file_path)

    def download_file(self, file_naming, to_download_file, download_destination):
        try:
            self.s3_client.download_file(
                self.R2_BUCKET,
                to_download_file,
                f"{download_destination}/{file_naming}"
            )
            time.sleep(2)
            st.image(f"{download_destination}/{file_naming}")
        except Exception as e:
            print(e)
        