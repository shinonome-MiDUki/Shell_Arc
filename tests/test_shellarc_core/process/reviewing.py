from test_shellarc_core.cloudio.io_firebase import DB_info, DB_meta, DB_movemode, DB_status
from test_shellarc_core.cloudio.io_firebase import DB_IO
from test_shellarc_core.cloudio.io_spreadsheet import GCP_IO
from test_shellarc_core.utils.file_operation import FileOperation as FileOp
from test_shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item

from test_shellarc_core.exception.user_exception import SA_InvalidRequestObj

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

    def approve_action(self,
                       reviewer_name: str
                       ) -> dict:
        self._existence_check(reviewer_name=reviewer_name)
        structure = self.db_io.move_data_block(move_mode=DB_movemode.TEMP2ACTIVE)
        structure = self.db_io.set_info(
            structure=structure,
            setting_status=DB_status.ACTIVE,
            setting_info=DB_info.REVIEWER,
            new_value=reviewer_name,
        )
        check_pt_1 = self.db_io.update_remote(structure=structure)

        check_pt_2 = self.gcp_io.update_info(
            info_type=f"{self.reviewing_component}_progress",
            cut_num=self.cut_num,
            new_value="完了"
        )
        check_pt_2 = list(check_pt_2)
        return {"cp1" : check_pt_1, "cp2" : check_pt_2}

    def decline_action(self,
                      reviewer_name: str
                      ) -> dict:
        self._existence_check(reviewer_name=reviewer_name)
        current_temp_data = self.db_io.get_status_dict(request_status=DB_status.TEMP)
        structure = self.db_io.set_info(
            structure={DB_status.TEMP.value : current_temp_data},
            setting_status=DB_status.TEMP,
            setting_info=DB_info.REVIEWER,
            new_value=reviewer_name,
        )
        structure = self.db_io.move_data_block(
            move_mode=DB_movemode.TEMP2NONACTIVE,
            structure=structure
            )
        check_pt = self.db_io.update_remote(structure=structure)
        return check_pt
        