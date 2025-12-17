import tempfile
import time
import os

import boto3

class Cloudflare_R2_service:
    def __init__(self, s3_client):
        self.s3_client = s3_client
        self.R2_BUCKET = "null-portal"

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
            try:
                import streamlit as st
                st.image(f"{download_destination}/{file_naming}")
            except: pass
        except Exception as e:
            print(e)