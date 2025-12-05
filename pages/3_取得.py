import time
import tempfile
import os
import sys
from pathlib import Path

import streamlit as st
from platformdirs import user_downloads_path

project_root = os.path.dirname(os.path.abspath(__file__)) 
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.request_r2 import Cloudflare_R2_service as R2
from backend.common_initialisation import CommonInitialisation as Common

def main():
    st.set_page_config(
        page_title="プロジェクト設定ページ",
        page_icon=":snail:"
    )
    
    common = Common()

    #access firebase database
    ref_setting = common.ref_setting #project setting data referncer
    proj_setting_data = common.proj_setting_data #project setting data dictionary
    ref_collection = common.ref_collection #project main data referncer

    #access spreadsheet
    spreadsheet = common.spreadsheet
    loadGS = common.loadGS

    #obtain or set needed variables
    cut_num = int(proj_setting_data["cut_number"])
    component_number = int(proj_setting_data["component_number"])

    #User input requesting cut
    reviewing_cut = int(st.selectbox(
        "取得するカットを選択してください",
        [i for i in range(1, cut_num+1)]
    ))

    #User input requesting request work
    reviewing_component = st.selectbox(
        "取得する部分を選択してください",
        [proj_setting_data[f"component{j}"]["display"] for j in range(1, component_number+1)]
    )
    working_data = common.work_info(reviewing_component)
    working_index = working_data["working_index"]
    working_component = working_data["working_component"]
    required_format = working_data["required_format"]
    mime_format = working_data["mime_format"]

    difficulty = str(loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=reviewing_cut, target_info="difficulty"))
    st.write(f"難易度分類：{difficulty}")

    #access work database
    ref_work = ref_collection.collection(f"cut{reviewing_cut:02}").document(working_component).get() #project work data referncer
    work_data = ref_work.to_dict() #project work data dictionary

    #User input requesting take
    current_take = int(work_data["current_take"])
    reviewing_take_selection = st.selectbox(
        "取得するテイクを選択してください",
        ["最新"] + [i for i in range(1, current_take)]
    )
    temp_or_active = None
    if reviewing_take_selection == "最新": #Ask for requesting version
        reviewing_take = int(current_take)
        if  work_data["active"]["naming"] != None and work_data["temporary"]["naming"] != None:
            temp_or_active_selection = st.radio(
                "作業中ファイルと最新確定ファイルが同時に存在する。どれを取得しますか",
                ["作業中ファイル", "最新確定ファイル"]
            )
            temp_or_active = temp_or_active_selection == "最新確定ファイル"
    else:
        reviewing_take = int(reviewing_take_selection)

    #Procress status 
    reviewing_dir, status = None, None
    if reviewing_take_selection == "最新" and temp_or_active == None:
        reviewing_dir = work_data["active"] if work_data["active"]["naming"] != None else work_data["temporary"]
        status = "完了" if work_data["active"]["naming"] != None else "作業中"
    elif reviewing_take_selection == "最新" and temp_or_active != None:
        reviewing_dir = work_data["active"] if temp_or_active else work_data["temporary"]
        status = "完了" if temp_or_active else "作業中"
    else:
        reviewing_dir = work_data[f"non_active_{reviewing_take:02}"]

    if reviewing_dir["naming"] == None:
        st.write("未着手のため該当のファイルが見つかりません")
        return
    
    if status is not None : st.write(f"ステータス：{status}")
    
    if st.button("取得"):
        #Show comments if exist
        if reviewing_dir["comments"] != None:
            st.write(reviewing_dir["comments"])
        else:
            st.write("コメントはありません")
        #Naming
        renamed = reviewing_dir["naming"]

        #download from R2 storage
        r2 = R2()
        try:
            with st.spinner("ダウンロード中"):
                r2.download_file(
                    f"{renamed}.{required_format[0]}",
                    f"{proj_setting_data['collection_name']}/cut{reviewing_cut:02}/{working_component}/{renamed}.{required_format[0]}",
                    tempfile.gettempdir()
                )     
                download_dir : Path = user_downloads_path()
                destination_path : Path = f"{download_dir}/{renamed}.{required_format[0]}"
                download_dir.mkdir(parents=True, exist_ok=True)
                temp_file_path = f"{tempfile.gettempdir()}/{renamed}.{required_format[0]}"
                os.rename(temp_file_path, str(destination_path))
                st.write("ダウンロードディレクトリに保存しました")
        except Exception as e:
            st.write(f"Python error : {e}")
            st.write("技術班へご報告ください")


if __name__ == '__main__':
    pw = st.text_input("管理員ID", type="password")
    if pw == st.secrets["super"]["id"]:
      main()