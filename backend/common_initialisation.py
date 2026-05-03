import os 

import yaml
from pathlib import Path

from .access_database import AccessDB as DB
from .request_r2 import Cloudflare_R2_service as R2
from .access_r2 import Cloudflare_R2_service_Access as R2Access
from .access_spread_sheet import AccessSpreadSheet as GS
from .load_spread_sheet import LoadSpreadSheet as LoadGS
from .yaml_to_json_convertor import YamlJsonConvertor as YtoJ

class CommonInitialisation():
    def __init__(self, uninit=None, exclude_init_confirm=False):
        if uninit is None: 
            self.uninit = []
        else:
            self.uninit = uninit if exclude_init_confirm == True else []

        #access firebase database
        try:
            import streamlit as st
            collection_name = st.secrets["init"]["collection_name"]
        except:
            from dotenv import load_dotenv
            load_dotenv(verbose=True)
            dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
            load_dotenv(dotenv_path)
            collection_name = os.environ.get("init_collection_name")
            
        db_instance = DB()
        db = db_instance.database

        if "setting_db" not in self.uninit:
            self._ref_setting_obj = db.collection(collection_name).document("setting")  #project setting data object
            ref_setting_snapshot = db.collection(collection_name).document("setting").get() #project setting data referencer
            self._ref_setting = ref_setting_snapshot #property use duplicate
            self.proj_setting_data_snapshot = ref_setting_snapshot.to_dict() #project setting data dictionary
            self._proj_setting_data = self.proj_setting_data_snapshot #property use duplicate
        else:
            setting_yaml_file_path = Path(__file__).resolve().parents[1] / "project_setting.yaml"
            try:
                with open(setting_yaml_file_path, "r", encoding="utf-8") as f:
                    dict_from_yaml_data = yaml.safe_load(f)
                ytoj = YtoJ(dict_from_yaml_data)
                self.proj_setting_data_snapshot = ytoj.meta_setting
                self._proj_setting_data = self.proj_setting_data_snapshot
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
            #spreadsheet_key = self.proj_setting_data_snapshot["spreadsheet_key"]

            spreadsheet_format_data = db.collection(collection_name).document("spreadsheet_format").get().to_dict() 
            #project spreadsheet format data dictionary
            #THIS PART should be deleted 

            #spreadsheet_format_data = dict_from_yaml_data["spreadsheet_format"]
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
