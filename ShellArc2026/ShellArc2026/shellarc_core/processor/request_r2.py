import tempfile
import time
import datetime
import os
from pathlib import Path
from typing import Any

import boto3

from ..keys.decoder import get_creds

class Cloudflare_R2_service:
    def __init__(self, 
                 s3_client: boto3.client
                 ) -> None:
        self.s3_client = s3_client
        self.R2_BUCKET = "null-portal"

    def check_existence(self,
                        checking_file: str
                        ) -> bool:
        checking_dir = str(Path(checking_file).resolve().parent) + "/"
        checking_file_name = Path(checking_file).name
        obj_list = self.s3_client.list_objects(
            Bucket=self.R2_BUCKET, 
            Prefix= checking_dir
            )
        return checking_file in obj_list
            

    def upload_file(self, 
                    local_file_path: str, 
                    cloud_file_path: str
                    ) -> bool:
        try:
            self.s3_client.upload_file(
                local_file_path,
                self.R2_BUCKET,
                cloud_file_path
            )
            return True
        except Exception as e:
            print(f"File upload failed, datetime : {datetime.datetime.now()}, error: {e}")
            return False

    def download_file(self, 
                      to_download_file: str, 
                      download_dest: str,
                      file_naming: str
                      ) -> bool:
        # if not self.check_existence(to_download_file):
        #     print("object not exist")
        #     return False
        try:
            self.s3_client.download_file(
                self.R2_BUCKET,
                to_download_file,
                f"{download_dest}/{file_naming}"
            )
            time.sleep(1)
            return True
        except Exception as e:
            print(f"File download failed, datetime : {datetime.datetime.now()}, error: {e}")
            return False