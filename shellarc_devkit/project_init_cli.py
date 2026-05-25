import time
import sys
import os
from pathlib import Path

import gspread
import yaml

from shellarc_core.auth.access_database import AccessDB as DB
from shellarc_core.auth.access_spread_sheet import AccessSpreadSheet as SpreadSheet
from shellarc_core.utils.linker_parser import MakeLinker as MakeLinker


def process_layered_component(index, dict_from_yaml_data):
    return dict_from_yaml_data["component"][index]

def generate_meta(dict_from_yaml_data, collection_name, spreadsheet_key):
    meta_info = {
        "project_name" : dict_from_yaml_data["project_name"],
        "collection_name" : collection_name,
        "mode" : dict_from_yaml_data["mode"],
        "cut_number" : dict_from_yaml_data["cut_number"],
        "component_number" : dict_from_yaml_data["component_number"],
        "parts" : dict_from_yaml_data["parts"],
        "spreadsheet_key" : spreadsheet_key
                 }
    for i in range(1, int(dict_from_yaml_data["component_number"])+1):
        meta_info[f"component{i}"] = process_layered_component(i, dict_from_yaml_data)
    return meta_info

def generate_spreadsheet_format(dict_from_yaml_data):
    spreadsheet_format = {
        "row_before_cut_1" : dict_from_yaml_data["spreadsheet_format"]["row_before_cut_1"],
        "progress_data_n_lines_under_last_cut" : dict_from_yaml_data["spreadsheet_format"]["progress_data_n_lines_under_last_cut"],
        "component_info_range" : dict_from_yaml_data["spreadsheet_format"]["component_info_range"],
        "common_column" : dict_from_yaml_data["spreadsheet_format"]["common_column"],
        "component_info_column_structure" : dict_from_yaml_data["spreadsheet_format"]["component_info_column_structure"],
        "spreadsheet_key" : dict_from_yaml_data["spreadsheet_format"]["spreadsheet_key"]
    }
    return spreadsheet_format

def build_main_proj_db(db, dict_from_yaml_data, proj_collection, spreadsheet_key, linker=None):
    db.collection(proj_collection).document("setting").set(generate_meta(dict_from_yaml_data, proj_collection, spreadsheet_key), merge=True)
    db.collection(proj_collection).document("spreadsheet_format").set(generate_spreadsheet_format(dict_from_yaml_data), merge=True)
    
    process_list_eng = []
    for k in range(1,dict_from_yaml_data["component_number"]+1):
        process_list_eng.append(dict_from_yaml_data["component"][k]["process"])
    ref_collection = db.collection(proj_collection).document("main_proj")
    structure = {
        "current_take" : 0,
        "current_reject_count" : 0,
        "active" : {"naming": None, "cut": None, "take": None, "creator": None, "reviewer": None, "comments": None},
        "temporary" : {"naming": None, "cut": None, "take": None, "creator": None, "reviewer": None, "comments": None}
    }
    for i in range(1,dict_from_yaml_data["cut_number"]+1):
        for work in process_list_eng:
            ref_collection.collection(f"cut{i}").document(work).set(structure, merge=True)

    if linker is not None:
        db.collection(proj_collection).document("linker").set(linker, merge=True)
    else:
        db.collection(proj_collection).document("linker").set({"linker" : "0"}, merge=True)

def inilialize_project():
    proj_setting_yaml = str(input("Input path to project setting yaml file : ")).strip()
    if not proj_setting_yaml or not Path(proj_setting_yaml).exists():
        print("An existing project setting yaml file is needed")
        print("Process abolished")
        return
    
    linker_doc_yaml = str(input("Input path to linker yaml file : ")).strip()
    if proj_setting_yaml and not Path(proj_setting_yaml).exists():
        print("Please input an existing linker yaml file")
        print("Process abolished")
        return
    
    proj_collection = str(input("Input project collection name : ")).strip()
    if not proj_collection:
        print("Input a valid collection name")
        print("Process abolished")
        return
    
    custom_spreadsheet_confirmaton = str(input("Use custom spreafsheet or not (y/N) : ")).strip()
    custom_spreadsheet = custom_spreadsheet_confirmaton in ["y", "Y"]
    if custom_spreadsheet:
        spreadsheet_key = str(input("Input spreadsheet key : ")).strip()
        if not spreadsheet_key:
            print("Input a valid spreadsheet key")
            print("Process abolished")
            return
        
    if not proj_setting_yaml or not proj_collection or not spreadsheet_key:
        print("Invalid inputs detected")
        print("Process abolished")
        return
    
    with open(proj_setting_yaml, "r") as f:
        dict_from_yaml_data = yaml.safe_load(f)
    if linker_doc_yaml:
        with open(linker_doc_yaml, "r") as f:
            linker_doc_dict = yaml.safe_load(f)
        linker_doc_dict = MakeLinker.restructure_linker(linker_doc_dict)
    else:
        linker_doc_dict = None
        
    run_confirmation = str(input("Run project inilialization now ? (y/N) : ")).strip()
    if run_confirmation not in ["y", "Y"]:
        return
    
    time_s = time.time()
    print()
    print("--------------------")
    print("Start initialization process")

    #try access
    try:
        spreadsheet_instance = SpreadSheet(spreadsheet_key)
        spreadsheet = spreadsheet_instance.spreadsheet_obj
        print("Spreadsheet (GCP) access successful")
    except:
        print("Spreadsheet (GCP) access failed")
        print("Process abolished")
        return
    try:
        db_instance = DB()
        db = db_instance.database
        print("Firebase DB access successful")
    except:
        print("Firebase DB access failed")
        print("Process abolished")
        return
        
    try:
        build_main_proj_db(db, dict_from_yaml_data, proj_collection, spreadsheet_key, linker=linker_doc_dict)
        print("Database build successful")
    except:
        print("Database build failed")
        print("Process abolished")
        return
    
    print(f"Inilialization completed in {time.time() - time_s} seconds")
    print("--------------------")
    print()

if __name__ == "__main__":
    inilialize_project()