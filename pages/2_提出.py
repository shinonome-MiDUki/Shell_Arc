import time
import os
import sys

import streamlit as st

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

    #User input name
    submitting_person = str(st.text_input("ここに名前を記入してください"))

    #User input submitting cut
    submitting_cut = int(st.selectbox(
        "提出するカットを選択してください",
        [i for i in range(1, cut_num+1)]
    ))

    #User input submitting component
    submitting_component = st.selectbox(
        "提出する部分を選択してください",
        [proj_setting_data[f"component{j}"]["display"] for j in range(1, component_number+1)]
    )
    working_data = common.work_info(submitting_component)
    working_index = working_data["working_index"]
    working_component = working_data["working_component"]
    required_format = working_data["required_format"]
    mime_format = working_data["mime_format"]

    #Check person incharge
    member_incharge = str(loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=submitting_cut, target_info="member", component_index=working_index))
    if member_incharge != submitting_person and member_incharge not in [None, "None"] and submitting_person != "":
        st.write(f"この作業は {member_incharge}さん の担当です。ご確認の上作業を進めてください")

    if submitting_component is not None:
        #access work database
        ref_work_obj = ref_collection.collection(f"cut{submitting_cut:02}").document(working_component)
        ref_work = ref_work_obj.get()
        work_data = ref_work.to_dict()

        difficulty = str(loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=submitting_cut, target_info="difficulty"))
        st.write(f"難易度分類：{difficulty}")

        #Uploading file
        submission = st.file_uploader("ここに提出ファイルをアップロードしてください", type=required_format)
        if st.button("提出") and submission is not None:
            with st.spinner("アップロード中"):

                #renaming
                current_take = int(work_data["current_take"]) + 1
                naming_reference = []
                for i in range(0, proj_setting_data[f"component{working_index}"]["naming_section"]):
                    process_subdata = proj_setting_data[f"component{working_index}"]
                    naming_rule = process_subdata[f"name_component_{i+1}"]
                    if naming_rule.startswith("-"):
                        if naming_rule == "-cut":
                            naming_reference.append(f"cut{submitting_cut:02}")
                        elif naming_rule == "-take":
                            naming_reference.append(f"take{current_take:02}")
                    else:
                        naming_reference.append(naming_rule)
                renamed = "_".join(naming_reference)

                #update database
                if work_data["temporary"]["naming"] != None:
                    current_reject_count = int(work_data["current_reject_count"]) 
                    temporary = {"naming": renamed, "cut": submitting_cut, "take": current_take, "creator": str(submitting_person), "reviewer": None, "comments": None}
                    rejected = work_data["temporary"]
                    rejected_index = f"non_active_{rejected['take']:02}"
                    structure = {
                        "current_take" : current_take,
                        "current_reject_count" : current_reject_count + 1,
                        "temporary" : temporary,
                        rejected_index : rejected
                    }
                else:
                    current_reject_count = int(work_data["current_reject_count"])
                    temporary = {"naming": renamed, "cut": submitting_cut, "take": current_take, "creator": str(submitting_person), "reviewer": None, "comments": None}
                    structure = {
                        "current_take" : current_take,
                        "current_reject_count" : current_reject_count + 1,
                        "temporary" : temporary
                    }
                ref_work_obj.update(structure)

                #upload to  R2 storage
                r2 = R2()
                r2.upload_file(submission, f"{proj_setting_data['collection_name']}/cut{submitting_cut:02}/{working_component}/{renamed}.{required_format[0]}")

                #update spreadsheet
                loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=submitting_cut, target_info="member", update_info=submitting_person, component_index=working_index)
                loadGS.load_spreadsheet(spreadsheet=spreadsheet, cut_index=submitting_cut, target_info="situation", update_info="作業中", component_index=working_index)

                st.write("提出が完了しました。お疲れ様でした！")


if __name__ == '__main__':
    pw = st.text_input("管理員ID", type="password")
    if pw == st.secrets["super"]["id"]:
      main()




#  conda activate null_proj ; cd /Users/shiinaayame/Documents/null_proj_urlONLY/main/pages ; streamlit run submission.py

