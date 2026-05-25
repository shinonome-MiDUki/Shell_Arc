import tempfile
import os

from shellarc_core.cloudio.io_r2 import R2_IO
from shellarc_core.cloudio.io_firebase import DB_info, DB_meta, DB_movemode, DB_status
from shellarc_core.cloudio.io_firebase import DB_IO
from shellarc_core.utils.file_operation import FileOperation as FileOp
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from shellarc_core.exception.user_exception import SA_DataNotExist, SA_InvalidUserQuery
from shellarc_core.exception.structure_error import SA_LocalIOError, SA_ErrorCode

class ShellArc_Request:
    def __init__(self,
                 cut_num: int,
                 requesting_component: str
                 ) -> None:
        self.r2_io = R2_IO()
        self.db_io = DB_IO(
            cut_num=cut_num,
            processing_component=requesting_component
        )
        self.working_component = requesting_component
        self.cut_num = cut_num
        self.cfg_io = Cfg_IO()

    def _validate_request_take(self,
                               requesting_take: int
                               ) -> None:
        if requesting_take < -1:
            raise SA_InvalidUserQuery(
                error_log=f"Incalid take num input of {requesting_take}",
                frontend_msg="テイク数は1以上、あるいは0（=最新確定テイク）、-1（=最新確認待ちテイク）でなければなりません"
            )
        current_total_take_num = int(self.db_io.get_meta_info(request_info=DB_meta.CURRENT_TAKE))
        if requesting_take > current_total_take_num:
            raise SA_InvalidUserQuery(
                error_log=f"user request take {requesting_take} while max take is {current_total_take_num}",
                frontend_msg=f"テイク{requesting_take}はまだ存在しません\n （現在のテイク数は{current_total_take_num}です）"
            )

    def download_material(self,
                         requesting_take: int
                         ) -> str:
        self._validate_request_take(requesting_take=requesting_take)
        # take = 0 : latest ; take = -1 : working
        frontend_msg_whenerror = ""
        if requesting_take == 0:
            naming = self.db_io.get_info(
                request_status=DB_status.ACTIVE,
                request_info=DB_info.NAMING
            )
            frontend_msg_whenerror = "確定データはまだありません"
        elif requesting_take == -1:
            naming = self.db_io.get_info(
                request_status=DB_status.TEMP,
                request_info=DB_info.NAMING
            )
            frontend_msg_whenerror = "作業中のデータはまだありません\n（確定済みになったかもしれませんので、「..dl 0 」でご確認ください）"
        else:
            naming = self.db_io.get_info(
                request_status=DB_status.NONACTIVE,
                request_info=DB_info.NAMING,
                request_non_active=requesting_take
            )
            frontend_msg_whenerror = f"テイク{requesting_take}が見つかりません"
        if naming is None or naming == "STATUS DICT NOT EXIST":
            raise SA_DataNotExist(
                error_log=f"Requesting a non-existing take{requesting_take}",
                frontend_msg=frontend_msg_whenerror
            )
        
        name_with_ext = f"{naming}.{self.cfg_io.get_cfg_setting(Cfg_item.COMPONENT, self.working_component, 'format')}"
        temp_dir = tempfile.mkdtemp()
        self.r2_io.download_file(
            to_download_file=f"{self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)}" \
                f"/cut{self.cut_num}/{self.working_component}/{name_with_ext}",
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
        return full_temp_path