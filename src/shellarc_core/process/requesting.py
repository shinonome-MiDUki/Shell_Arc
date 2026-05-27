import tempfile
import os

from shellarc_core.cloudio.io_r2 import R2_IO
from shellarc_core.cloudio.io_git import Git_IO, ShellArcGitBranch
from shellarc_core.utils.file_operation import FileOperation as FileOp
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from shellarc_core.exception.user_exception import SA_DataNotExist, SA_InvalidUserQuery
from shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_LocalIOError, SA_ErrorCode
)

class ShellArc_Request:
    def __init__(self,
                 cut_num: int,
                 requesting_component: str
                 ) -> None:
        self.r2_io = R2_IO()
        self.git_io = Git_IO()
        self.cfg_io = Cfg_IO()
        self.working_component = requesting_component
        self.cut_num = cut_num

    async def download_material(self,
                                requesting_take: str
                                ) -> tuple[str]:
        # take = 0 : latest ; take = -1 : working
        frontend_msg_whenerror = ""
        if requesting_take == "0":
            branch = ShellArcGitBranch.MAIN
            commit_id = None
            frontend_msg_whenerror = "確定データはまだありません"
        elif requesting_take == "-1":
            branch = ShellArcGitBranch.PENDING
            commit_id = None
            frontend_msg_whenerror = "作業中のデータはまだありません\n（確定済みになったかもしれませんので、「..dl」でご確認ください）"
        else:
            branch = ShellArcGitBranch.PENDING
            commit_id = requesting_take
            frontend_msg_whenerror = f"履歴ID:{requesting_take}が見つかりません"
        component_info = await self.git_io.get_component_info(
            branch=branch,
            cut_num=self.cut_num,
            component=self.working_component,
            commit_id=commit_id
        )
        if component_info == {}:
            raise SA_DataNotExist(
                error_log=f"Requesting a non-existing take {requesting_take}",
                frontend_msg=frontend_msg_whenerror
            )
        naming = component_info.get("fileindex", None)
        if naming is None:
            raise SA_ProjStructError(
                error_log="fileindex not exist in component json file",
                error_code=SA_ErrorCode.SA_6002
            )
        
        name_with_ext = f"{naming}.{self.cfg_io.get_cfg_setting(Cfg_item.COMPONENT, self.working_component, 'format')}"
        temp_dir = tempfile.mkdtemp()
        target_file_s3path = f"{self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)}/stage/{name_with_ext}"
        target_file_size = self.r2_io.get_s3obj_size(target_s3_file=target_file_s3path)
        if target_file_size > 9:
            presigned_url = self.r2_io.issue_presigned_url(
                target_s3_file=target_file_s3path,
                url_client_method="get_object",
                http_method="GET",
                time_limit=180
            )
            return (presigned_url, name_with_ext, "url")
        else:
            self.r2_io.download_file(
                to_download_file=target_file_s3path,
                download_destination=temp_dir,
                file_naming=name_with_ext
            )
            full_temp_path = os.path.join(temp_dir, name_with_ext)
            if not os.path.exists(full_temp_path):
                raise SA_LocalIOError(
                    error_log=f"making temp file for file download for " \
                        f"c{self.cut_num}{self.working_component}, but temp file disappear",
                    error_code=SA_ErrorCode.SA_8000
                )
            return (full_temp_path, name_with_ext, "path")