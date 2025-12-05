import gspread

from .access_spread_sheet import AccessSpreadSheet as AccessGS

class LoadSpreadSheet:
    def __init__(self, spreadsheet_format_data):
        self.row_before_cut_1 = spreadsheet_format_data["row_before_cut_1"]
        self.common_column = spreadsheet_format_data["common_column"]
        self.component_info_range = spreadsheet_format_data["component_info_range"]
        self.component_info_column_structure = spreadsheet_format_data["component_info_column_structure"]
        self.progress_data_n_lines_under_last_cut = spreadsheet_format_data["progress_data_n_lines_under_last_cut"]
        self.component_info_starting_column_index = max([self.common_column[k] for k in self.common_column]) + 1

    def cell_id(self, column_index, row_index):
        alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        column = alphabets[column_index-1]
        row = row_index
        cell_id = f"{column}{row}"
        return cell_id
    
    def column_index_of_requested_component_info(self, component_index, requesting_info):
        starting_column_index = self.component_info_starting_column_index + ((component_index-1) * self.component_info_range)
        requesting_column_index = starting_column_index + self.component_info_column_structure[requesting_info]
        return int(requesting_column_index)
    
    def load_spreadsheet(self, spreadsheet, cut_index, target_info, update_info=None, component_index=0):
        row_index = self.row_before_cut_1 + cut_index
        if component_index == 0:
            cell_id = self.cell_id(self.common_column[target_info], row_index)
        else:
            column_index = self.column_index_of_requested_component_info(component_index, target_info)
            cell_id = self.cell_id(column_index, row_index)
        
        if update_info != None:
            spreadsheet.update_acell(cell_id, update_info)
            return
        else:
            info_requested = spreadsheet.acell(cell_id).value
            return info_requested
        
    def load_progress(self, spreadsheet, component_index, is_get, total_cut_number):
        column_index = self.column_index_of_requested_component_info(component_index, "progress")
        row_index = int(total_cut_number + self.row_before_cut_1 + self.progress_data_n_lines_under_last_cut)
        cell_id = self.cell_id(column_index, row_index)
        current_progress = float(spreadsheet.acell(cell_id).value)
        if is_get:
            return str(current_progress)
        else:
            current_progress = current_progress + (1/total_cut_number)
            spreadsheet.update_acell(cell_id, str(current_progress))
            return
