import tempfile
import datetime
import os
import time
from typing import Any
from pathlib import Path

from test_shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from test_shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_CommunicationError, SA_ErrorCode
)

class R2_IO:
    def __init__(self):
        cfg_io = Cfg_IO()
        self.bucket_name = cfg_io.get_cfg_setting(Cfg_item.BUCKET_NAME)

    def upload_file(self,
                    file,
                    uploading_file: Any,
                    file_path: str | Path
                    ) -> str:
        # if isinstance(file_path, Path):
        #     file_path = str(file_path)
        # if uploading_file is None:
        #     raise SA_ProjStructError(
        #         error_log="Uploading file to R2 storage is None",
        #         error_code=SA_ErrorCode.SA_5101
        #     )
        # with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        #     tmp_file.write(uploading_file.read())
        #     tmp_file_path = tmp_file.name
        # os.unlink(tmp_file_path)
        return "UPLOADED TO R2"

    def download_file(self,
                      to_download_file: str,
                      download_destination: str,
                      file_naming: str
                      ) -> str:
        return "DOWNLOADED FROM R2"

    