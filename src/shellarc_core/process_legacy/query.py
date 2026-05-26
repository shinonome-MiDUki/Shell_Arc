from shellarc_core.cloudio_legacy.io_spreadsheet import GCP_IO
from shellarc_core.exception.structure_error import SA_InternalSyntaxError, SA_ErrorCode

class ShellArc_Query:
    def __init__(self):
        self.gcp_io = GCP_IO()

    async def efficient_get_spreadsheet_info(self,
                                             target_index_value: str,
                                             index_info_types: list[str],
                                             target_info_types: list[str],
                                             search_range: list[int],
                                             output_key: str="index_info_type"
                                             ) -> dict:
        vert_offset = self.smap_io.get_vert_offset()
        if len(search_range) != 2:
            raise SA_InternalSyntaxError(
                error_log="a range is needed for efficient_get_spreadsheet",
                error_code=SA_ErrorCode.SA_7000
            )
        elif len(current_spreadsheet_cache) < search_range[1] + vert_offset - 1:
            raise SA_InternalSyntaxError(
                error_log="requesting range for efficient_get_spreadsheet overflowing",
                error_code=SA_ErrorCode.SA_7000
            )
        elif search_range[0] > search_range[1]:
            raise SA_InternalSyntaxError(
                error_log="starting cut cannot be greater than ending cut",
                error_code=SA_ErrorCode.SA_7000
            )
        elif len(index_info_type) != len(target_info_types):
            raise SA_InternalSyntaxError(
                error_log="index_info_types must be of same length of target_info_types",
                error_code=SA_ErrorCode.SA_7000
            )
        
        current_spreadsheet_cache = self.gcp_io.spreadsheet_cache
        rtn = {}
        cycle = len(index_info_types)
        for i in range(0, cycle):
            index_info_type = index_info_types[i]
            target_info_type = target_info_types[i]
            index_col = self.smap_io.get_cell_coord(
                cut_num=1,
                item=index_info_type
            )[1]
            target_col = self.smap_io.get_cell_coord(
                cut_num=1,
                item=target_info_type
            )[1]
            for row_num in range(search_range[0] + vert_offset - 1, search_range[1] + vert_offset):
                searching_row = current_spreadsheet_cache[row_num]
                target_value = searching_row[target_col]
                index_value = searching_row[index_col]
                if index_value == target_index_value:
                    if output_key == "index_info_type":
                        rtn[index_info_type] = str(target_value)
                    else:
                        rtn[target_info_type] = str(target_value)
        
        return rtn