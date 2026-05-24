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

    def upload_file(self,
                    uploading_file: Any,
                    file_path: str | Path
                    ) -> None:
        if isinstance(file_path, Path):
            file_path = str(file_path)
        if uploading_file is None:
            raise SA_ProjStructError(
                error_log="Uploading file to R2 storage is None",
                error_code=SA_ErrorCode.SA_5101
            )
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploading_file.read())
            tmp_file_path = tmp_file.name
        try:
            self.s3_client.upload_file(
                tmp_file_path,
                self.bucket_name,
                file_path
            )
        except Exception as e:
            raise SA_CommunicationError(
                error_log=f"Communication error with R2 when uploading [{e}]",
                error_code=SA_ErrorCode.SA_5102
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
                error_code=SA_ErrorCode.SA_5102
            )

    