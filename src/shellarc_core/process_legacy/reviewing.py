from shellarc_core.cloudio_legacy.io_firebase import DB_info, DB_meta, DB_movemode, DB_status
from shellarc_core.cloudio_legacy.io_firebase import DB_IO
from shellarc_core.cloudio_legacy.io_spreadsheet import GCP_IO
from shellarc_core.utils.file_operation import FileOperation as FileOp
from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from shellarc_core.exception.user_exception import SA_InvalidRequestObj

class ShellArc_Review:
    def __init__(self,
                 cut_num: int,
                 reviewing_component: str
                 ) -> None:
        
        self.db_io = DB_IO(
            cut_num=cut_num,
            processing_component=reviewing_component
        )
        self.gcp_io = GCP_IO()
        self.cfg_io = Cfg_IO()
        self.cut_num = cut_num
        self.reviewing_component = reviewing_component

    def _existence_check(self,
                         reviewer_name: str
                         ) -> None:
        current_temp = self.db_io.get_info(
            request_status=DB_status.TEMP,
            request_info=DB_info.NAMING,
        )
        if current_temp is None:
            raise SA_InvalidRequestObj(
                error_log=f"not yet existing tempdata requester by {reviewer_name}",
                frontend_msg="確認待ちのカットはありません"
            )

    async def approve_action(self,
                       reviewer_name: str
                       ) -> None:
        self._existence_check(reviewer_name=reviewer_name)
        structure = self.db_io.move_data_block(move_mode=DB_movemode.TEMP2ACTIVE)
        structure = self.db_io.set_info(
            structure=structure,
            setting_status=DB_status.ACTIVE,
            setting_info=DB_info.REVIEWER,
            new_value=reviewer_name,
        )
        self.db_io.update_remote(structure=structure)

        self.gcp_io.update_info(
            info_type=f"{self.reviewing_component}_progress",
            cut_num=self.cut_num,
            new_value="完了"
        )

    async def decline_action(self,
                      reviewer_name: str
                      ) -> None:
        self._existence_check(reviewer_name=reviewer_name)
        current_temp_data = self.db_io.get_status_dict(request_status=DB_status.TEMP)
        structure = self.db_io.set_info(
            structure={DB_status.TEMP : current_temp_data},
            setting_status=DB_status.TEMP,
            setting_info=DB_info.REVIEWER,
            new_value=reviewer_name,
        )
        structure = self.db_io.move_data_block(
            move_mode=DB_movemode.TEMP2NONACTIVE,
            structure=structure
            )
        self.db_io.update_remote(structure=structure)
        