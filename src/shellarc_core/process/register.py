from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.exception.user_exception import SA_EditingRejection

class ShellArc_Register:
    def __init__(self):
        self.gcp_io = GCP_IO()

    def register_work(self,
                      registering_person: str,
                      registering_component: str,
                      cut_num: int,
                      force: bool=False
                      ) -> None:
        current_pic = self.gcp_io.get_info(
            info_type=f"{registering_component}_PIC",
            cut_num=cut_num
        )
        if current_pic and not force:
            raise SA_EditingRejection(
                error_log=f"When {registering_person} registering for c{cut_num} {registering_component}, " \
                    f"overwritting rejected as {current_pic} already registered",
                frontend_msg=f"{current_pic}さんが担当しています"
            )
        self.gcp_io.update_info(
            info_type=f"{registering_component}_PIC",
            cut_num=cut_num,
            new_value=registering_person
        )