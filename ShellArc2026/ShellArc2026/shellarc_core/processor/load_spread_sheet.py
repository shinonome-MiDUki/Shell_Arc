from typing import Any

import gspread

from shellarc_core.auth.access_spread_sheet import AccessSpreadSheet as AccessGS

class LoadSpreadSheet:
    def __init__(self, 
                 spreadsheet_format_data: dict, 
                 spreadsheet: gspread.Spreadsheet
                 ) -> None:
        """
        spreadsheet_format_data is a dict that contains the followings:
        - row_before_cut_1 - int: number of rows before the first cut in the spreadsheet 
        - common_column - dict[name: str : column_index: int(1-based)]: a dict that maps the name of the common info to the column index in the spreadsheet
        - component_info_range - int: number of columns each component info occupies in the spreadsheet
        - component_info_column_structure - dict[name: str : column_index: int(0-based)]: a dict that maps the name of the component info to the column index in the component info range
        - progress_data_n_lines_under_last_cut - int: number of empty lines under the last row before the progress data row
        """
        self.spreadsheet = spreadsheet
        self.row_before_cut_1 = spreadsheet_format_data["row_before_cut_1"]
        self.common_column = spreadsheet_format_data["common_column"]
        self.component_info_range = spreadsheet_format_data["component_info_range"]
        self.component_info_column_structure = spreadsheet_format_data["component_info_column_structure"]
        print(f"component_info_column_structure is {self.component_info_column_structure}")
        self.progress_data_n_lines_under_last_cut = spreadsheet_format_data["progress_data_n_lines_under_last_cut"]
        self.component_info_starting_column_index = max([self.common_column[k] for k in self.common_column]) + 1

    def cell_id(self, 
                column_index: int, 
                row_index: int
                ) -> tuple:
        """
        Input values are 1-based index
        """
        cell_id = (row_index, column_index)
        return cell_id
    
    def component_info_to_column_index(self,
                                       component_index: int,
                                       requesting_info: str
                                       ) -> int:
        """
        compoment_index is 1-based index
        """
        starting_column_index = self.component_info_starting_column_index + ((component_index-1) * self.component_info_range)
        requesting_column_index = starting_column_index + self.component_info_column_structure[requesting_info]
        return int(requesting_column_index)
    
    def load_spreadsheet(self, 
                         cut_index: int, 
                         target_info: str, 
                         update_info: str | int=None, 
                         component_index: int=0, 
                         spreadsheet: gspread.Spreadsheet=None
                         ) -> str | int | None:
        """
        cut_index, component_index are 1-based index
        update mode : update_info is not None, update cell value with update_info, return None
        get mode: update_info is None, return cell value
        """
        if spreadsheet == None:
            spreadsheet = self.spreadsheet
        row_index = self.row_before_cut_1 + cut_index
        if component_index == 0:
            cell_coord = self.cell_id(self.common_column[target_info], row_index)
        else:
            column_index = self.component_info_to_column_index(component_index, target_info)
            cell_coord = self.cell_id(column_index, row_index)
        
        if update_info != None:
            spreadsheet.update_cell(cell_coord[0], cell_coord[1], update_info)
            return None
        else:
            info_requested = spreadsheet.cell(cell_coord[0], cell_coord[1]).value
            return info_requested
        
    @property
    def spreadsheet_cache(self):
        """
        cache the whole spreadsheet into a dict of list to reduce num of api calles when intensive searching is needed
        """
        _spreadsheet_cache = self.spreadsheet.get_all_values()
        return _spreadsheet_cache
        
    def efficient_get_spreadsheet(self, 
                                  current_spreadsheet_cache: dict, 
                                  cut_index: int, 
                                  target_info: str, 
                                  component_index: int=0):
        """
        cut_index, component_index are 1-based index
        """
        first_index = self.row_before_cut_1 + cut_index
        second_index = self.common_column[target_info] if component_index == 0 \
            else self.component_info_to_column_index(component_index, target_info)
        info_requested = current_spreadsheet_cache[first_index-1][second_index-1]
        return info_requested
        
    def load_progress(self, component_index, is_get, total_cut_number, spreadsheet=None):
        """
        DEPRECATED
        """
        if spreadsheet == None:
            spreadsheet = self.spreadsheet

        column_index = self.component_info_to_column_index(component_index, "progress")
        row_index = int(total_cut_number + self.row_before_cut_1 + self.progress_data_n_lines_under_last_cut)
        cell_id = self.cell_id(column_index, row_index)
        current_progress = float(spreadsheet.acell(cell_id).value)
        if is_get:
            return str(current_progress)
        else:
            current_progress = current_progress + (1/total_cut_number)
            spreadsheet.update_acell(cell_id, str(current_progress))
            return

#logic using Load progeess has to be rewritten
#spreadsheet object is obtained automatically internally 

#added efficient loading by feeding in a dict of a full spread sheet, 
#the logic is 1.invert row and col 2.deduct 1 from both due to zerostart