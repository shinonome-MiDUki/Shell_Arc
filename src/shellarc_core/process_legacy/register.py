from shellarc_core.cloudio_legacy.io_spreadsheet import GCP_IO
from shellarc_core.exception.user_exception import SA_EditingRejection

class ShellArc_Register:
    def __init__(self):
        self.gcp_io = GCP_IO()

    async def register_work(self,
                      registering_person: str,
                      registering_component: str,
                      registering_cut: int,
                      force: bool=False
                      ) -> None:
        current_pic = self.gcp_io.get_info(
            info_type=f"{registering_component}_PIC",
            cut_num=registering_cut
        )
        if current_pic and not force:
            raise SA_EditingRejection(
                error_log=f"When {registering_person} registering for c{registering_cut} {registering_component}, " \
                    f"overwritting rejected as {current_pic} already registered",
                frontend_msg=f"{current_pic}さんが担当しています"
            )
        self.gcp_io.update_info(
            info_type=f"{registering_component}_PIC",
            cut_num=registering_cut,
            new_value=registering_person
        )