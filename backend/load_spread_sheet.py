import gspread

from .access_spread_sheet import AccessSpreadSheet as AccessGS

class LoadSpreadSheet:
    def __init__(self, spreadsheet_format_data, spreadsheet):
        self.spreadsheet = spreadsheet
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
    
    def load_spreadsheet(self, cut_index, target_info, update_info=None, component_index=0, spreadsheet=None):
        if spreadsheet == None:
            spreadsheet = self.spreadsheet
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
        
    def spreadsheet_cache(self):
        _spreadsheet_cache = self.spreadsheet.get_all_values()
        return _spreadsheet_cache
        
    def efficient_get_spreadsheet(self, spreadsheet_cache, cut_index, target_info, component_index=0):
        first_index = self.row_before_cut_1 + cut_index
        second_index = self.common_column[target_info] if component_index == 0 else self.column_index_of_requested_component_info(component_index, target_info)
        info_requested = spreadsheet_cache[first_index-1][second_index-1]
        return info_requested
        
    def load_progress(self, component_index, is_get, total_cut_number, spreadsheet=None):
        if spreadsheet == None:
            spreadsheet = self.spreadsheet

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

#logic using Load progeess has to be rewritten
#spreadsheet object is obtained automatically internally 

#added efficient loading by feeding in a dict of a full spread sheet, 
#the logic is 1.invert row and col 2.deduct 1 from both due to zerostart