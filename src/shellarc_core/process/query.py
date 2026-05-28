from shellarc_core.cloudio.io_spreadsheet import GCP_IO
from shellarc_core.cloudio.io_git import Git_IO, SA_GitLogFilter, SA_CommitType, ShellArcGitBranch
from shellarc_core.cfg.spreadsheet_map_io import SpreadsheetMap_IO

from shellarc_core.exception.structure_error import SA_InternalSyntaxError, SA_ErrorCode

class ShellArc_Query:   
    @staticmethod
    async def efficient_get_spreadsheet_info(target_index_value: str,
                                             index_info_types: list[str],
                                             target_info_types: list[str],
                                             search_range: list[int],
                                             output_key: str="index_info_type"
                                             ) -> dict:
        gcp_io = GCP_IO()
        smap_io = SpreadsheetMap_IO()
        vert_offset = smap_io.get_vert_offset()
        if len(search_range) != 2:
            raise SA_InternalSyntaxError(
                error_log="a range is needed for efficient_get_spreadsheet",
                error_code=SA_ErrorCode.SA_7000
            )
        elif search_range[0] > search_range[1]:
            raise SA_InternalSyntaxError(
                error_log="starting cut cannot be greater than ending cut",
                error_code=SA_ErrorCode.SA_7000
            )
        elif len(index_info_types) != len(target_info_types):
            raise SA_InternalSyntaxError(
                error_log="index_info_types must be of same length of target_info_types",
                error_code=SA_ErrorCode.SA_7000
            )
        
        current_spreadsheet_cache = gcp_io.spreadsheet_cache
        rtn = {}
        cycle = len(index_info_types)
        for i in range(0, cycle):
            index_info_type = index_info_types[i]
            target_info_type = target_info_types[i]
            index_col = smap_io.get_cell_coord(
                cut_num=1,
                item=index_info_type
            )[1]
            target_col = smap_io.get_cell_coord(
                cut_num=1,
                item=target_info_type
            )[1]
            for row_num in range(search_range[0] + vert_offset - 1, search_range[1] + vert_offset):
                searching_row = current_spreadsheet_cache[row_num]
                target_value = searching_row[target_col-1]
                index_value = searching_row[index_col-1]
                if index_value == target_index_value:
                    if output_key == "index_info_type":
                        rtn[index_info_type] = str(target_value)
                    else:
                        rtn[target_info_type] = str(target_value)
        
        return rtn
    
    @staticmethod
    def get_components_enname(cut_num: int) -> list[str]:
        git_io = Git_IO()
        return git_io.get_components(cut_num=cut_num)
    
    @staticmethod
    async def get_history(cut_num: int,
                    component: str,
                    max_length: int | None=None
                    ) -> dict[str, str]:
        git_io = Git_IO()
        json_file_path = f"stage/cut{cut_num}/{component}.json"
        print("CALL72")
        log_filter = SA_GitLogFilter(
            commit_type=SA_CommitType.SUBMIT,
            log_length=max_length
        )
        hist_dict = await git_io.get_log(
            output_format=[5, 3, 4],
            log_filter=log_filter,
            limit_scope=json_file_path
        )
        return hist_dict
    
    @staticmethod
    async def get_approve_history(cut_num: int,
                            component: str,
                            max_length: int | None=None
                            ) -> dict[str, str]:
        git_io = Git_IO()
        json_file_path = f"stage/cut{cut_num}/{component}.json"
        log_filter = SA_GitLogFilter(
            commit_type=SA_CommitType.APPROVE,
            log_length=max_length
        )
        hist_dict = await git_io.get_log(
            output_format=[5, 3, 4],
            log_filter=log_filter,
            limit_scope=json_file_path,
            branch=ShellArcGitBranch.MAIN
        )
        return hist_dict

    