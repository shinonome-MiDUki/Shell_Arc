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
    ref_setting_obj = common.ref_setting_obj  #project setting data object   
    ref_setting = common.ref_setting #project setting data referncer
    proj_setting_data = common.proj_setting_data #project setting data dictionary
    ref_collection = common.ref_collection #project main data referncer

    #access spreadsheet
    spreadsheet = common.spreadsheet
    loadGS = common.loadGS
    
    #obtain or set needed variables 
    cut_num = int(proj_setting_data["cut_number"])
    component_number = int(proj_setting_data["component_number"])
    is_reviewing = False

    #User input reviewing cut
    reviewing_cut = int(st.selectbox(
        "検査するカットを選択してください",
        [i for i in range(1, cut_num+1)]
    ))

    #User input reviewing component
    reviewing_component = st.selectbox(
        "検査する部分を選択してください",
        [proj_setting_data[f"component{j}"]["display"] for j in range(1, component_number+1)]
    )
    working_data = common.work_info(reviewing_component)
    working_index = working_data["working_index"]
    working_component = working_data["working_component"]
    required_format = working_data["required_format"]
    mime_format = working_data["mime_format"]

    #access work database
    ref_work_obj = ref_collection.collection(f"cut{reviewing_cut:02}").document(working_component)
    ref_work = ref_work_obj.get()
    work_data = ref_work.to_dict()

    #Check reviewing file existance 
    if work_data["temporary"]["naming"] == None:
        st.write("検査待ちの提出物はありません")
        return
    else:
        member_incharge = str(loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=reviewing_cut, target_info="member", component_index=working_index))
        st.write(f"{member_incharge}さん の担当部分です")

     #User input name
    reviewing_person = str(st.text_input("ここに名前を記入してください"))

    if st.button("ファイルを取得"):
        #naming
        renamed = work_data["temporary"]["naming"]

        #download from R2 storage
        if not is_reviewing:
            is_reviewing = True
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
                return
        
    #Reviewer's reaction (comment or approval)
    comment_or_approve = st.radio(
        "行なっている検査作業を選択してください",
        ["コメント", "完了許可"]
    )
    is_commenting = comment_or_approve == "コメント"

    if is_commenting: #Commenting
        comment = str(st.text_input("ここにコメントを記入してください"))
        submit = st.button("コメントを記録")
        if comment != "" and submit:
            ref_work_obj.update({"temporary.comments" : comment , "temporary.reviewer" : reviewing_person})
            st.write("コメントが記録されました")
            is_reviewing = False

    else: #Approving
        approval = st.radio(
            "完了を許可しますか",
            ["はい", "いいえ"]
        )
        is_approved = approval == "はい"
        #Check if there has already been an approved file that has to be overwritten
        is_need_overwrite = work_data["active"]["naming"] != None
        is_overwrite = True 
        if is_need_overwrite:
            overwrite_ask = st.radio(
                "最新確定ファイルはすでに存在しています。上書きしますか",
                ["はい", "いいえ"]
            )
            is_overwrite = overwrite_ask == "はい"
        is_confirm = st.button("確定")
            
        if is_confirm and is_approved and is_overwrite:
            if is_need_overwrite:
                current_reject_count = int(work_data["current_reject_count"]) + 1
                rejected = work_data["active"]
                active = work_data["temporary"]
                rejected_index = f"non_active_{rejected['take']:02}"
                structure = {
                    "active" : active,
                    "temporary" : {"naming": None, "cut": None, "take": None, "creator": None, "reviewer": None, "comments": None},
                    "current_reject_count" : current_reject_count + 1,
                    rejected_index : rejected
                }
                ref_work_obj.update(structure)
            else:
                active = work_data["temporary"]
                structure = {
                    "active" : active,
                    "temporary" : {"naming": None, "cut": None, "take": None, "creator": None, "reviewer": None, "comments": None}
                }
                ref_work_obj.update(structure)
                current_progress = float(proj_setting_data[f"component{working_index}"]["progress"])
                current_progress += (1 / cut_num)
                loadGS.load_progress(spreadsheet, working_index, False, cut_num)
                ref_setting_obj.update({f"component{working_index}.progress" : current_progress})
            loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=reviewing_cut, target_info="situation", update_info="完了", component_index=working_index)
            st.write("アップデートが完了しました")
        elif is_confirm and (not is_approved or not is_overwrite): 
            st.write("検査作業を終了します")
            return
                    
if __name__ == '__main__':
    st.write("作画を検査するには、検査権限が必要です")
    pw = st.text_input("検査員ID", type="password")
    if pw == st.secrets["super"]["checker_id"]:
        main()