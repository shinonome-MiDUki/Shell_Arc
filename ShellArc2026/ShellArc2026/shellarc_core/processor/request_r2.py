import tempfile
import time
import datetime
import os
from pathlib import Path
from typing import Any

import boto3

class Cloudflare_R2_service:
    def __init__(self, 
                 s3_client: boto3.client, 
                 bucket_name: str
                 ) -> None:
        self.s3_client = s3_client
        self.R2_BUCKET = bucket_name

    def upload_file(self, 
                    uploaded_file: Any, 
                    file_path: str
                    ) -> None:
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
                print(f"File upload failed, datetime : {datetime.datetime.now()}, error: {e}")
            finally:
                os.unlink(tmp_file_path)

    def download_file(self, 
                      to_download_file: str, 
                      download_dest: str,
                      file_naming: str
                      ) -> None:
        try:
            self.s3_client.download_file(
                self.R2_BUCKET,
                to_download_file,
                f"{download_dest}/{file_naming}"
            )
            time.sleep(1)
        except Exception as e:
            print(f"File download failed, datetime : {datetime.datetime.now()}, error: {e}")