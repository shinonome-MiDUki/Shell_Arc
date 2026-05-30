import os
import tempfile
from pathlib import Path

from shellarc_core.cloudio.io_r2 import R2_IO
from shellarc_core.cloudio.io_git import Git_IO
from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.utils.file_operation import FileOperation
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from shellarc_core.exception.user_exception import SA_InvalidUserQuery

class ShellArc_Upload:
    def __init__(self,
                 cut_num: int,
                 working_component: str
                 ) -> None:
        self.r2_io = R2_IO()
        self.git_io = Git_IO()
        self.gcp_io = GCP_IO()
        self.cfg_io = Cfg_IO()
        self.working_component = working_component
        self.cut_num = cut_num

    async def upload_file(self,
                    file: dict[str, bytes],
                    submitter_name: str,
                    message: str=""
                    ) -> None:
        required_format = self.cfg_io.get_cfg_setting(Cfg_item.COMPONENT, self.working_component, "format")
        filename = ""
        if len(file) > 1 and required_format == "zip":
            fileobj = await FileOperation.make_zip(
                files=file,
                required_format=required_format
                )
            filename = Path(fileobj).name
        elif len(file) > 1 and required_format != "zip":
            raise SA_InvalidUserQuery(
                error_log=f"file with invalid extension format uploaded by {submitter_name}",
                frontend_msg=f"{required_format}形式でご提出ください"
            )
        elif len(file) == 1:
            filename, fileobj= file.popitem()
        else:
            raise Exception
        submission_format = Path(filename).suffix.lstrip(".")

        try:
            if submission_format != required_format:
                raise SA_InvalidUserQuery(
                    error_log=f"file with invalid extension format uploaded by {submitter_name}",
                    frontend_msg=f"{required_format}形式でご提出ください"
                )
            collection_name = self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)

            file_index_name = await self.git_io.update_data(
                cut_num=self.cut_num,
                component=self.working_component,
                creator_name=submitter_name,
                message=message
            )

            self.r2_io.upload_file(
                uploading_file=fileobj,
                file_path=f"{collection_name}/stage/{file_index_name}.{required_format}"
            )
        except Exception as e:
            raise
        finally:
            if Path(filename).exists():
                os.unlink(filename)

        self.gcp_io.update_info(
            info_type=f"{self.working_component}_PIC",
            cut_num=self.cut_num,
            new_value=submitter_name
        )
        self.gcp_io.update_info(
            info_type=f"{self.working_component}_progress",
            cut_num=self.cut_num,
            new_value="作業中"
        )
        self.gcp_io.color_cell(
            info_type=f"{self.working_component}_PIC",
            cut_num=self.cut_num,
            target_color=(1, 1, 0)
        )


    async def _get_upload_url(self,
                             submitter_name: str,
                             message: str=""
                             ) -> str:
        required_format = self.cfg_io.get_cfg_setting(Cfg_item.COMPONENT, self.working_component, "format")
        collection_name = self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)

        file_index_name = await self.git_io.update_data(
            cut_num=self.cut_num,
            component=self.working_component,
            creator_name=submitter_name,
            message=message
        )

        presigned_url = self.r2_io.issue_presigned_url(
            target_s3_file=f"{collection_name}/stage/{file_index_name}.{required_format}",
            url_client_method="put_object",
            http_method="PUT",
            time_limit=300
        )

        self.gcp_io.update_info(
            info_type=f"{self.working_component}_PIC",
            cut_num=self.cut_num,
            new_value=submitter_name
        )
        self.gcp_io.update_info(
            info_type=f"{self.working_component}_progress",
            cut_num=self.cut_num,
            new_value="作業中"
        )

        return presigned_url
    
    async def get_upload_page(self,
                              submitter_name: str,
                              message: str
                              ) -> tuple[str]:
        presigned_url = await self._get_upload_url(
            submitter_name=submitter_name,
            message=message
        )
        with open("uploader_from_url.html.template", "r", encoding="utf-8") as f:
            html_template = f.read()
        html_page_code = html_template.replace("__S3_PRESIGNED_URL_PLACEHOLDER_XYZ__", presigned_url)
        temp_dir = tempfile.mkdtemp()
        html_path = Path(temp_dir) / f"cut{self.cut_num}_uploader.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_page_code)
        return (str(html_path), temp_dir)


    @staticmethod
    async def sync_vps_with_remote() -> None:
        await Git_IO().sync_remote()