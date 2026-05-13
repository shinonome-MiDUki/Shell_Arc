import tempfile
import shutil
from pathlib import Path

import bpy

from .shellarc_core.utils.common_initialisation import CommonInitialisation as Common
from .shellarc_core.processor.request_r2 import Cloudflare_R2_service as R2Service

class BlenderOperation:
    def __init__(self):
        pass

    def make_new_file(self,
                      asset_name: str,
                      saving_dir: str
                      ) -> None:
        bpy.ops.wm.read_homefile(app_template='')
        default_coll = bpy.data.collections.get("Collection")
        default_coll.name = asset_name
        if not Path(saving_dir).exists():
            Path(saving_dir).mkdir(parents=True)
        bpy.ops.wm.save_as_mainfile(filepath=f"{saving_dir}/{asset_name}.blend")

    def open_file(self,
                  local_path: str
                  ) -> None:
        bpy.ops.wm.open_mainfile(filepath=local_path)

    def snapshot_file(self) -> None:
        if not "snapshot_path" in bpy.context.scene \
            or bpy.context.scene["snapshot_path"] == ""\
            or not Path(bpy.context.scene["snapshot_path"]).exists():
            current_file_path = bpy.data.filepath
            snapshot_dir = Path(tempfile.mkdtemp)
            snapshot_path = snapshot_dir / f"{Path(current_file_path).stem}_snapshot.blend"
            bpy.context.scene["snapshot_path"] = str(snapshot_path)
        snapshot_path = bpy.context.scene["snapshot_path"]
        bpy.ops.wm.save_as_mainfile(filepath=snapshot_path, copy=True)

    def save_file(self) -> str:
        current_file_path = bpy.data.filepath
        bpy.ops.wm.save_as_mainfile()
        return current_file_path
    
    def delete_snapshot_dir(self) -> None:
        if not "snapshot_path" in bpy.context.scene \
            or bpy.context.scene["snapshot_path"] == ""\
            or not Path(bpy.context.scene["snapshot_path"]).exists():
            return
        snapshot_path = bpy.context.scene["snapshot_path"]
        shutil.rmtree(snapshot_path)
        bpy.context.scene["snapshot_path"] = ""

class BackendCommunication:
    def __init__(self):
        self.sa_common = Common()
        self.blender_ops = BlenderOperation()

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
        cg_asset_data = self.sa_common.ref_cg_obj.collection("assets").document("general_data").get().to_dict()
        return cg_asset_data
    
    def set_asset_metadata(self,
                           asset_name: str,
                           status: str
                           ) -> None:
        self.sa_common.ref_cg_obj.collection("assets").document("general_data").update({asset_name : status})
        

    def get_cg_data(self,
                    asset_name: str
                    ) -> dict:
        cg_asset_data = self.sa_common.ref_cg_obj.collection("assets").document(asset_name).get().to_dict()
        return cg_asset_data


    def get_member_data(self,
                        mem_id: str
                        ) -> list:
        """
        This lists the accessibility to each assets of each registered member 
        It is a dict storing member_id: str - accessible_asset_list: str
        The "accessible_asset_list" is a str in which asset names are separeted by "*"
        """
        member_accessible = self.sa_common.ref_cg_obj.collection("members").document("accessible").get().to_dict()
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
        current_cg_asset_data = self.sa_common.ref_cg_obj.collection("assets").document("general_data").get().to_dict()
        if asset_name in current_cg_asset_data:
            return
        self.sa_common.ref_cg_obj.collection("assets").add(asset_name)
        self.sa_common.ref_cg_obj.collection("assets").document("general_data").update({asset_name : "0"})
        
    
    def request_asset(self,
                      asset_name: str,
                      saving_dir: str
                      ) -> str:
        asset_metadata = self.get_asset_metadata()
        asset_status = asset_metadata[asset_name]

        if asset_status == "1" or asset_status == "2":
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
        
        if asset_status == "1":
            self.blender_ops.make_new_file(
                asset_name=asset_name,
                saving_dir=saving_dir
            )
            return asset_name
        elif asset_status == "2":
            if not Path(saving_dir).exists():
                Path(saving_dir).mkdir(parents=True)
            r2_service = R2Service(s3_client=self.sa_common.s3_client)
            download_status = r2_service.download_file(
                to_download_file=f"cg/asset/{asset_name}/{asset_name}.blend",
                download_dest=saving_dir,
                file_naming=f"{asset_name}.blend"
                )
            if not download_status:
                return "NOT_EXIST"
            self.blender_ops.open_file(local_path=f"{saving_dir}/{asset_name}.blend")
            return asset_name
        
    def upload_asset(self,
                     asset_name: str
                     ) -> str:
        current_local_path = self.blender_ops.save_file()
        r2_service = R2Service(s3_client=self.sa_common.s3_client)
        upload_status = r2_service.upload_file(
            local_file_path=current_local_path,
            cloud_file_path=f"cg/asset/{asset_name}/{asset_name}.blend"
        )
        if not upload_status:
            return "UPLOAD ERROR"
        self.blender_ops.delete_snapshot_dir()
        return asset_name

class DiscordCommunication:
    def __init__(self):
        pass