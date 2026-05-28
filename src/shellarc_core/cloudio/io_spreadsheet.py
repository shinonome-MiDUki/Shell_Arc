from shellarc_core.auth.access_spread_sheet import AccessSpreadSheet as A_GCP
from shellarc_core.cfg.cfg_io import Cfg_IO as Cfg_IO
from shellarc_core.cfg.cfg_io import Cfg_item
from shellarc_core.cfg.spreadsheet_map_io import SpreadsheetMap_IO as SMap_IO


class GCP_IO:
    def __init__(self):
        cfg_io = Cfg_IO()
        spreadsheet_key = cfg_io.get_cfg_setting(Cfg_item.SPREADSHEET_KEY)
        a_gcp = A_GCP(spreadsheet_key=spreadsheet_key)
        self.spreadsheet = a_gcp.spreadsheet_obj
        self.smap_io = SMap_IO()

    def get_info(self,
                 info_type: str,
                 cut_num: int
                 ) -> str | None:
        cell_coord = self.smap_io.get_cell_coord(
            cut_num=cut_num,
            item=info_type
        )
        rtn = self.spreadsheet.cell(
            row=cell_coord[0], 
            col=cell_coord[1]
            ).value
        return str(rtn) if rtn is not None else None
    
    def update_info(self,
                    info_type: str,
                    cut_num: int,
                    new_value: str
                    ) -> None:
        cell_coord = self.smap_io.get_cell_coord(
            cut_num=cut_num,
            item=info_type
        )
        self.spreadsheet.update_cell(
            row=cell_coord[0],
            col=cell_coord[1],
            value=new_value
        )

    @property
    def spreadsheet_cache(self):
        if not hasattr(self, "_spreadsheet_cache"):
            self._spreadsheet_cache = self.spreadsheet.get_all_values()
        return self._spreadsheet_cache


