import streamlit as st

from .access_database import AccessDB as DB
from .request_r2 import Cloudflare_R2_service as R2
from .access_spread_sheet import AccessSpreadSheet as GS
from .load_spread_sheet import LoadSpreadSheet as LoadGS

class CommonInitialisation():
    def __init__(self):
        #access firebase database
        collection_name = st.secrets["init"]["collection_name"]
        db_instance = DB()
        db = db_instance.database

        self._ref_setting_obj = db.collection(collection_name).document("setting")  #project setting data object
        ref_setting_snapshot = db.collection(collection_name).document("setting").get() #project setting data referencer
        self._ref_setting = ref_setting_snapshot #property use duplicate
        self.proj_setting_data_snapshot = ref_setting_snapshot.to_dict() #project setting data dictionary
        self._proj_setting_data = self.proj_setting_data_snapshot #property use duplicate

        self._ref_collection = db.collection(collection_name).document("main_proj") #project main data referncer

        #access spreadsheet
        spreadsheet_key = self.proj_setting_data_snapshot["spreadsheet_key"]
        spreadsheet_format_data = db.collection(collection_name).document("spreadsheet_format").get().to_dict() #project spreadsheet format data dictionary
        gs = GS(spreadsheet_key)
        self._spreadsheet = gs.spreadsheet_obj
        self._loadGS = LoadGS(spreadsheet_format_data)

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
    def spreadsheet(self):
        return self._spreadsheet
    
    @property
    def loadGS(self):
        return self._loadGS
    
    def work_info(self, processing_component):
        working_index = self.component_list.index(processing_component) + 1
        working_component = self.component_list_eng[working_index-1]
        required_format = [self.proj_setting_data[f"component{working_index}"]["format"][0]]
        mime_format = [self.proj_setting_data[f"component{working_index}"]["format"][1]]
        rtn = {
             "working_index" : working_index,
             "working_component" : working_component,
             "required_format" : required_format,
             "mime_format" : mime_format
        }
        return rtn