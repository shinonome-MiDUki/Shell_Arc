import json
import os
from pathlib import Path
from typing import Any

from shellarc_core.exception.structure_error import SA_ProjStructError, SA_ErrorCode

class SpreadsheetMap_IO:
    def __init__(self):
        project_ctx_dir = Path(os.environ.get("SHELLARC_PROJECT_CTX", None))
        spreadsheet_map_path = project_ctx_dir / "spreadsheet_map.json"
        if not spreadsheet_map_path.exists():
            raise SA_ProjStructError(
                error_log="project cfg_path not exist",
                error_code=SA_ErrorCode.SA_4101,
            )
        with open(spreadsheet_map_path, "r", encoding="utf-8") as f:
            self.spreadsheet_map = json.load(f)

    def get_cell_coord(self,
                 cut_num: int,
                 item: str
                 ) -> tuple[int]:
        row_idx = cut_num + self.spreadsheet_map.get("vert_offset", None)
        if not isinstance(row_idx, int):
            raise SA_ProjStructError(
                error_log="vert_offset not configured properly in spreadsheet map",
                error_code=SA_ErrorCode.SA_4102
            )
        col_idx = self.spreadsheet_map.get("items", {}).get(item, None)
        if not isinstance(col_idx, int):
            raise SA_ProjStructError(
                error_log="requested spreadsheet cell column idx not configured",
                error_code=SA_ErrorCode.SA_4102
            )
        return (row_idx, col_idx)
        