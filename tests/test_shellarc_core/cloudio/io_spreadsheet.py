from test_shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from test_shellarc_core.cfg.spreadsheet_map_io import SpreadsheetMap_IO as SMap_IO
from test_shellarc_core.exception.structure_error import SA_ProjStructError, SA_ErrorCode

class GCP_IO:
    def __init__(self):
        cfg_io = Cfg_IO()
        spreadsheet_key = cfg_io.get_cfg_setting(Cfg_item.SPREADSHEET_KEY)
        self.smap_io = SMap_IO()

    def get_info(self,
                 info_type: str,
                 cut_num: int
                 ) -> tuple[int]:
        cell_coord = self.smap_io.get_cell_coord(
            cut_num=cut_num,
            item=info_type
        )
        return cell_coord
    
    def update_info(self,
                    info_type: str,
                    cut_num: int,
                    new_value: str
                    ) -> tuple[int]:
        cell_coord = self.smap_io.get_cell_coord(
            cut_num=cut_num,
            item=info_type
        )
        return cell_coord
