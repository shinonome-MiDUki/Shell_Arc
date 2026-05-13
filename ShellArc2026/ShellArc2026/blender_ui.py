import os
import pickle
from pathlib import Path

import bpy
from bpy.types import Operator, Panel
from bpy.props import (
    EnumProperty,
    StringProperty
)

import keyring

from .shellarc_action import BlenderOperation, BackendCommunication

def update_asset_list(backend_communication: BackendCommunication | None=None) -> None:
    asset_list = []
    if backend_communication is None:
        backend_communication = BackendCommunication()
    pref = bpy.context.preferences
    addon_pref = pref.addons[__package__].preferences
    accessible_asset_set = backend_communication.get_member_data(mem_id=addon_pref.member_id)
    print(type(accessible_asset_set))
    asset_dict = backend_communication.get_asset_metadata()
    if accessible_asset_set != ["NIL"]:
        for asset in asset_dict:
            if accessible_asset_set == ["ALL"]:
                asset_list.append((asset, asset, asset))
                continue
            if asset not in accessible_asset_set:
                continue
            asset_list.append((asset, asset, asset))
    cache_path = Path(__file__).resolve().parent / "asset_list.pkl"
    with open(cache_path, "wb") as f:
        pickle.dump(asset_list, f)
    
class SHELLARC_getfile_Nop(Operator):

    bl_idname = "object.shellarc_getfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバからロードする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name = context.scene.shellarc_prop_enum
        backend_communication = BackendCommunication()
        getfile_status = backend_communication.request_asset(
            asset_name=asset_name,
            saving_dir=context.scene.shellarc_prop_str_savepath
        )
        backend_communication.set_asset_metadata(
            asset_name=asset_name,
            status="3"
        )
        if getfile_status != asset_name:
            self.report({'INFO'}, f"loaded blend file failed : {getfile_status}")
            return {'CANCELLED'}
        bpy.context.scene["under_progress"] = True
        self.report({'INFO'}, f"loaded blend file")
        return {'FINISHED'}
    
class SHELLARC_exclock_Nop(Operator):

    bl_idname = "object.shellarc_exclock_nop"
    bl_label = "NOP"
    bl_description = "排他ロックをかける"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name = context.scene.shellarc_prop_enum
        backend_communication = BackendCommunication()
        if backend_communication.get_asset_metadata()[asset_name] not in ["1", "2"]:
            self.report({'INFO'}, f"locking failed. Someone is locking")
            return {'CANCELLED'}
        backend_communication.set_asset_metadata(
            asset_name=asset_name,
            status="4")
        self.report({'INFO'}, f"locked")
        return {'FINISHED'}
    
class SHELLARC_reloadassetlist_Nop(Operator):

    bl_idname = "object.shellarc_reloadassetlist_nop"
    bl_label = "NOP"
    bl_description = "アセットリストをリロードする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        update_asset_list()
        return {'FINISHED'}
    
class SHELLARC_commitfile_Nop(Operator):

    bl_idname = "object.shellarc_commitfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバでキャッシュする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        BlenderOperation().snapshot_file()
        return {'FINISHED'}
    
class SHELLARC_submitfile_Nop(Operator):

    bl_idname = "object.shellarc_submitfile_nop"
    bl_label = "NOP"
    bl_description = "ファイルをサーバに提出する"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        asset_name=Path(bpy.data.filepath).stem
        backend_communication = BackendCommunication()
        backend_communication.upload_asset(
            asset_name=asset_name
        )
        backend_communication.set_asset_metadata(
            asset_name=asset_name,
            status="2"
        )
        context.scene["under_progress"] = False
        update_asset_list(backend_communication=backend_communication)
        return {'FINISHED'}
    
class SHELLARC_login_Nop(Operator):

    bl_idname = "object.shellarc_login_nop"
    bl_label = "NOP"
    bl_description = "ログインする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not keyring.get_password("shellarc", "shellarc"):
            decode_key = context.scene.shellarc_prop_str_decodekey
            keyring.set_password("shellarc", "shellarc", decode_key)

        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        mem_id = context.scene.shellarc_prop_str_memid

        backend_communication = BackendCommunication()
        accessible_asset_set = backend_communication.get_member_data(mem_id=mem_id)
        if accessible_asset_set == []:
            self.report({'INFO'}, f"Invalid ID")
            return {'CANCELLED'}
        addon_pref.member_id = mem_id
        update_asset_list(backend_communication=backend_communication)
        self.report({'INFO'}, f"logged-in as {mem_id}")
        return {'FINISHED'}

class SHELLARC_logout_Nop(Operator):

    bl_idname = "object.shellarc_logout_nop"
    bl_label = "NOP"
    bl_description = "ログアウトする"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        addon_pref.member_id = ""
        self.report({'INFO'}, f"logged-out")
        return {'FINISHED'}


class SHELLARC_BLENDER_CustomPanel(Panel):

    bl_label = "ShellArc 2026"         
    bl_space_type = 'VIEW_3D'           
    bl_region_type = 'UI'               
    bl_category = "ShellArc"      
    bl_context = "objectmode"        

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='PLUGIN')

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        pref = context.preferences
        addon_pref = pref.addons[__package__].preferences
        mem_id = addon_pref.member_id if addon_pref is not None else ""

        if not mem_id:
            layout.prop(scene, "shellarc_prop_str_memid", text="作業者ID")
            if not keyring.get_password("shellarc", "shellarc"):
                layout.prop(scene, "shellarc_prop_str_decodekey", text="デコードキー")
            layout.operator(SHELLARC_login_Nop.bl_idname, text="ログイン")

        elif mem_id.startswith("m"):

            if "under_progress" not in bpy.context.scene or bpy.context.scene["under_progress"] is False:
                layout.prop(scene, "shellarc_prop_enum", text="アセット")
                layout.prop(scene, "shellarc_prop_str_savepath", text="保存ディレクトリ")
                layout.separator()
                layout.operator(SHELLARC_getfile_Nop.bl_idname, text="ロード")
                layout.operator(SHELLARC_exclock_Nop.bl_idname, text="排他ロック")
                layout.operator(SHELLARC_reloadassetlist_Nop.bl_idname, text="アセットリストをリロード")
                layout.operator(SHELLARC_logout_Nop.bl_idname, text="ログアウト")

            else:
                layout.operator(SHELLARC_commitfile_Nop.bl_idname, text="キャッシュ")
                layout.operator(SHELLARC_submitfile_Nop.bl_idname, text="アップ")


def read_asset_list(self, context) -> list[str]:
    cache_path = Path(__file__).resolve().parent / "asset_list.pkl"
    if not cache_path.exists():
        return []
    with open(cache_path, "rb") as f:
        asset_list = pickle.load(f)
    return asset_list

def init_props():
    scene = bpy.types.Scene
    scene.shellarc_prop_str_decodekey = StringProperty(
        name="鍵",
        description="デコードキーを入力してください（わからない場合は問い合わせてください）",
        subtype="PASSWORD",
        default=""
    )
    scene.shellarc_prop_str_memid = StringProperty(
        name="作業者ID",
        description="Discordボットから発行された6桁のIDを入力してください",
        default=""
    )
    scene.shellarc_prop_str_savepath = StringProperty(
        name="保存ディレクトリ",
        description="ファイルを格納するディレクトリを指定してください",
        default=f"{os.path.expanduser("~")}/Downloads"
    )
    scene.shellarc_prop_enum = EnumProperty(
        name="アセット",
        description="アセットを選択してください",
        items=read_asset_list
    )