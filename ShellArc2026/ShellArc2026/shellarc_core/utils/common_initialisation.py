import os 

import yaml
from dotenv import load_dotenv
from pathlib import Path

from shellarc_core.auth.access_database import AccessDB as DB
from shellarc_core.auth.access_r2 import Cloudflare_R2_service_Access as R2Access
from shellarc_core.auth.access_spread_sheet import AccessSpreadSheet as GS
from shellarc_core.processor.load_spread_sheet import LoadSpreadSheet as LoadGS
from shellarc_core.processor.request_r2 import Cloudflare_R2_service as R2Access
from shellarc_core.utils.yaml_to_json_convertor import YamlJsonConvertor as YtoJ

class CommonInitialisation():
    def __init__(self, 
                 uninit: list[str] | None=None, 
                 exclude_init_confirm: bool=False
                 ) -> None:
        """
        list var uninit is a list of strings that specifies which part of the initialisation to skip
        Possible values are "setting_db", "project_db", "linker_db", "r2", "spreadsheet"
        bool var exclude_init_confirm is a confirmation flag
        if True, the processes specofied in uninit will be skipped 
        if False, the processes specified in uninit will be ignored and all initialisation processes will be executed
        """
        if uninit is None: 
            self.uninit = []
        else:
            self.uninit = uninit if exclude_init_confirm == True else []

        #access firebase database
        load_dotenv(verbose=True)
        dotenv_path = Path(dotenv_path).resolve().parents[3] / 'project_ctx/.env'
        load_dotenv(dotenv_path)
        collection_name = os.environ.get("init_collection_name")
        
        if uninit != ["setting_db", "project_db", "linker_db", "spreadsheet"] or exclude_init_confirm == True:
          db_instance = DB()
          db = db_instance.database

        """
        firebase DB query structure:
        db.collection(collection_name).document(document_name).get().to_dict() 
        """

        #project setting data object
        if "setting_db" not in self.uninit:
            self._ref_setting_obj = db.collection(collection_name).document("setting")  #project setting data object
            ref_setting_snapshot = db.collection(collection_name).document("setting").get() #project setting data referencer
            self._ref_setting = ref_setting_snapshot.copy() #data copy for property use
            self.proj_setting_data_snapshot = ref_setting_snapshot.to_dict() #project setting data dictionary
            self._proj_setting_data = self.proj_setting_data_snapshot.copy() #property use duplicate
        else:
            setting_yaml_file_path = Path(dotenv_path).resolve().parents[3] / 'project_ctx/project_setting.yaml'
            try:
                with open(setting_yaml_file_path, "r", encoding="utf-8") as f:
                    dict_from_yaml_data = yaml.safe_load(f)
                ytoj = YtoJ(dict_from_yaml_data)
                self.proj_setting_data_snapshot = ytoj.meta_setting
                self._proj_setting_data = self.proj_setting_data_snapshot.copy() #property use duplicate
                self._ref_setting = None
                self._ref_setting_obj = None
            except FileNotFoundError:
                print("File not found")
                return


        if "project_db" not in self.uninit:
            self._ref_collection = db.collection(collection_name).document("main_proj") #project main data referncer
        else:
            self._ref_collection = None

        if "linker_db" not in self.uninit:
            self._ref_linker = db.collection(collection_name).document("linker")
        else:
            self._ref_linker = None

        #access R2 storage
        if "r2" not in self.uninit:
            r2access = R2Access()
            self._s3_client = r2access.s3_client
        else:
            self._s3_client = None

        #access spreadsheet
        if "spreadsheet" not in self.uninit:
            spreadsheet_format_data = db.collection(collection_name).document("spreadsheet_format").get().to_dict() 
            spreadsheet_key = spreadsheet_format_data["spreadsheet_key"]
            gs = GS(spreadsheet_key)
            self._spreadsheet = gs.spreadsheet_obj
            self._loadGS = LoadGS(spreadsheet_format_data, gs.spreadsheet_obj)
        else:
            self._spreadsheet = None
            self._loadGS = None

        #prepare python usable list of components and their corresponding english names 
        component_number = int(self.proj_setting_data_snapshot["component_number"])
        self.component_list = []
        self.component_list_eng = []
        for k in range(1,component_number+1):
            self.component_list.append(self.proj_setting_data_snapshot[f"component{k}"]["display"])
            self.component_list_eng.append(self.proj_setting_data_snapshot[f"component{k}"]["process"])

    @property
    def ref_setting_obj(self):
        return self._ref_setting_obj
    
    @property
    def ref_setting(self):
        return self._ref_setting
    
    @property
    def proj_setting_data(self):
        return self._proj_setting_data
    
    @property
    def ref_collection(self):
        return self._ref_collection
    
    @property
    def ref_linker(self):
        return self._ref_linker
    
    @property
    def s3_client(self):
        return self._s3_client
    
    @property
    def spreadsheet(self):
        return self._spreadsheet
    
    @property
    def loadGS(self):
        return self._loadGS
