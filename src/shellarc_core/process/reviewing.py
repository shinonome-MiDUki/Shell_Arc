from shellarc_core.cloudio.io_git import Git_IO
from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.cfg.cfg_io import Cfg_IO

from shellarc_core.exception.user_exception import SA_InvalidRequestObj

class ShellArc_Review:
    def __init__(self,
                 cut_num: int,
                 reviewing_component: str
                 ) -> None:
        self.git_io = Git_IO()
        self.gcp_io = GCP_IO()
        self.cfg_io = Cfg_IO()
        self.cut_num = cut_num
        self.reviewing_component = reviewing_component

    async def _existence_check(self,
                         reviewer_name: str
                         ) -> None:
        current_pending = await self.git_io.get_component_info(
            branch="pending",
            cut_num=self.cut_num,
            component=self.reviewing_component
        )
        if current_pending == {}:
            raise SA_InvalidRequestObj(
                error_log=f"not yet existing tempdata requester by {reviewer_name}",
                frontend_msg="確認待ちのカットはありません"
            )
        
    async def pending_action(self,
                       reviewer_name: str,
                       is_approve: bool,
                       message: str=""
                       ) -> None:
        self._existence_check(reviewer_name=reviewer_name)
        await self.git_io.pend_data(
            cut_num=self.cut_num,
            component=self.reviewing_component,
            is_approve=is_approve,
            message=message
        )
        self.gcp_io.update_info(
            info_type=f"{self.reviewing_component}_progress",
            cut_num=self.cut_num,
            new_value="完了"
        )
