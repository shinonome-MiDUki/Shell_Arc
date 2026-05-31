import asyncio
import os
import json
import hashlib
import datetime

from enum import StrEnum
from dataclasses import dataclass
from pathlib import Path

from shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_LocalIOError, SA_ErrorCode,
    SA_InternalSyntaxError
)
from shellarc_core.exception.user_exception import SA_InvalidRequestObj


class GitCommands(StrEnum):
    SHOW = "show"
    COMMIT = "commit"
    CHECKOUT = "checkout"
    MERGE = "merge"
    PUSH = "push"
    ADD = "add"
    INIT = "init"
    LOG = "log"
    STATUS = "status"

class SA_CommitType(StrEnum):
    DECLINE = "DECLINE"
    APPROVE = "APPROVE"
    SUBMIT = "SUBMIT"

class ShellArcGitBranch(StrEnum):
    PENDING = "pending"
    MAIN = "main"

@dataclass
class SA_GitLogFilter:
    commit_type: SA_CommitType | None = None
    cut_num: int | None = None
    component: str | None = None
    log_length: int | None = None



class Git_IO:
    _git_lock = asyncio.Lock()

    def __init__(self,
                 git_repo_local_dir: str | None=None):
        cfg_io = Cfg_IO()
        self.git_repo_local_dir = Path(cfg_io.get_cfg_setting(Cfg_item.GIT_LREPO)) \
            if git_repo_local_dir is None else Path(git_repo_local_dir)


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
        creator_id = hashlib.shake_128(creator_name.encode('utf-8')).hexdigest(3)
        index_name = f"cut{cut_num}_{component}_{creator_id}_{self._get_timemark}"
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
                print(stderr.decode('utf-8'))
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
            "common" : {c : [c_info["format"]] for c, c_info in proj_settings["components"].items()}
        }
        with open(self.git_repo_local_dir / "project_main.json", "w", encoding="utf-8") as f:
            json.dump(proj_main_dict, f, ensure_ascii=False, indent=3)
        for c in range(1, int(proj_settings["cut_num"]) + 1):
            cut_dir = stage_dir / f"cut{c}"
            cut_dir.mkdir(parents=True, exist_ok=True)
        git_commands = [
            [GitCommands.INIT, "-b", ShellArcGitBranch.MAIN],
            [GitCommands.ADD, "."],
            [GitCommands.COMMIT, "-m", f"Initialized project ({self._get_timemark})"],
            [GitCommands.CHECKOUT, "-b", ShellArcGitBranch.PENDING],
            [GitCommands.ADD, "."],
            [GitCommands.COMMIT, "--allow-empty", "-m", f"Initialized pending branch ({self._get_timemark})"],
            [GitCommands.CHECKOUT, "main"]
        ]
        await self._continuous_git_command(git_commands=git_commands)
        print(f"Project repo built ({self._get_timemark})")
        

    async def get_component_info(self,
                                 branch: ShellArcGitBranch,
                                 cut_num: int,
                                 component: str,
                                 commit_id: str | None=None
                                 ) -> dict[str, str]:
        await self._continuous_git_command([[GitCommands.CHECKOUT, branch]])
        component_json_path = self.git_repo_local_dir / f"stage/cut{cut_num}/{component}.json"
        if component_json_path.exists():
            commit_id = commit_id if commit_id is not None else branch
            git_proc = await self._git_command(GitCommands.SHOW, f"{commit_id}:stage/cut{cut_num}/{component}.json")
            stdout, stderr = await git_proc.communicate()
            if git_proc.returncode == 0:
                requested_info_str = stdout.decode("utf-8")
                requested_info = json.loads(requested_info_str)
            else:
                requested_info = {}
        else:
            requested_info = {}
        return requested_info
    

    async def get_log(self,
                      output_format: list[int],
                      log_filter: SA_GitLogFilter | None=None,
                      limit_scope: str | None=None,
                      branch: ShellArcGitBranch=ShellArcGitBranch.PENDING
                      ) -> dict[str, str]:
        if log_filter is None:
            log_filter = SA_GitLogFilter()
        if limit_scope is None:
            git_log_proc = await self._git_command(GitCommands.LOG, branch, f"--format=%h=&=%s")
        else:
            git_log_proc = await self._git_command(GitCommands.LOG, branch, f"--format=%h=&=%s", "--", limit_scope)
        stdout, stderr = await git_log_proc.communicate()
        if git_log_proc.returncode != 0:
            raise SA_LocalIOError(
                error_log=f"A git command error : {stderr.decode('utf-8')}",
                error_code=SA_ErrorCode.SA_8002
            )
        log_list = stdout.decode("utf-8").split("\n")
        rtn = {}
        for log_piece in log_list:
            if not log_piece.strip():
                continue
            breakdown_log = log_piece.split("=&=")
            breakdown_commit_record_ls = breakdown_log[1].split("*")
            if output_format and max(output_format) >= len(breakdown_commit_record_ls):
                continue
            breakdown_commit_record_ls = [x.strip() for x in breakdown_commit_record_ls]
            # "commit_type" : breakdown_commit_record_ls[0],
            # "cut_num" : breakdown_commit_record_ls[1],
            # "component" : breakdown_commit_record_ls[2],
            # "creator_name" : breakdown_commit_record_ls[3],
            # "commit_message" : breakdown_commit_record_ls[4],
            # "timemark" : breakdown_commit_record_ls[5],
            # "file_index_name" : breakdown_commit_record_ls[6]?
            if log_filter.commit_type is not None and log_filter.commit_type != breakdown_commit_record_ls[0]:
                continue
            elif log_filter.cut_num is not None and str(log_filter.cut_num) != breakdown_commit_record_ls[1]:
                continue
            elif log_filter.component is not None and log_filter.component != breakdown_commit_record_ls[2]:
                continue
            filtered_record_ls = [breakdown_commit_record_ls[i] for i in output_format]
            filtered_record = " ".join(filtered_record_ls)
            rtn[breakdown_log[0]] = filtered_record
            if log_filter.log_length is not None and len(rtn) >= log_filter.log_length:
                break
        return rtn
        
    
    async def pend_data(self,
                        cut_num: int,
                        component: str,
                        processing_person: str,
                        is_approve: bool,
                        message: str=""
                        ) -> None:
        if not message:
            message = "No message"
        async with self.__class__._git_lock:
            message = message.replace("*", "+")
            git_statuscheck_proc = await self._git_command(GitCommands.STATUS, "--porcelain", f"stage/cut{cut_num}")
            stdout, stderr = await git_statuscheck_proc.communicate()
            if git_statuscheck_proc.returncode != 0:
                print(stderr.decode('utf-8'))
                raise SA_LocalIOError(
                    error_log=f"A git command error : {stderr.decode('utf-8')}",
                    error_code=SA_ErrorCode.SA_8002
                )
            status_str = stdout.decode("utf-8").strip()
            if f".sa_pending_{component}" not in status_str:
                raise SA_InvalidRequestObj(
                    error_log=f"c{cut_num} {component} pending attempted by {processing_person} but not exist",
                    frontend_msg="承認待ちの提出はありません"
                )
            os.unlink(self.git_repo_local_dir / f"stage/cut{cut_num}/.sa_pending_{component}")
            print("osunlink")
            git_commands_approve = [
                [GitCommands.CHECKOUT, ShellArcGitBranch.PENDING],
                [GitCommands.ADD, f"stage/cut{cut_num}"],
                [GitCommands.COMMIT, "--allow-empty", "-m", f"{SA_CommitType.APPROVE} * {cut_num} * {component} * {processing_person} * {message} * {self._get_timemark} * 'na'"],
                [GitCommands.CHECKOUT, ShellArcGitBranch.MAIN],
                [GitCommands.CHECKOUT, ShellArcGitBranch.PENDING, "--", f"stage/cut{cut_num}/{component}.json"],
                [GitCommands.ADD, f"stage/cut{cut_num}/{component}.json"],
                [GitCommands.COMMIT, "--allow-empty", "-m", f"{SA_CommitType.APPROVE} * {cut_num} * {component} * {processing_person} * {message} * {self._get_timemark} * 'na'"]
            ]
            git_commands_decline = [
                [GitCommands.CHECKOUT, ShellArcGitBranch.PENDING],
                [GitCommands.ADD, f"stage/cut{cut_num}"],
                [GitCommands.COMMIT, "--allow-empty", "-m", f"{SA_CommitType.DECLINE} * {cut_num} * {component} * {processing_person} * {message} * {self._get_timemark} * 'na'"]
            ]
            git_commands = git_commands_approve if is_approve else git_commands_decline
            try:
                await self._continuous_git_command(git_commands=git_commands)
            except Exception as e:
                with open(self.git_repo_local_dir / f"stage/cut{cut_num}/.sa_pending_{component}", "w") as f:
                    f.write("")
                raise SA_LocalIOError(
                    error_log="Git error while approving",
                    error_code=SA_ErrorCode.SA_8002
                )
            
            
    async def update_data(self,
                          cut_num: int,
                          component: str,
                          creator_name: str,
                          message: str=""
                          ) -> str:
        if not message:
            message = "No message"
        async with self.__class__._git_lock:
            message = message.replace("*", "+")
            file_index_name = self._make_index_name(
                cut_num=cut_num,
                component=component,
                creator_name=creator_name
            )
            await self._continuous_git_command([[GitCommands.CHECKOUT, ShellArcGitBranch.PENDING]])
            current_component_info = {
                "creator" : creator_name,
                "fileindex" : file_index_name
            }
            with open(self.git_repo_local_dir / f"stage/cut{cut_num}/{component}.json", "w", encoding="utf-8") as f:
                json.dump(current_component_info, f, ensure_ascii=False, indent=3)
            git_commands = [
                [GitCommands.ADD, f"stage/cut{cut_num}/{component}.json"],
                [GitCommands.COMMIT, "-m", f"{SA_CommitType.SUBMIT} * {cut_num} * {component} * {creator_name} * {message} * {self._get_timemark} * {file_index_name}"]
            ]
            await self._continuous_git_command(git_commands=git_commands)
            with open(self.git_repo_local_dir / f"stage/cut{cut_num}/.sa_pending_{component}", "w") as f:
                f.write("")
            return file_index_name
    

    async def sync_remote(self) -> None:
        git_commands = [
            [GitCommands.PUSH, "origin", ShellArcGitBranch.MAIN],
            [GitCommands.CHECKOUT, ShellArcGitBranch.PENDING],
            [GitCommands.PUSH, "origin", ShellArcGitBranch.PENDING]
        ]
        await self._continuous_git_command(git_commands=git_commands)
        
