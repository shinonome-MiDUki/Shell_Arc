import tempfile
import datetime
import os
import time
from typing import Any
from pathlib import Path

import boto3

from shellarc_core.auth.access_r2 import Cloudflare_R2_service_Access as A_R2
from shellarc_core.cfg.cfg_io import Cfg_IO as Cfg_IO
from shellarc_core.cfg.cfg_io import Cfg_item
from shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_CommunicationError, SA_ErrorCode
)

class R2_IO:
    def __init__(self):
        a_r2 = A_R2()
        self.s3_client = a_r2.s3_client
        cfg_io = Cfg_IO()
        self.bucket_name = cfg_io.get_cfg_setting(Cfg_item.BUCKET_NAME)

    def get_s3obj_size(self,
                       target_s3_file: str
                       ) -> int:
        s3_obj = self.s3_client.get_object(
            Bucket=self.bucket_name,
            Key=target_s3_file,
        )
        size_bytes = float(s3_obj.get('Size'))
        size_mb = size_bytes / 1024 / 1024
        return int(size_mb)

    def issue_presigned_url(self,
                            target_s3_file: str,
                            url_client_method: str,
                            http_method: str,
                            time_limit: int=180
                            ) -> str:
        presigned_url = self.s3_client.generate_presigned_url(
            ClientMethod=url_client_method,
            Params={
                "Bucket" : self.bucket_name,
                "Key" : target_s3_file
            },
            ExpiresIn=time_limit,
            HttpMethod=http_method
        )
        return presigned_url
        

    def upload_file(self,
                    uploading_file: bytes | str | Path,
                    file_path: str | Path
                    ) -> None:
        if isinstance(file_path, Path):
            file_path = str(file_path)
        if uploading_file is None:
            raise SA_ProjStructError(
                error_log="Uploading file to R2 storage is None",
                error_code=SA_ErrorCode.SA_5101
            )
        if isinstance(uploading_file, bytes):
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                tmp_file.write(uploading_file)
                tmp_file_path = tmp_file.name
        else:
            if isinstance(uploading_file, Path):
                uploading_file = str(uploading_file)
            tmp_file_path = uploading_file
        try:
            self.s3_client.upload_file(
                tmp_file_path,
                self.bucket_name,
                file_path
            )
        except Exception as e:
            raise SA_CommunicationError(
                error_log=f"Communication error with R2 when uploading [{e}]",
                error_code=SA_ErrorCode.SA_8001
            )
        finally:
            os.unlink(tmp_file_path)

    def download_file(self,
                      to_download_file: str,
                      download_destination: str,
                      file_naming: str
                      ) -> None:
        try:
            self.s3_client.download_file(
                self.bucket_name,
                to_download_file,
                f"{download_destination}/{file_naming}"
            )
            time.sleep(1)
        except Exception as e:
            raise SA_CommunicationError(
                error_log=f"Communication error with R2 when downloading [{e}]",
                error_code=SA_ErrorCode.SA_8001
            )

    