from enum import Enum
from pathlib import Path
import json

from test_shellarc_core.cfg.cfg_io import Cfg_IO, Cfg_item
from test_shellarc_core.exception.structure_error import (
    SA_ProjStructError, SA_RequestItemError, SA_ErrorCode,
    SA_CommunicationError
)
from test_mock_modules.mock_firebase import MockFirebase

class DB_status(Enum):
    ACTIVE = "active"
    TEMP = "temporary"
    NONACTIVE = "non_active"

class DB_info(Enum):
    NAMING = "naming"
    CUT = "cut"
    TAKE = "take"
    CREATOR = "creator"
    REVIEWER = "reviewer"

class DB_meta(Enum):
    CURRENT_TAKE = "current_take"
    CURRENT_REJECTED_COUNT = "current_reject_count"

class DB_movemode(Enum):
    TEMP2NONACTIVE = 1
    TEMP2ACTIVE = 2

class DB_IO:
    def __init__(self,
                 cut_num: int,
                 processing_component: str
                 ) -> None:
        cfg_io = Cfg_IO()
        collection_name = cfg_io.get_cfg_setting(Cfg_item.COLL_NAME)
        mock_db_path = Path(__file__).resolve().parents[2] / "test_data/test_db.json"
        with open(mock_db_path, "r", encoding="utf-8") as f:
            mock_db = json.load(f)
        self.requested_data = mock_db.get(f"cut{cut_num}", {}).get(processing_component, None)
        if self.requested_data is None:
            raise SA_ProjStructError(
                error_log=f"cut{cut_num} data not found in db",
                error_code=SA_ErrorCode.SA_5004
            )
        self.cut_num = cut_num
        self.processing_component = processing_component
    
    def _move_to_empty_status(self,
                           structure: dict,
                           from_status: DB_status,
                           to_status: DB_status
                           ) -> dict:
        from_dict = self.get_status_dict(request_status=from_status)
        if to_status == DB_status.NONACTIVE:
            current_take = from_dict.get(DB_info.TAKE.value, "")
            if current_take == "":
                raise SA_ProjStructError(
                    error_log=f"info {DB_info.TAKE.value} is not found from " \
                        f"{from_status.value} in c{self.cut_num}{self.processing_component}",
                    error_code=SA_ErrorCode.SA_5001
                )
            to_status_name = f"non_active_{current_take}"
        else:
            to_status_name = to_status.value
        structure[to_status_name] = from_dict
        if to_status == DB_status.NONACTIVE:
            current_reject_count = int(self.get_meta_info(request_info=DB_meta.CURRENT_REJECTED_COUNT))
            structure[DB_meta.CURRENT_REJECTED_COUNT.value] = str(current_reject_count + 1)
        return structure

    def move_data_block(self,
                        move_mode: DB_movemode,
                        new_info: dict | None=None,
                        structure: dict | None=None
                        ) -> dict:
        structure = structure if structure is not None else {}
        clr = {
            "naming": None, 
            "cut": None, 
            "take": None, 
            "creator": None, 
            "reviewer": None
            }
        if move_mode == DB_movemode.TEMP2NONACTIVE:
            current_temp_name = self.get_info(
                request_status=DB_status.TEMP,
                request_info=DB_info.NAMING
            )
            if current_temp_name is not None: 
                structure = self._move_to_empty_status(
                    structure=structure,
                    from_status=DB_status.TEMP,
                    to_status=DB_status.NONACTIVE
                    )
            structure[DB_status.TEMP.value] = clr if new_info is None else new_info
        elif move_mode == DB_movemode.TEMP2ACTIVE:
            current_active_name = self.get_info(
                request_status=DB_status.ACTIVE,
                request_info=DB_info.NAMING
            )
            if current_active_name is not None:
                structure = self._move_to_empty_status(
                    structure=structure,
                    from_status=DB_status.ACTIVE,
                    to_status=DB_status.NONACTIVE
                    )
            structure = self._move_to_empty_status(
                structure=structure,
                from_status=DB_status.TEMP,
                to_status=DB_status.ACTIVE
            )
            structure[DB_status.TEMP.value] = clr if new_info is None else new_info
        return structure

    def make_data_block(self,
                        naming: str | None = None,
                        cut: str | None = None,
                        take: str | None = None,
                        creator: str | None = None,
                        reviewer: str | None = None
                        ) -> dict:
        current_data = {}
        current_data[DB_info.NAMING.value] = str(naming) if naming is not None else None
        current_data[DB_info.CUT.value] = str(cut) if cut is not None else None
        current_data[DB_info.TAKE.value] = str(take) if take is not None else None
        current_data[DB_info.CREATOR.value] = str(creator) if creator is not None else None
        current_data[DB_info.REVIEWER.value] = str(reviewer) if reviewer is not None else None
        return current_data

    def get_info(self,
                 request_status: DB_status,
                 request_info: DB_info,
                 request_non_active: int | None=None
                 ) -> str | None:
        if request_status == DB_status.NONACTIVE and request_non_active is None:
            raise SA_ProjStructError(
                error_log="get non_active info but non_active index not specified",
                error_code=SA_ErrorCode.SA_5002
            )
        request_status_name = f"non_active_{request_non_active}" if request_status == DB_status.NONACTIVE else request_status.value
        requested_status_dict = self.requested_data.get(request_status_name, None)
        if requested_status_dict is None:
            return "STATUS DICT NOT EXIST"
        if request_info.value not in requested_status_dict:
            raise SA_ProjStructError(
                error_log=f"info {request_info.value} not found from {request_status_name} in " \
                f"c{self.cut_num}{self.processing_component}",
                error_code=SA_ErrorCode.SA_5001
            )
        requested_info = requested_status_dict[request_info.value]
        request_info = str(request_info) if request_info is not None else None
        return requested_info
    
    def get_meta_info(self,
                      request_info: DB_meta
                      ) -> str:
        if request_info.value not in self.requested_data:
            raise SA_RequestItemError(
                error_log=f"requested metadata {request_info.value} c{self.cut_num}{self.processing_component} not exist",
                error_code=SA_ErrorCode.SA_5003
            )
        requested_info = str(self.requested_data[request_info.value])
        return requested_info
    
    def get_status_dict(self,
                        request_status: DB_status,
                        request_non_active: int | None=None
                        ) -> dict | None:
        if request_status == DB_status.NONACTIVE and request_non_active is None:
            raise SA_ProjStructError(
                error_log="get non_active info but non_active index not specified",
                error_code=SA_ErrorCode.SA_5002
            )
        request_status_name = f"non_active_{request_non_active}" if request_status == DB_status.NONACTIVE else request_status.value
        requested_status_dict = self.requested_data.get(request_status_name, None)
        return requested_status_dict
    
    def set_info(self,
                 structure: dict,
                 setting_status: DB_status,
                 setting_info: DB_info,
                 new_value: str,
                 setting_non_active: int | None=None
                 ) -> dict:
        if setting_status == DB_status.NONACTIVE and setting_non_active is None:
            raise SA_ProjStructError(
                error_log="set non_active info but non_active index not specified",
                error_code=SA_ErrorCode.SA_5002
            )
        setting_status_name = f"non_active_{setting_non_active}" if setting_status == DB_status.NONACTIVE else setting_status.value
        if setting_status_name not in structure:
            existing_data = self.get_status_dict(
                request_status=setting_status,
                request_non_active=setting_non_active
            )
            structure[setting_status_name] = existing_data if existing_data is not None else {}
        structure[setting_status_name][setting_info.value] = new_value
        return structure
    
    def set_meta_info(self,
                      structure: dict,
                      setting_info: DB_meta,
                      new_value: str
                      ) -> dict:
        structure[setting_info.value] = new_value
        return structure
    
    def update_remote(self,
                      structure: dict
                      ) -> dict :
        update_sim = MockFirebase.mock_update(
            cut_num=self.cut_num,
            component=self.processing_component,
            structure=structure
        )
        return update_sim