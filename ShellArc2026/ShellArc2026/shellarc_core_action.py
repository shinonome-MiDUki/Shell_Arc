from pathlib import Path

import bpy

from .shellarc_blender_action import BlenderOperation, LocalOperation
from .shellarc_core.utils.common_initialisation import CommonInitialisation as Common
from .shellarc_core.processor.request_r2 import Cloudflare_R2_service as R2Service
    

class BackendCommunicationLogic:
    def __init__(self,
                 submission_type_name: str,
                 accessibility_db_label: str
                 ):
        self.submission_type_name = submission_type_name
        self.accessibility_db_label = accessibility_db_label
        self.sa_common = Common()

    def get_asset_metadata(self) -> dict:
        """
        The document "general_data" stores a dict of asset_name: str - status: str pair
        status codes are :
        "0" - not assigned
        "1" - assigned but file not made
        "2" - assigned and file made but free now
        "3" - someone working on
        "4" - locked
        "5" - under merging
        """
        cg_asset_data = self.sa_common.ref_cg_obj.collection(self.submission_type_name).document("general_data").get().to_dict()
        return cg_asset_data
    
    def set_asset_metadata(self,
                           asset_name: str,
                           status: list[str]
                           ) -> None:
        self.sa_common.ref_cg_obj.collection(self.submission_type_name).document("general_data").update({asset_name : status})
        

    def get_cg_data(self,
                    asset_name: str
                    ) -> dict:
        cg_asset_data = self.sa_common.ref_cg_obj.collection(self.submission_type_name).document(asset_name).get().to_dict()
        return cg_asset_data


    def get_member_data(self,
                        mem_id: str
                        ) -> list:
        """
        This lists the accessibility to each assets of each registered member 
        It is a dict storing member_id: str - accessible_asset_list: str
        The "accessible_asset_list" is a str in which asset names are separeted by "*"
        """
        member_accessible = self.sa_common.ref_cg_obj.collection("members").document(self.accessibility_db_label).get().to_dict()
        if mem_id not in member_accessible:
            return []
        accessible_assets = member_accessible[mem_id]
        if accessible_assets == "ALL":
            return ["ALL"]
        elif accessible_assets == "NIL":
            return ["NIL"]
        accessible_assets_list = accessible_assets.split("*")
        return accessible_assets_list
    
    def register_asset(self,
                       asset_name: str
                       ) -> None:
        current_cg_asset_data = self.sa_common.ref_cg_obj.collection(self.submission_type_name).document("general_data").get().to_dict()
        if asset_name in current_cg_asset_data:
            return
        self.sa_common.ref_cg_obj.collection(self.submission_type_name).add(asset_name)
        self.sa_common.ref_cg_obj.collection(self.submission_type_name).document("general_data").update({asset_name : ["0", ""]})
    
    def request_asset(self,
                      ctx: bpy.context,
                      mem_id: str,
                      asset_name: str,
                      saving_dir: str
                      ) -> str:
        asset_metadata = self.get_asset_metadata()
        asset_status_info = asset_metadata[asset_name]
        asset_status = asset_status_info[0]
        asset_status_owner = asset_status_info[1]

        if asset_status == "1" or asset_status == "2" or asset_status_owner == mem_id:
            pass
        elif asset_status == "0":
            return "NOT_ASSIGNED"
        elif asset_status == "3":
            return "LOCKED_WORKING"
        elif asset_status == "4":
            return "LOCKED"
        elif asset_status == "5":
            return "LOCKED_MERGING"
        else:
            return "ERROR"
        
        LocalOperation.freeze_locally(ctx=ctx)
        if asset_status != "1":
            if not Path(saving_dir).exists():
                Path(saving_dir).mkdir(parents=True)
            r2_service = R2Service(s3_client=self.sa_common.s3_client)
            download_status = r2_service.download_file(
                to_download_file=f"cg/{self.submission_type_name}/{asset_name}/{asset_name}.blend",
                download_dest=saving_dir,
                file_naming=f"{asset_name}.blend"
                )
            if not download_status:
                return "DOWNLOAD_ERROR"
            BlenderOperation.open_file(local_path=f"{saving_dir}/{asset_name}.blend")
        else:
            BlenderOperation.make_new_file(
                asset_name=asset_name,
                saving_dir=saving_dir
            )
        return asset_name
        
    def upload_asset(self,
                     ctx: bpy.context,
                     asset_name: str
                     ) -> str:
        current_local_path = BlenderOperation.save_file()
        r2_service = R2Service(s3_client=self.sa_common.s3_client)
        upload_status = r2_service.upload_file(
            local_file_path=current_local_path,
            cloud_file_path=f"cg/{self.submission_type_name}/{asset_name}/{asset_name}.blend"
        )
        if not upload_status:
            return "UPLOAD ERROR"
        LocalOperation.delete_snapshot_dir(ctx=ctx)
        return asset_name
    
    def submit_action(self,
                      ctx: bpy.context,
                      asset_name: str,
                      status: list[str]
                      ) -> str:
        upload_status = self.upload_asset(
            ctx=ctx,
            asset_name=asset_name
        )
        if upload_status != asset_name:
            return upload_status
        self.set_asset_metadata(
            asset_name=asset_name,
            status=status
        )
        return upload_status
    
class BackendCommunication(BackendCommunicationLogic):
    def __init__(self,
                 ctx: bpy.context
                 ):
        submission_type = "assets" if ctx.scene.shellarc_prop_bool_ismodellingmode else "shots"
        initial_value_dict = {
            "submission_type_name" : {
                "assets" : "assets",
                "shots" : "shots"
            },
            "accessibility_db_label" : {
                "assets" : "accessible",
                "shots" : "shot_responsibility"
            }
        }
        super().__init__(
            submission_type_name=initial_value_dict["submission_type_name"][submission_type],
            accessibility_db_label=initial_value_dict["accessibility_db_label"][submission_type]
        )

class DiscordCommunication:
    def __init__(self):
        pass