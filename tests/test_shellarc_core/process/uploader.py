from test_shellarc_core.cloudio.io_r2 import R2_IO
from test_shellarc_core.cloudio.io_firebase import DB_info, DB_meta, DB_movemode, DB_status
from test_shellarc_core.cloudio.io_firebase import DB_IO
from test_shellarc_core.cloudio.io_spreadsheet import GCP_IO
from test_shellarc_core.utils.file_operation import FileOperation as FileOp
from test_shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from test_shellarc_core.exception.user_exception import SA_InvalidUserQuery

class ShellArc_Upload:
    def __init__(self,
                 cut_num: int,
                 working_component: str
                 ) -> None:
        self.r2_io = R2_IO()
        self.db_io = DB_IO(
            cut_num=cut_num,
            processing_component=working_component
        )
        self.gcp_io = GCP_IO()
        self.working_component = working_component
        self.cut_num = cut_num
        self.cfg_io = Cfg_IO()

    def upload_file(self,
                    file: str,
                    format: str,
                    submitter_name: str
                    ) -> dict:
        current_take_num = int(self.db_io.get_meta_info(request_info=DB_meta.CURRENT_TAKE)) + 1
        naming = FileOp.renamed(
            cut_num=self.cut_num,
            take=current_take_num,
            component=self.working_component
        )
        check_pt_1 = naming
        required_format = self.cfg_io.get_cfg_setting(Cfg_item.COMPONENT, self.working_component, "format")
        if format != required_format:
            raise SA_InvalidUserQuery(
                error_log=f"file with invalid extension format uploaded by {submitter_name}",
                frontend_msg=f"{required_format}形式でご提出ください"
            )
        collection_name = self.cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)
        new_temp_data = self.db_io.make_data_block(
            naming=naming,
            cut=str(self.cut_num),
            take=current_take_num,
            creator=submitter_name
        )
        print(f"s1s1s1s1@{new_temp_data}")
        structure = self.db_io.move_data_block(
            move_mode=DB_movemode.TEMP2NONACTIVE,
            new_info=new_temp_data
        )
        print(f"s2s2s2s2@{structure}")
        structure = self.db_io.set_meta_info(
            structure=structure,
            setting_info=DB_meta.CURRENT_TAKE,
            new_value=str(current_take_num)
        )
        check_pt_2 = self.db_io.update_remote(structure=structure)

        check_pt_3 = self.r2_io.upload_file(
            file="",
            uploading_file=file,
            file_path=f"{collection_name}/cut{self.cut_num}/{self.working_component}/{naming}.{required_format}"
        )

        check_pt_4 = self.gcp_io.update_info(
            info_type=f"{self.working_component}_PIC",
            cut_num=self.cut_num,
            new_value=submitter_name
        )
        check_pt_4 = list(check_pt_4)
        check_pt_5 = self.gcp_io.update_info(
            info_type=f"{self.working_component}_progress",
            cut_num=self.cut_num,
            new_value="作業中"
        )
        check_pt_5 = list(check_pt_5)
        
        return {
            "cp1" : check_pt_1,
            "cp2" : check_pt_2,
            "cp3" : check_pt_3,
            "cp4" : check_pt_4,
            "cp5" : check_pt_5
        }
