from pathlib import Path
import tempfile

from shellarc_core.cloudio.io_r2 import R2_IO
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from shellarc_core.exception.structure_error import SA_ErrorCode, SA_LocalIOError
from shellarc_core.exception.user_exception import SA_InvalidUserQuery


class ShellArc_Storyboard:
    def __init__(self,
                 cut_num: int
                 ) -> None:
        self.r2_io = R2_IO()
        self.cfg_io = Cfg_IO()
        self.cut_num = cut_num

    async def upload_storyboard(self,
                                file: tuple[str, bytes]
                                ) -> None:
        submission_format = Path(file[0]).suffix.lstrip(".")
        if submission_format != ".png":
            raise SA_InvalidUserQuery(
                error_log="Storyboard lo not in png format",
                frontend_msg="png形式で提出してください"
            )
        fileobj = file[1]
        collection_name = self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)
        self.r2_io.upload_file(
            uploading_file=fileobj,
            file_path=f"{collection_name}/stage/cut{self.cut_num}_layout.{submission_format}"
        )


    async def download_storyboard(self) -> tuple:
        naming = f"cut{self.cut_num}_layout.png"
        name_with_ext = f"{naming}.{self.cfg_io.get_cfg_setting(Cfg_item.COMPONENT, self.working_component, 'format')}"
        temp_dir = tempfile.mkdtemp()
        collection_name = self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)
        target_file_s3path = f"{collection_name}/storyboard/{name_with_ext}"
        self.r2_io.download_file(
            to_download_file=target_file_s3path,
            download_destination=temp_dir,
            file_naming=name_with_ext
        )
        full_temp_path = Path(temp_dir) / name_with_ext
        if not full_temp_path.exists():
            raise SA_LocalIOError(
                error_log=f"making temp file for file download for " \
                    f"c{self.cut_num}{self.working_component}, but temp file disappear",
                error_code=SA_ErrorCode.SA_8000
            )
        return (full_temp_path, name_with_ext)

