import time
import sys
import os

import streamlit as st
import gspread
import yaml

project_root = os.path.dirname(os.path.abspath(__file__)) 
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.access_database import AccessDB as DB
from backend.access_spread_sheet import AccessSpreadSheet as SpreadSheet

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
        "component_info_column_structure" : dict_from_yaml_data["spreadsheet_format"]["component_info_column_structure"]
    }
    return spreadsheet_format

def build_main_proj_db(db, dict_from_yaml_data, proj_collection, spreadsheet_key):
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
            ref_collection.collection(f"cut{i:02}").document(work).set(structure, merge=True)

def build_main_proj_spread_sheet(spreadsheet, dict_from_yaml_data, proj_collection):
    cut_number = int(dict_from_yaml_data["cut_number"])
    parts_info = dict_from_yaml_data["parts"]
    spreadsheet.update_acell("B4", "パート")
    for part in parts_info:
        part_range = parts_info[part]
        starting_cut = part_range[0]
        spreadsheet.update_acell(f"B{4+starting_cut}", part)
    spreadsheet.update_acell("C4", "カット")
    spreadsheet.update(f"C5:C{4+cut_number}", [[cut_index] for cut_index in range(1, cut_number+1)])
    spreadsheet.update_acell("D4", "難易度")
    component_number = int(dict_from_yaml_data["component_number"])
    component_info = dict_from_yaml_data["component"]
    for work_index in range(1, component_number+1):
        work_info = component_info[work_index]
        work_name = work_info["display"]
        alphabets = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        starting_column_index = (3+(work_index*2))-1
        spreadsheet.update_acell(f"{alphabets[starting_column_index]}3", work_name)
        spreadsheet.update_acell(f"{alphabets[starting_column_index]}4", "担当")
        spreadsheet.update_acell(f"{alphabets[starting_column_index+1]}4", "状態")
        spreadsheet.update_acell(f"{alphabets[starting_column_index]}{cut_number+6}", 0.0)

def main():
    st.set_page_config(
        page_title="プロジェクト設定ページ",
        page_icon=":snail:"
    )
    st.write("新規プロジェクトをビルドするには、管理員権限が必要です")
    pw = st.text_input("管理員ID", type="password")
    if pw == st.secrets["super"]["id"]:
        proj_setting_yaml = st.file_uploader("プロジェクト設定ファイル(.yaml)", type=["yaml"])
        proj_collection = str(st.text_input("プロジェクトコレクション名を入力してください"))
        if proj_collection != st.secrets["init"]["collection_name"] and proj_collection != "":
            st.write("プロジェクトコレクションが不正です")
            return
        spreadsheet_key = str(st.text_input("使うスプレッドシートのキーを入力してください"))
        custom_spreadsheet = st.checkbox("カスタムスプレッドシートを使います")
        if proj_setting_yaml is not None and proj_collection != "" and spreadsheet_key != "":
            dict_from_yaml_data = yaml.safe_load(proj_setting_yaml)
            if st.button("プロジェクトをビルド"):
                with st.spinner("ビルド中"):
                    time.sleep(0.5)
                    #build spreadsheet
                    try:
                        spreadsheet_instance = SpreadSheet(spreadsheet_key)
                        spreadsheet = spreadsheet_instance.spreadsheet_obj
                    except:
                        st.write("スプレッドシートアクセス失敗。スプレッドシートキーと共有設定を確認してください")
                        return
                    if not custom_spreadsheet:
                        build_main_proj_spread_sheet(spreadsheet, dict_from_yaml_data, proj_collection)

                    #build firebase DB
                    db_instance = DB()
                    db = db_instance.database
                    build_main_proj_db(db, dict_from_yaml_data, proj_collection, spreadsheet_key)
                    st.write("ビルド完了")
    elif pw != st.secrets["super"]["id"] and pw != "":
        st.warning("IDは不正です")

if __name__ == '__main__':
    main()


                
#conda activate null_proj; cd /Users/shiinaayame/Documents/null_proj_urlONLY; streamlit run pages/project_setting.py