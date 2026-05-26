import asyncio
import json
import datetime
from enum import StrEnum
from pathlib import Path

from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_LocalIOError, SA_ErrorCode
)
from shellarc_core.exception.user_exception import SA_DataNotExist

class GitCommands(StrEnum):
    SHOW = "show"
    COMMIT = "commit"
    CHECKOUT = "checkout"
    MERGE = "merge"
    PUSH = "push"
    ADD = "add"
    INIT = "init"

class Git_IO:
    def __init__(self):
        cfg_io = Cfg_IO()
        self.git_repo_local_dir = Path(cfg_io.get_cfg_setting(Cfg_item.GIT_LREPO))

    def get_components(self,
                       cut_num: int
                       ) -> list[str]:
        with open(self.git_repo_local_dir / "project_main.json", "r", encoding="utf-8") as f:
            pj_main = json.load(f)
            components = pj_main.get("common", None)
            if components is None:
                raise SA_ProjStructError(
                    error_log="The common key not found in project_main.json file",
                    error_code=SA_ErrorCode.SA_6001
                )
            components = pj_main.get(f"cut{cut_num}", components)
        return [component for component in components]
    
    
    @property
    def _get_timemark(self) -> str:
        t_delta = datetime.timedelta(hours=9)
        now = datetime.datetime.now(datetime.timezone(t_delta, 'JST'))
        time_mark = now.strftime('%Y%m%d%H%M%S')
        return time_mark
    
    def _make_index_name(self,
                        cut_num: int,
                        component: str,
                        creator_name: str
                        ) -> str:
        component = component.replace("_", "-")
        creator_name = creator_name.replace("_", "-")
        index_name = f"cut{cut_num}_{component}_{creator_name}_{self._get_timemark}"
        return index_name

    async def _git_command(self,
                          *git_cmds_param
                          ) -> asyncio.subprocess.Process:
        git_cmds = ["git"] + list(git_cmds_param)
        git_proc = await asyncio.create_subprocess_exec(
                *git_cmds,
                cwd=str(self.git_repo_local_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        return git_proc
    
    async def _continuous_git_command(self,
                                      git_commands: list
                                      ) -> None:
        for git_command in git_commands:
            git_proc = await self._git_command(*git_command)
            stdout, stderr = await git_proc.communicate()
            if git_proc.returncode != 0:
                raise SA_LocalIOError(
                    error_log=f"A git command error : {stderr.decode('utf-8')}",
                    error_code=SA_ErrorCode.SA_8002
                )
            
    async def make_proj_repo(self,
                       proj_settings: dict
                       ) -> None:
        self.git_repo_local_dir.mkdir(parents=True, exist_ok=True)
        stage_dir = self.git_repo_local_dir / "stage"
        stage_dir.mkdir(parents=True, exist_ok=True)
        proj_main_dict = {
            "cut_num" : int(proj_settings["cut_num"]),
            "common" : {c : [c_info["format"]] for c, c_info in proj_settings["components"]}
        }
        with open(self.git_repo_local_dir / "project_main.json", "w", encoding="utf-8") as f:
            json.dump(proj_main_dict, f, ensure_ascii=False, indent=3)
        for c in range(1, int(proj_settings["cut_num"]) + 1):
            with open(stage_dir / f"cut{c}.json", "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False)
        git_commands = [
            [GitCommands.INIT],
            [GitCommands.ADD, "."],
            [GitCommands.COMMIT, "-m", f"Initialize project ({self._get_timemark})"]
        ]
        await self._continuous_git_command(git_commands=git_commands)
        print(f"Project repo built ({self._get_timemark})")
        

    async def get_component_info(self,
                                 branch: str,
                                 cut_num: int,
                                 component: str
                                 ) -> dict[str, str]:
        git_proc = await self._git_command(GitCommands.SHOW, f"{branch}:stage/{cut_num}.json")
        stdout, stderr = await git_proc.communicate()
        if git_proc.returncode == 0:
            cut_info_str = stdout.decode("utf-8")
            cut_info = json.loads(cut_info_str)
        else:
            raise SA_LocalIOError(
                error_log=f"A git command error : {stderr.decode('utf-8')}",
                error_code=SA_ErrorCode.SA_8002
            )
        requested_info = cut_info.get(component, {})
        return requested_info
    
    async def pend_data(self,
                        cut_num: int,
                        processing_person: str,
                        is_approve: bool,
                        message: str=""
                        ) -> None:
        git_commands_approve = [
            [GitCommands.CHECKOUT, "main"],
            [GitCommands.CHECKOUT, "pending", "--", f"stage/{cut_num}.json"],
            [GitCommands.ADD, f"stage/{cut_num}.json"],
            [GitCommands.COMMIT, "-m", f"APPROVED by {processing_person} : {message} ({self._get_timemark})"]
        ]
        git_commands_decline = [
            [GitCommands.CHECKOUT, "pending"],
            [GitCommands.ADD, f"stage/{cut_num}.json"],
            [GitCommands.COMMIT, "--allow-empty", "-m", f"DECLINED by {processing_person} : {message} ({self._get_timemark})"]
        ]
        git_commands = git_commands_approve if is_approve else git_commands_decline
        await self._continuous_git_command(git_commands=git_commands)
            
            
    async def update_data(self,
                          cut_num: int,
                          component: str,
                          creator_name: str,
                          message: str=""
                          ) -> str:
        file_index_name = self._make_index_name(
            cut_num=cut_num,
            component=component,
            creator_name=creator_name
        )
        git_show_proc = await self._git_command(GitCommands.SHOW, f"pending:stage/{cut_num}.json")
        stdout, stderr = await git_show_proc.communicate()
        if git_show_proc.returncode == 0:
            current_cut_info_str = stdout.decode("utf-8")
            current_cut_info = json.loads(current_cut_info_str)
        else:
            raise SA_LocalIOError(
                error_log=f"A git command error : {stderr.decode('utf-8')}",
                error_code=SA_ErrorCode.SA_8002
            )
        current_cut_info[component] = {
            "creator" : creator_name,
            "fileindex" : file_index_name
        }
        git_checkout_proc = await self._git_command(GitCommands.CHECKOUT, "pending")
        stdout, stderr = await git_checkout_proc.communicate()
        if git_checkout_proc.returncode != 0:
            raise SA_LocalIOError(
                error_log=f"A git command error : {stderr.decode('utf-8')}",
                error_code=SA_ErrorCode.SA_8002
            )
        with open(self.git_repo_local_dir / "stage" / f"{cut_num}.json", "w", encoding="utf-8") as f:
            json.dump(current_cut_info, f, ensure_ascii=False, indent=3)
        git_commands = [
            [GitCommands.CHECKOUT, "pending"],
            [GitCommands.ADD, f"stage/{cut_num}.json"],
            [GitCommands.COMMIT, "-m", f"SUBMITTED by {creator_name} : {message} ({self._get_timemark}) @{file_index_name}"]
        ]
        await self._continuous_git_command(git_commands=git_commands)
        return file_index_name
    

    async def sync_remote(self) -> None:
        git_commands = [
            [GitCommands.PUSH, "origin", "main"],
            [GitCommands.PUSH, "origin", "pending"]
        ]
        await self._continuous_git_command(git_commands=git_commands)
        
