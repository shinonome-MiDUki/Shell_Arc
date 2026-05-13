import os 

import yaml
from pathlib import Path

from ..auth.access_database import AccessDB as DB
from ..auth.access_r2 import Cloudflare_R2_service_Access as R2Access
from ..auth.access_spread_sheet import AccessSpreadSheet as GS
from ..processor.load_spread_sheet import LoadSpreadSheet as LoadGS
from ..utils.yaml_to_json_convertor import YamlJsonConvertor as YtoJ
from ..keys.decoder import get_creds

class CommonInitialisation():
    def __init__(self) -> None:

        #access firebase database
        service_account_info = get_creds(service="init")
        collection_name = service_account_info["init_collection_name"]
        
        db_instance = DB()
        db = db_instance.database

        """
        firebase DB query structure:
        db.collection(collection_name).document(document_name).get().to_dict() 
        """

        self._ref_cg_obj = db.collection(collection_name).document("cg")
        ref_cg_snapshot = db.collection(collection_name).document("cg").get()
        self._ref_cg = ref_cg_snapshot
        self.proj_cg_data_snapshot = ref_cg_snapshot.to_dict()
        self._proj_cg_data = self.proj_cg_data_snapshot

        #access R2 storage
        r2access = R2Access()
        self._s3_client = r2access.s3_client

        #access spreadsheet
        spreadsheet_format_data = db.collection(collection_name).document("spreadsheet_format").get().to_dict() 
        spreadsheet_key = spreadsheet_format_data["spreadsheet_key"]
        gs = GS(spreadsheet_key)
        self._spreadsheet = gs.spreadsheet_obj
        self._loadGS = LoadGS(spreadsheet_format_data, gs.spreadsheet_obj)

    @property
    def ref_cg_obj(self):
        return self._ref_cg_obj
    
    @property
    def ref_cg(self):
        return self._ref_cg
    
    @property
    def proj_cg_data(self):
        return self._proj_cg_data
    
    @property
    def s3_client(self):
        return self._s3_client
    
    @property
    def spreadsheet(self):
        return self._spreadsheet
    
    @property
    def loadGS(self):
        return self._loadGS
